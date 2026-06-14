# -*- coding: utf-8 -*-
"""
跨平台 SDK 库加载器
====================

本模块负责：
  1. 根据当前操作系统（Windows / Linux）和位数（32 / 64）解析所需的
     HCNetSDK、PlayCtrl 动态库的绝对路径；
  2. 在 import 阶段把 sdk/win 或 sdk/linux 注入操作系统的库搜索路径，
     使得 HCCore.dll/libHCCore.so 这样的依赖项能被自动找到；
  3. 提供 ``ensure_runtime_paths()`` 工具函数，业务代码可在加载前手动调用。

设计要点：
  * 唯一的 SDK 物理位置：项目根目录的 ``sdk/win`` 与 ``sdk/linux``。
  * 不依赖工作目录（CWD），始终基于本文件位置反推工程根目录。
  * Windows 使用 ``os.add_dll_directory``（Python 3.8+）注入搜索路径，
    避免 PATH 污染；Linux 通过设置 ``LD_LIBRARY_PATH`` 影响子进程，
    本进程使用 ``ctypes.CDLL(absolute_path)`` 直接加载，主库已可解析。
  * Windows 上的 HCNetSDKCom 子目录通过 ``NET_DVR_SetSDKInitCfg`` 在
    上层 ``core.py`` 中注入，本模块只负责保证主库能加载到。
"""

from __future__ import annotations

import os
import sys
import platform
import ctypes
from pathlib import Path
from typing import Optional


# ===========================================================================
# 路径解析
# ===========================================================================

def get_project_root() -> Path:
    """返回工程根目录（即包含 ``sdk/`` 的那一层目录）。

    本文件位于 ``<project_root>/hikvision_sdk/_bindings/loader.py``，
    所以向上回溯两级即可定位到工程根目录。
    """
    return Path(__file__).resolve().parents[2]


def get_sdk_root() -> Path:
    """返回 sdk 资源根目录 ``<project_root>/sdk``。"""
    return get_project_root() / "sdk"


def _detect_platform_dir() -> str:
    """根据当前系统返回 ``win`` 或 ``linux``。"""
    sys_name = platform.system().lower().strip()
    if sys_name == "windows":
        return "win"
    if sys_name == "linux":
        return "linux"
    raise RuntimeError(f"不支持的操作系统: {sys_name}")


def get_platform_sdk_dir() -> Path:
    """返回当前平台对应的 SDK 目录，例如 ``<root>/sdk/win`` 或 ``<root>/sdk/linux``。"""
    return get_sdk_root() / _detect_platform_dir()


def get_hcnetsdk_com_dir() -> Path:
    """返回 HCNetSDKCom 子目录路径（功能模块库存放处）。"""
    return get_platform_sdk_dir() / "HCNetSDKCom"


# ===========================================================================
# DLL/SO 文件名映射
# ===========================================================================

_LIBRARY_FILENAMES = {
    # system_type -> (HCNetSDK 文件名, PlayCtrl 文件名)
    "windows64": ("HCNetSDK.dll", "PlayCtrl.dll"),
    "windows32": ("HCNetSDK.dll", "PlayCtrl.dll"),
    "linux64": ("libhcnetsdk.so", "libPlayCtrl.so"),
    "linux32": ("libhcnetsdk.so", "libPlayCtrl.so"),
}


def resolve_netsdk_dll_path(system_type: str) -> str:
    """解析 HCNetSDK 动态库的绝对路径。

    Args:
        system_type: ``windows64`` / ``windows32`` / ``linux64`` / ``linux32``。

    Returns:
        动态库的绝对路径字符串。
    """
    if system_type not in _LIBRARY_FILENAMES:
        raise RuntimeError(f"未知的平台标识: {system_type}")
    fname = _LIBRARY_FILENAMES[system_type][0]
    path = get_platform_sdk_dir() / fname
    if not path.exists():
        raise FileNotFoundError(
            f"找不到 HCNetSDK 库文件: {path}\n"
            f"请确认已将 SDK 文件正确拷贝到 {get_platform_sdk_dir()}"
        )
    return str(path)


def resolve_playctrl_dll_path(system_type: str) -> str:
    """解析 PlayCtrl(PlayM4) 动态库的绝对路径。"""
    if system_type not in _LIBRARY_FILENAMES:
        raise RuntimeError(f"未知的平台标识: {system_type}")
    fname = _LIBRARY_FILENAMES[system_type][1]
    path = get_platform_sdk_dir() / fname
    if not path.exists():
        raise FileNotFoundError(
            f"找不到 PlayCtrl 库文件: {path}\n"
            f"请确认已将 SDK 文件正确拷贝到 {get_platform_sdk_dir()}"
        )
    return str(path)


