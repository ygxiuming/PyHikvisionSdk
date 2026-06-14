# -*- coding: utf-8 -*-
"""报警布防与事件监听。

调用流程：
  1. ``NET_DVR_SetDVRMessageCallBack_V31`` 注册全局消息回调；
  2. ``NET_DVR_SetupAlarmChan_V41`` 对设备布防；
  3. 设备上报的报警信息通过回调推回 Python；
  4. 撤防 ``NET_DVR_CloseAlarmChan_V30``。

回调签名（MSGCallBack_V31）::

    BOOL cb(LONG lCommand, LPNET_DVR_ALARMER pAlarmer,
            char* pAlarmInfo, DWORD dwBufLen, void* pUser)

我们用一个 dispatch 表把 ``lCommand``（事件类型，例如 0x4000=移动侦测、
0x4001=信号丢失、0x70d=越界检测 等）映射到用户提供的处理函数。
"""

from __future__ import annotations

import threading
from ctypes import (
    POINTER, Structure, byref, c_bool, c_byte, c_void_p, string_at,
)
from typing import Callable, Dict, Optional

from hikvision_sdk._bindings import HCNetSDK
from hikvision_sdk.exceptions import HikvisionError
from hikvision_sdk.utils.logging import get_logger

_logger = get_logger("hikvision_sdk.alarm")


class _NET_DVR_SETUPALARM_PARAM(Structure):
    """布防参数 V40。"""
    _fields_ = [
        ("dwSize", c_byte * 4),       # 实际为 DWORD，用 4 字节占位
        ("byLevel", c_byte),
        ("byAlarmInfoType", c_byte),
        ("byRetAlarmTypeV40", c_byte),
        ("byRetDevInfoVersion", c_byte),
        ("byRetVCAType", c_byte),
        ("byDeployType", c_byte),
        ("byRes1", c_byte * 2),
        ("byAlarmTypeURL", c_byte),
        ("byCustomCtrl", c_byte),
    ]


class AlarmListener:
    """报警事件监听。

    用法::

        alarm = AlarmListener(device)
        alarm.on_event = lambda cmd, info_bytes, alarmer: print(hex(cmd), len(info_bytes))
        alarm.start()
        ... 等待事件 ...
        alarm.stop()
    """

    def __init__(self, device):
        self.device = device
        self.netsdk = device.netsdk
        self._handle: int = -1
        self._cb_ref = None
        self._handlers: Dict[int, Callable] = {}
        self.on_event: Optional[Callable[[int, bytes, object], None]] = None
        self._lock = threading.Lock()

    def register_handler(self, cmd: int, handler: Callable[[int, bytes, object], None]) -> None:
        """注册某种 ``lCommand`` 的处理函数。"""
        self._handlers[int(cmd)] = handler

    def start(self) -> None:
        if self._handle >= 0:
            return

        def _msg_cb(lCommand, pAlarmer, pAlarmInfo, dwBufLen, pUser):
            try:
                size = int(dwBufLen)
                payload = string_at(pAlarmInfo, size) if (pAlarmInfo and size > 0) else b""
                alarmer_struct = pAlarmer.contents if pAlarmer else None
                cmd = int(lCommand)
                if self.on_event:
                    try:
                        self.on_event(cmd, payload, alarmer_struct)
                    except Exception as e:  # pragma: no cover
                        _logger.exception("on_event 处理异常: %s", e)
                h = self._handlers.get(cmd)
                if h:
                    try:
                        h(cmd, payload, alarmer_struct)
                    except Exception as e:  # pragma: no cover
                        _logger.exception("handler[%s] 异常: %s", cmd, e)
            except Exception as e:  # pragma: no cover
                _logger.exception("MSGCallBack_V31 异常: %s", e)
            return True

        self._cb_ref = HCNetSDK.MSGCallBack_V31(_msg_cb)
        if not self.netsdk.NET_DVR_SetDVRMessageCallBack_V31(self._cb_ref, c_void_p(0)):
            code = int(self.netsdk.NET_DVR_GetLastError())
            raise HikvisionError(code, api="NET_DVR_SetDVRMessageCallBack_V31")

        # 默认布防参数
        param = _NET_DVR_SETUPALARM_PARAM()
        # dwSize = sizeof(struct)，这里我们粗略给一个安全大小
        size = 32
        param.dwSize = (c_byte * 4)(size & 0xFF, (size >> 8) & 0xFF,
                                    (size >> 16) & 0xFF, (size >> 24) & 0xFF)
        param.byLevel = 1
        param.byAlarmInfoType = 1
        param.byRetAlarmTypeV40 = 1
        param.byRetDevInfoVersion = 0

        h = int(self.netsdk.NET_DVR_SetupAlarmChan_V41(
            self.device.user_id, byref(param)
        ))
        if h < 0:
            # V41 失败时退回到普通布防
            h = int(self.netsdk.NET_DVR_SetupAlarmChan_V30(self.device.user_id))
        if h < 0:
            code = int(self.netsdk.NET_DVR_GetLastError())
            raise HikvisionError(code, api="NET_DVR_SetupAlarmChan_V41")
        self._handle = h
        _logger.info("布防成功 handle=%d", h)

    def stop(self) -> None:
        if self._handle < 0:
            return
        try:
            self.netsdk.NET_DVR_CloseAlarmChan_V30(self._handle)
        except Exception:  # pragma: no cover
            pass
        self._handle = -1

    def __enter__(self) -> "AlarmListener":
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.stop()


__all__ = ["AlarmListener"]
