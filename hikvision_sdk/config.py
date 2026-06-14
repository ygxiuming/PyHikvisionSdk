# -*- coding: utf-8 -*-
"""通用远程参数 Get/Set 配置封装。

使用 ``NET_DVR_GetDVRConfig`` / ``NET_DVR_SetDVRConfig`` 即可对设备做几乎所有
非视频流参数的读写（设备时间、网络、用户、码流、OSD、智能等）。

各 ``dwCommand`` 命令码对应的结构体请参考《设备网络SDK编程指南》。
本模块只提供"裸"读写工具，业务层根据具体命令码自行准备 ctypes 结构体。
"""

from __future__ import annotations

from ctypes import POINTER, Structure, byref, c_byte, c_uint, sizeof
from typing import Type

from hikvision_sdk.exceptions import HikvisionError
from hikvision_sdk.utils.logging import get_logger

_logger = get_logger("hikvision_sdk.config")


# 常用命令码摘录（命令码完整列表见 HCNetSDK.h）
NET_DVR_GET_TIMECFG = 117          # 获取设备时间
NET_DVR_SET_TIMECFG = 118          # 设置设备时间
NET_DVR_GET_NETCFG_V30 = 1000      # 获取网络参数
NET_DVR_SET_NETCFG_V30 = 1001      # 设置网络参数
NET_DVR_GET_DEVICECFG_V40 = 1100   # 获取设备参数 V40
NET_DVR_GET_USERCFG_V30 = 1042     # 获取用户参数
NET_DVR_GET_PICCFG_V30 = 1024      # 获取图像参数 V30
NET_DVR_GET_COMPRESSCFG_V30 = 1040 # 获取压缩参数 V30
NET_DVR_SET_COMPRESSCFG_V30 = 1041 # 设置压缩参数 V30


def get_config(device, command: int, channel: int, struct_cls: Type[Structure]) -> Structure:
    """泛型读取：把 ``struct_cls`` 当作输出缓冲返回。"""
    obj = struct_cls()
    written = c_uint(0)
    ok = device.netsdk.NET_DVR_GetDVRConfig(
        device.user_id, int(command), int(channel),
        byref(obj), sizeof(obj), byref(written)
    )
    if not ok:
        code = int(device.netsdk.NET_DVR_GetLastError())
        raise HikvisionError(code, api=f"NET_DVR_GetDVRConfig({command})")
    return obj


def set_config(device, command: int, channel: int, struct_obj: Structure) -> None:
    """泛型写入。"""
    ok = device.netsdk.NET_DVR_SetDVRConfig(
        device.user_id, int(command), int(channel),
        byref(struct_obj), sizeof(struct_obj)
    )
    if not ok:
        code = int(device.netsdk.NET_DVR_GetLastError())
        raise HikvisionError(code, api=f"NET_DVR_SetDVRConfig({command})")


# ---------------------------------------------------------------------------
# 便捷封装：设备时间
# ---------------------------------------------------------------------------
class _NET_DVR_TIME(Structure):
    _fields_ = [
        ("dwYear", c_uint), ("dwMonth", c_uint), ("dwDay", c_uint),
        ("dwHour", c_uint), ("dwMinute", c_uint), ("dwSecond", c_uint),
    ]


def get_device_time(device) -> "datetime":
    """读取设备当前时间。"""
    from datetime import datetime
    t = get_config(device, NET_DVR_GET_TIMECFG, 0, _NET_DVR_TIME)
    return datetime(int(t.dwYear), int(t.dwMonth), int(t.dwDay),
                    int(t.dwHour), int(t.dwMinute), int(t.dwSecond))


def set_device_time(device, dt: "datetime") -> None:
    """同步设备时间。"""
    t = _NET_DVR_TIME()
    t.dwYear = dt.year; t.dwMonth = dt.month; t.dwDay = dt.day
    t.dwHour = dt.hour; t.dwMinute = dt.minute; t.dwSecond = dt.second
    set_config(device, NET_DVR_SET_TIMECFG, 0, t)


__all__ = [
    "get_config", "set_config",
    "get_device_time", "set_device_time",
    "NET_DVR_GET_TIMECFG", "NET_DVR_SET_TIMECFG",
    "NET_DVR_GET_NETCFG_V30", "NET_DVR_SET_NETCFG_V30",
    "NET_DVR_GET_DEVICECFG_V40", "NET_DVR_GET_USERCFG_V30",
    "NET_DVR_GET_PICCFG_V30",
    "NET_DVR_GET_COMPRESSCFG_V30", "NET_DVR_SET_COMPRESSCFG_V30",
]
