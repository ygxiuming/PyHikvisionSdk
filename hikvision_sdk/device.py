# -*- coding: utf-8 -*-
"""设备登录与基本信息封装。

调用 ``NET_DVR_Login_V40`` 完成同步登录，登出时调用 ``NET_DVR_Logout``。
本类同时是其他业务模块（PTZ、Snapshot、Live、PlayBack…）的入口。
"""

from __future__ import annotations

from ctypes import byref, addressof
from typing import Optional

from hikvision_sdk._bindings import HCNetSDK
from hikvision_sdk.core import HikvisionSDK
from hikvision_sdk.exceptions import HikvisionError
from hikvision_sdk.types import DeviceInfo
from hikvision_sdk.utils.logging import get_logger

_logger = get_logger("hikvision_sdk.device")


class Device:
    """单台海康设备的会话对象。

    用法::

        from hikvision_sdk import HikvisionSDK, Device
        with HikvisionSDK() as _:
            with Device("192.168.1.64", "admin", "password") as dev:
                print(dev.info)
                # ... 使用 dev.user_id 调用其他模块 ...
    """

    def __init__(
        self,
        ip: str,
        username: str,
        password: str,
        port: int = 8000,
        login_mode: int = 0,
    ):
        """
        Args:
            ip: 设备 IP 地址或域名。
            username: 登录用户名。
            password: 登录密码。
            port: 设备 SDK 端口，默认 8000。
            login_mode: 0=私有协议（默认），1=ISAPI 协议。
        """
        self._sdk = HikvisionSDK.get_instance()
        self.netsdk = self._sdk.netsdk
        self.ip = ip
        self.username = username
        self.password = password
        self.port = int(port)
        self.login_mode = int(login_mode)

        self.user_id: int = -1
        self.info: Optional[DeviceInfo] = None

    # ------------------------------------------------------------------ #
    # 上下文
    # ------------------------------------------------------------------ #

    def __enter__(self) -> "Device":
        self.login()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.logout()
        # 释放对全局 SDK 单例的一次引用
        HikvisionSDK.release_instance()

    # ------------------------------------------------------------------ #
    # 登录 / 登出
    # ------------------------------------------------------------------ #

    def login(self) -> int:
        """同步登录设备，成功返回 ``user_id``，失败抛 ``HikvisionError``。"""
        if self.user_id >= 0:
            return self.user_id

        # NET_DVR_USER_LOGIN_INFO 字段为定长 byte 数组，需要按长度填充
        login_info = HCNetSDK.NET_DVR_USER_LOGIN_INFO()
        login_info.bUseAsynLogin = 0
        login_info.byLoginMode = self.login_mode
        login_info.sDeviceAddress = self.ip.encode("utf-8")
        login_info.wPort = self.port
        login_info.sUserName = self.username.encode("utf-8")
        login_info.sPassword = self.password.encode("utf-8")

        device_info_v40 = HCNetSDK.NET_DVR_DEVICEINFO_V40()
        uid = int(self.netsdk.NET_DVR_Login_V40(byref(login_info), byref(device_info_v40)))
        if uid < 0:
            code = int(self.netsdk.NET_DVR_GetLastError())
            raise HikvisionError(code, api="NET_DVR_Login_V40")

        self.user_id = uid
        self.info = self._parse_device_info(device_info_v40, uid)
        _logger.info(
            "登录成功 IP=%s user_id=%d serial=%s 通道(模拟/IP)=%d/%d",
            self.ip, uid, self.info.serial_number,
            self.info.channel_num, self.info.ip_channel_num,
        )
        return uid

    def logout(self) -> None:
        """登出设备。"""
        if self.user_id >= 0:
            try:
                self.netsdk.NET_DVR_Logout(self.user_id)
            except Exception:  # pragma: no cover
                pass
            _logger.info("登出 IP=%s user_id=%d", self.ip, self.user_id)
            self.user_id = -1

    # ------------------------------------------------------------------ #
    # 信息查询
    # ------------------------------------------------------------------ #

    @staticmethod
    def _parse_device_info(raw: "HCNetSDK.NET_DVR_DEVICEINFO_V40", uid: int) -> DeviceInfo:
        """把 NET_DVR_DEVICEINFO_V40 翻译成 DeviceInfo。"""
        v30 = raw.struDeviceV30
        try:
            serial = bytes(v30.sSerialNumber).split(b"\x00", 1)[0].decode("utf-8", errors="replace")
        except Exception:
            serial = ""
        return DeviceInfo(
            serial_number=serial,
            device_type=int(getattr(v30, "wDevType", 0) or 0),
            channel_num=int(getattr(v30, "byChanNum", 0) or 0),
            ip_channel_num=int(getattr(v30, "byIPChanNum", 0) or 0),
            start_channel=int(getattr(v30, "byStartChan", 1) or 1),
            start_ip_channel=int(getattr(v30, "byStartDChan", 1) or 1),
            audio_channel_num=int(getattr(v30, "byAudioChanNum", 0) or 0),
            zero_channel_num=int(getattr(v30, "byZeroChanNum", 0) or 0),
            alarm_in_num=int(getattr(v30, "byAlarmInPortNum", 0) or 0),
            alarm_out_num=int(getattr(v30, "byAlarmOutPortNum", 0) or 0),
            disk_num=int(getattr(v30, "byDiskNum", 0) or 0),
            user_id=int(uid),
        )

    @property
    def is_logged_in(self) -> bool:
        return self.user_id >= 0


__all__ = ["Device"]
