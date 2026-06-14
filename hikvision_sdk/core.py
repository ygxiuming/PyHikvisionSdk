# -*- coding: utf-8 -*-
"""HCNetSDK 全局生命周期管理。

封装：
  * NET_DVR_Init / NET_DVR_Cleanup
  * NET_DVR_SetSDKInitCfg：通知 SDK 在哪里寻找 HCNetSDKCom 子目录与 OpenSSL
  * NET_DVR_SetLogToFile：设置日志路径与级别
  * NET_DVR_GetSDKVersion / NET_DVR_GetSDKBuildVersion

整个进程内全局 **单例**：第一次构造时初始化 SDK，最后一次释放时清理。
推荐使用方式：

    from hikvision_sdk import HikvisionSDK
    with HikvisionSDK() as sdk:
        ...

或者直接：

    HikvisionSDK.get_instance()    # 全局共享
"""

from __future__ import annotations

import os
import threading
from ctypes import byref, create_string_buffer
from pathlib import Path
from typing import Optional

from hikvision_sdk._bindings import HCNetSDK, PlayCtrl, loader
from hikvision_sdk.exceptions import HikvisionError
from hikvision_sdk.utils.logging import get_logger

_logger = get_logger("hikvision_sdk.core")


class HikvisionSDK:
    """HCNetSDK 单例封装。"""

    _instance: Optional["HikvisionSDK"] = None
    _lock = threading.Lock()
    _ref_count = 0

    def __init__(self, log_dir: Optional[str] = None, log_level: int = 0):
        """
        Args:
            log_dir: SDK 日志输出目录；为空则不写文件。
            log_level: 0=关闭 1=ERROR 2=ERROR+DEBUG 3=ERROR+DEBUG+INFO。
        """
        self._log_dir = log_dir
        self._log_level = int(log_level)
        self._initialized = False
        # 提前确保 dll 搜索路径已就绪
        loader.ensure_runtime_paths()
        # 加载并持有底层句柄
        self.netsdk = HCNetSDK.load_library(HCNetSDK.netsdkdllpath)
        self.playm4 = PlayCtrl.load_library(PlayCtrl.playM4dllpath)
        # 把"用户直接构造的实例"登记为全局单例，避免重复初始化
        HikvisionSDK._register_as_singleton(self)

    # ------------------------------------------------------------------ #
    # 单例接口
    # ------------------------------------------------------------------ #

    @classmethod
    def get_instance(cls, **kwargs) -> "HikvisionSDK":
        """获取（或创建）全局 SDK 单例。"""
        with cls._lock:
            if cls._instance is None:
                inst = cls(**kwargs)
                inst.initialize()
                cls._instance = inst
            cls._ref_count += 1
            return cls._instance

    @classmethod
    def _register_as_singleton(cls, inst: "HikvisionSDK") -> None:
        """供构造函数把"用户显式 new 出来的实例"登记为单例。"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = inst
                # 用户直接 new 的实例视作初始引用 1
                cls._ref_count = max(cls._ref_count, 1)

    @classmethod
    def release_instance(cls) -> None:
        """释放对单例的一次引用，引用归零时执行 NET_DVR_Cleanup。"""
        with cls._lock:
            if cls._instance is None:
                return
            cls._ref_count -= 1
            if cls._ref_count <= 0:
                cls._instance.cleanup()
                cls._instance = None
                cls._ref_count = 0

    # ------------------------------------------------------------------ #
    # 上下文管理
    # ------------------------------------------------------------------ #

    def __enter__(self) -> "HikvisionSDK":
        if not self._initialized:
            self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.cleanup()

    # ------------------------------------------------------------------ #
    # 生命周期
    # ------------------------------------------------------------------ #

    def initialize(self) -> None:
        """完成 SDK 初始化（NET_DVR_Init + 路径与日志配置）。"""
        if self._initialized:
            return

        # 1. 告诉 SDK 在哪里找 HCNetSDKCom（功能模块）以及 SSL 库
        self._apply_sdk_init_cfg()

        # 2. 初始化
        ok = self.netsdk.NET_DVR_Init()
        if not ok:
            code = int(self.netsdk.NET_DVR_GetLastError())
            raise HikvisionError(code, api="NET_DVR_Init")

        # 3. 日志配置
        if self._log_dir:
            os.makedirs(self._log_dir, exist_ok=True)
            self.netsdk.NET_DVR_SetLogToFile(
                self._log_level,
                self._log_dir.encode("utf-8"),
                False,
            )

        self._initialized = True
        _logger.info("HCNetSDK 初始化完成, 版本=%s", self.get_version_string())

    def cleanup(self) -> None:
        """卸载 SDK。"""
        if not self._initialized:
            return
        try:
            self.netsdk.NET_DVR_Cleanup()
        except Exception:  # pragma: no cover
            pass
        self._initialized = False
        _logger.info("HCNetSDK 已清理")

    # ------------------------------------------------------------------ #
    # 内部辅助
    # ------------------------------------------------------------------ #

    def _apply_sdk_init_cfg(self) -> None:
        """通过 NET_DVR_SetSDKInitCfg 注入路径，避免依赖工作目录。"""
        sdk_dir: Path = loader.get_platform_sdk_dir()
        com_dir: Path = sdk_dir / "HCNetSDKCom"

        # NET_DVR_LOCAL_SDK_PATH（功能模块所在目录）
        cfg = HCNetSDK.NET_DVR_LOCAL_SDK_PATH()
        # 海康在 Windows 下要求 GBK 编码、Linux 下 UTF-8
        if loader._detect_platform_dir() == "win":
            cfg.sPath = str(com_dir).encode("gbk")
        else:
            cfg.sPath = str(com_dir).encode("utf-8")
        try:
            self.netsdk.NET_DVR_SetSDKInitCfg(
                HCNetSDK.NET_SDK_INIT_CFG_TYPE.NET_SDK_INIT_CFG_SDK_PATH.value,
                byref(cfg),
            )
        except Exception as e:  # pragma: no cover
            _logger.warning("NET_SDK_INIT_CFG_SDK_PATH 设置失败: %s", e)

        # OpenSSL 库的精确路径（Windows 与 Linux 文件名不同）
        if loader._detect_platform_dir() == "win":
            libeay = sdk_dir / "libcrypto-1_1-x64.dll"
            ssleay = sdk_dir / "libssl-1_1-x64.dll"
            encoding = "gbk"
        else:
            libeay = sdk_dir / "libcrypto.so.1.1"
            ssleay = sdk_dir / "libssl.so.1.1"
            encoding = "utf-8"

        if libeay.exists():
            buf = create_string_buffer(str(libeay).encode(encoding))
            try:
                self.netsdk.NET_DVR_SetSDKInitCfg(
                    HCNetSDK.NET_SDK_INIT_CFG_TYPE.NET_SDK_INIT_CFG_LIBEAY_PATH.value,
                    buf,
                )
            except Exception as e:  # pragma: no cover
                _logger.warning("NET_SDK_INIT_CFG_LIBEAY_PATH 设置失败: %s", e)
        if ssleay.exists():
            buf = create_string_buffer(str(ssleay).encode(encoding))
            try:
                self.netsdk.NET_DVR_SetSDKInitCfg(
                    HCNetSDK.NET_SDK_INIT_CFG_TYPE.NET_SDK_INIT_CFG_SSLEAY_PATH.value,
                    buf,
                )
            except Exception as e:  # pragma: no cover
                _logger.warning("NET_SDK_INIT_CFG_SSLEAY_PATH 设置失败: %s", e)

    # ------------------------------------------------------------------ #
    # 信息查询
    # ------------------------------------------------------------------ #

    def get_version(self) -> int:
        """返回 NET_DVR_GetSDKVersion 的原始整数。"""
        return int(self.netsdk.NET_DVR_GetSDKVersion())

    def get_build_version(self) -> int:
        """返回 NET_DVR_GetSDKBuildVersion 的原始整数。"""
        try:
            return int(self.netsdk.NET_DVR_GetSDKBuildVersion())
        except Exception:
            return 0

    def get_version_string(self) -> str:
        """返回形如 ``6.1.9.48`` 的版本字符串。

        海康的版本编码：
          * NET_DVR_GetSDKVersion: 高 16 位为主版本号、低 16 位为次版本号
            （例如 0x00060001 = 6.1）
          * NET_DVR_GetSDKBuildVersion: 4 个字节依次为
            major.minor.build_major.build_minor（例如 0x06010930 = 6.1.9.48）
        """
        v = self.get_version()
        b = self.get_build_version()
        if b:
            return "{0}.{1}.{2}.{3}".format(
                (b >> 24) & 0xFF,
                (b >> 16) & 0xFF,
                (b >> 8) & 0xFF,
                b & 0xFF,
            )
        major = (v >> 16) & 0xFFFF
        minor = v & 0xFFFF
        return f"{major}.{minor}"

    def get_last_error(self) -> int:
        return int(self.netsdk.NET_DVR_GetLastError())


__all__ = ["HikvisionSDK"]