# ===========================================================================
# 运行时路径注入
# ===========================================================================

_runtime_initialized = False


def ensure_runtime_paths() -> Path:
    """在加载海康任意动态库之前，把 SDK 目录注入到操作系统的库搜索路径。

    可以反复调用，仅第一次生效。返回当前平台对应的 SDK 根目录。
    """
    global _runtime_initialized
    sdk_dir = get_platform_sdk_dir()
    if _runtime_initialized:
        return sdk_dir

    if not sdk_dir.exists():
        raise FileNotFoundError(
            f"未找到平台 SDK 目录: {sdk_dir}\n"
            f"请确认已将海康 SDK 的库文件拷贝到该目录。"
        )

    sys_name = platform.system().lower().strip()
    if sys_name == "windows":
        # Python 3.8+ 推荐使用 os.add_dll_directory 显式注入 dll 搜索路径
        if hasattr(os, "add_dll_directory"):
            try:
                os.add_dll_directory(str(sdk_dir))
            except (OSError, FileNotFoundError):
                pass
            com_dir = sdk_dir / "HCNetSDKCom"
            if com_dir.exists():
                try:
                    os.add_dll_directory(str(com_dir))
                except (OSError, FileNotFoundError):
                    pass
        # 兼容 Python 3.7 及以下：把目录追加到 PATH
        os.environ["PATH"] = (
            str(sdk_dir) + os.pathsep + str(sdk_dir / "HCNetSDKCom")
            + os.pathsep + os.environ.get("PATH", "")
        )
    else:
        # Linux：把目录加到 LD_LIBRARY_PATH 仅对子进程生效；
        # 本进程使用绝对路径直接加载主库即可解析依赖（同目录下的 libHCCore.so 会被自动找到）。
        # 这里仍然设置环境变量，方便诸如 ffmpeg 子进程读取。
        existing = os.environ.get("LD_LIBRARY_PATH", "")
        com_dir = sdk_dir / "HCNetSDKCom"
        parts = [str(sdk_dir)]
        if com_dir.exists():
            parts.append(str(com_dir))
        if existing:
            parts.append(existing)
        os.environ["LD_LIBRARY_PATH"] = os.pathsep.join(parts)

    _runtime_initialized = True
    return sdk_dir


# 模块导入时自动注入一次（确保 HCNetSDK.py 中调用 load_library 前路径已就绪）
try:
    ensure_runtime_paths()
except FileNotFoundError:
    # SDK 目录尚未就绪时不要在 import 阶段抛异常，让上层得到更友好的报错位置
    pass


# ===========================================================================
# 便捷加载器（可被业务代码直接使用，避免每次自己 ctypes.CDLL）
# ===========================================================================

def load_hcnetsdk(system_type: Optional[str] = None) -> ctypes.CDLL:
    """加载并返回 HCNetSDK 句柄。"""
    ensure_runtime_paths()
    if system_type is None:
        system_type = _current_system_type()
    path = resolve_netsdk_dll_path(system_type)
    if platform.system().lower() == "windows":
        return ctypes.WinDLL(path)
    return ctypes.CDLL(path)


def load_playctrl(system_type: Optional[str] = None) -> ctypes.CDLL:
    """加载并返回 PlayCtrl(PlayM4) 句柄。"""
    ensure_runtime_paths()
    if system_type is None:
        system_type = _current_system_type()
    path = resolve_playctrl_dll_path(system_type)
    if platform.system().lower() == "windows":
        return ctypes.WinDLL(path)
    return ctypes.CDLL(path)


def _current_system_type() -> str:
    """返回 ``windows64`` / ``windows32`` / ``linux64`` / ``linux32``。"""
    sys_name = platform.system().lower().strip()
    bits = "64" if sys.maxsize > 2 ** 32 else "32"
    if sys_name == "windows":
        return f"windows{bits}"
    if sys_name == "linux":
        return f"linux{bits}"
    raise RuntimeError(f"不支持的操作系统: {sys_name}")


__all__ = [
    "get_project_root",
    "get_sdk_root",
    "get_platform_sdk_dir",
    "get_hcnetsdk_com_dir",
    "resolve_netsdk_dll_path",
    "resolve_playctrl_dll_path",
    "ensure_runtime_paths",
    "load_hcnetsdk",
    "load_playctrl",
]
