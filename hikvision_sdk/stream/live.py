# -*- coding: utf-8 -*-
"""实时预览 LiveStream（NET_DVR_RealPlay_V40）。

与 ``rtsp_stream.RTSPLowLatencyStream`` 区别：
  * 本类用于"显示+保存原始码流"等典型预览场景；
  * RTSP 类专注于低延迟取帧，并提供双后端切换。

两者底层机制相同（NET_DVR_RealPlay_V40），按需选用即可。
"""

from __future__ import annotations

import threading
from ctypes import POINTER, byref, c_byte, c_void_p, string_at
from typing import Callable, Optional

from hikvision_sdk._bindings import HCNetSDK
from hikvision_sdk.exceptions import HikvisionError
from hikvision_sdk.utils.logging import get_logger

_logger = get_logger("hikvision_sdk.stream.live")

NET_DVR_SYSHEAD = 1
NET_DVR_STREAMDATA = 2
NET_DVR_AUDIOSTREAMDATA = 3
NET_DVR_PRIVATE_DATA = 112


class LiveStream:
    """实时预览 + 原始码流回调。

    用法::

        stream = LiveStream(device, channel=1, stream_type=0)
        stream.set_data_callback(lambda dtype, data: ...)
        stream.start()
        ...
        stream.stop()
    """

    def __init__(self, device, channel: int = 1, stream_type: int = 0,
                 link_mode: int = 0):
        self.device = device
        self.netsdk = device.netsdk
        self.channel = int(channel)
        self.stream_type = int(stream_type)
        self.link_mode = int(link_mode)
        self._handle: int = -1
        self._cb_ref = None
        self._user_callback: Optional[Callable[[int, bytes], None]] = None

    def set_data_callback(self, cb: Callable[[int, bytes], None]) -> None:
        """设置原始码流回调：``cb(data_type, data_bytes)``。"""
        self._user_callback = cb

    def start(self) -> int:
        if self._handle >= 0:
            return self._handle

        def _real_cb(handle, data_type, p_buf, n_size, user):
            try:
                size = int(n_size)
                if size <= 0:
                    return
                payload = string_at(p_buf, size)
                if self._user_callback:
                    self._user_callback(int(data_type), payload)
            except Exception as e:  # pragma: no cover
                _logger.exception("码流回调异常: %s", e)

        self._cb_ref = HCNetSDK.REALDATACALLBACK(_real_cb)

        info = HCNetSDK.NET_DVR_PREVIEWINFO()
        start_chan = int(getattr(self.device.info, "start_channel", 1) or 1)
        info.lChannel = start_chan + (self.channel - 1)
        info.dwStreamType = self.stream_type
        info.dwLinkMode = self.link_mode
        info.hPlayWnd = 0
        info.bBlocked = 1
        info.byProtoType = 0
        info.dwDisplayBufNum = 1

        h = int(self.netsdk.NET_DVR_RealPlay_V40(
            self.device.user_id, byref(info), self._cb_ref, c_void_p(0)
        ))
        if h < 0:
            code = int(self.netsdk.NET_DVR_GetLastError())
            raise HikvisionError(code, api="NET_DVR_RealPlay_V40")
        self._handle = h
        _logger.info("LiveStream 启动 handle=%d 通道=%d 码流=%d",
                     h, info.lChannel, self.stream_type)
        return h

    def stop(self) -> None:
        if self._handle < 0:
            return
        try:
            self.netsdk.NET_DVR_StopRealPlay(self._handle)
        except Exception:  # pragma: no cover
            pass
        self._handle = -1

    def __enter__(self) -> "LiveStream":
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.stop()


__all__ = ["LiveStream"]
