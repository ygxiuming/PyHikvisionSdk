# -*- coding: utf-8 -*-
"""PlayM4(PlayCtrl) 解码器封装。

PlayM4 库负责把 H.264/H.265/MPEG4 码流 → YUV 原始图像 → （可选）BGR。
本模块同时支持两种数据源：

  1. **流模式** (Stream mode)：通过 ``feed(data)`` 持续投喂码流字节，
     适用于实时预览（NET_DVR_RealPlay 回调）以及 RTSP 拉流。
  2. **文件模式** (File mode)：通过 ``open_file(path)`` 让 PlayM4 自己读
     一段海康私有/MP4 文件，适用于"读取导出视频逐帧时间戳"功能。

回调签名（DECCBFUNWIN）::

    void cb(LONG nPort, char* pBuf, LONG nSize,
            FRAME_INFO* pFrameInfo, LONG nReserved1, LONG nReserved2)

其中 ``pFrameInfo->nStamp`` 是相对毫秒时间戳；当数据源是海康私有流（带
``NET_DVR_PRIVATE_DATA`` 帧头）时，PlayM4_GetSystemTime 可以返回当前帧的
绝对时间结构体（详见 video_file.py 中的 ``VideoFileReader`` 用法）。
"""

from __future__ import annotations

import threading
from ctypes import (
    POINTER, Structure, byref, c_char, c_int, c_long, c_uint, c_ulong, c_void_p,
    cast, string_at,
)
from typing import Callable, Optional

from hikvision_sdk._bindings import HCNetSDK, PlayCtrl
from hikvision_sdk.core import HikvisionSDK
from hikvision_sdk.utils.logging import get_logger

_logger = get_logger("hikvision_sdk.stream.decoder")


# PlayM4 流打开模式
STREAME_REALTIME = 0   # 实时流（默认，最低延迟）
STREAME_FILE = 1       # 文件流


# 解码图像类型（plaympeg4.h 中 T_YV12 = 3，本模块中默认输出 YV12）
T_YV12 = 3
T_RGB32 = 7


# PLAYM4_SYSTEM_TIME 结构体（来自 plaympeg4.h），用于 PlayM4_GetSystemTime。
# 其字段为 4/4/4/4/4/4/4 字节的 32 位整数，含毫秒。
class PLAYM4_SYSTEM_TIME(Structure):
    """PlayM4 系统时间，对应 plaympeg4.h 中的同名结构体。"""
    _fields_ = [
        ("dwYear", c_uint),    # 年
        ("dwMon",  c_uint),    # 月
        ("dwDay",  c_uint),    # 日
        ("dwHour", c_uint),    # 时
        ("dwMin",  c_uint),    # 分
        ("dwSec",  c_uint),    # 秒
        ("dwMs",   c_uint),    # 毫秒
    ]

# 帧类型（FRAME_INFO.nType）。
# PlayM4 的 nType 在不同回调里语义不同：解码回调里 nType 取 T_YV12 等图像格式；
# 我们再用专门的逻辑去推断 I/P/B（例如对私有头解析或对 SPS/PPS 计数）。


class PlayM4Decoder:
    """PlayM4 解码端口的封装（一个端口 = 一个解码会话）。"""

    def __init__(
        self,
        sdk: Optional[HikvisionSDK] = None,
        buffer_size: int = 1024 * 1024,
        display_buf: int = 1,
    ):
        """
        Args:
            sdk: 复用全局 SDK 单例；为空则自动获取。
            buffer_size: PlayM4_OpenStream 的内部缓冲大小。
            display_buf: 显示缓冲帧数（1 = 最低延迟）。
        """
        self._sdk = sdk or HikvisionSDK.get_instance()
        self.netsdk = self._sdk.netsdk
        self.playm4 = self._sdk.playm4

        self._buffer_size = int(buffer_size)
        self._display_buf = int(display_buf)
        self._port: int = -1
        self._stream_opened = False
        self._file_opened = False
        self._dec_cb_ref = None  # 必须保留引用避免被 GC
        self._user_callback: Optional[Callable] = None
        self._frame_counter = 0
        self._lock = threading.Lock()

    # ------------------------------------------------------------------ #
    # 端口生命周期
    # ------------------------------------------------------------------ #

    def acquire_port(self) -> int:
        """获取一个空闲的 PlayM4 端口号。"""
        if self._port >= 0:
            return self._port
        port = c_long(-1)
        if not self.playm4.PlayM4_GetPort(byref(port)):
            err = self._last_error()
            raise RuntimeError(f"PlayM4_GetPort 失败, code={err}")
        self._port = int(port.value)
        # 设置最小显示缓冲，降低延迟
        try:
            self.playm4.PlayM4_SetDisplayBuf(self._port, self._display_buf)
        except Exception:
            pass
        return self._port

    def release_port(self) -> None:
        """关闭流/文件并归还端口。"""
        if self._port < 0:
            return
        try:
            if self._stream_opened:
                self.playm4.PlayM4_Stop(self._port)
                self.playm4.PlayM4_CloseStream(self._port)
            if self._file_opened:
                self.playm4.PlayM4_Stop(self._port)
                self.playm4.PlayM4_CloseFile(self._port)
        except Exception:  # pragma: no cover
            pass
        try:
            self.playm4.PlayM4_FreePort(self._port)
        except Exception:  # pragma: no cover
            pass
        self._port = -1
        self._stream_opened = False
        self._file_opened = False

    @property
    def port(self) -> int:
        return self._port

    # ------------------------------------------------------------------ #
    # 流模式：用于实时预览 / RTSP 拉流
    # ------------------------------------------------------------------ #

    def open_stream(self, sys_header: bytes) -> None:
        """启动流模式：投喂第一段码流（通常是 NET_DVR_SYSHEAD 的 40 字节）。"""
        port = self.acquire_port()
        # 0=实时流 1=文件流
        self.playm4.PlayM4_SetStreamOpenMode(port, STREAME_REALTIME)
        n = len(sys_header)
        buf = (c_char * n).from_buffer_copy(sys_header)
        if not self.playm4.PlayM4_OpenStream(port, buf, c_uint(n), c_uint(self._buffer_size)):
            err = self._last_error()
            raise RuntimeError(f"PlayM4_OpenStream 失败, code={err}")
        self._stream_opened = True

    def feed(self, data: bytes) -> bool:
        """投喂一段码流字节。返回 SDK 是否接受。"""
        if not self._stream_opened or self._port < 0:
            raise RuntimeError("PlayM4 流尚未打开，请先调用 open_stream(sys_header)")
        n = len(data)
        if n == 0:
            return True
        buf = (c_char * n).from_buffer_copy(data)
        return bool(self.playm4.PlayM4_InputData(self._port, buf, c_uint(n)))

    def start_play(self, hwnd: int = 0) -> None:
        """开始解码。``hwnd=0`` 表示不渲染到任何窗口（仅走解码回调）。"""
        if self._port < 0:
            raise RuntimeError("尚未获取 PlayM4 端口")
        if not self.playm4.PlayM4_Play(self._port, hwnd):
            err = self._last_error()
            raise RuntimeError(f"PlayM4_Play 失败, code={err}")

    # ------------------------------------------------------------------ #
    # 文件模式：用于"导出视频文件逐帧时间戳"
    # ------------------------------------------------------------------ #

    def open_file(self, file_path: str) -> None:
        """打开海康私有/MP4 文件（PlayM4_OpenFile）。"""
        port = self.acquire_port()
        self.playm4.PlayM4_SetStreamOpenMode(port, STREAME_FILE)
        # 文件路径 Windows 用 GBK，Linux 用 UTF-8
        import platform
        encoding = "gbk" if platform.system().lower() == "windows" else "utf-8"
        path_bytes = file_path.encode(encoding)
        if not self.playm4.PlayM4_OpenFile(port, path_bytes):
            err = self._last_error()
            raise RuntimeError(f"PlayM4_OpenFile 失败, code={err}, path={file_path}")
        self._file_opened = True

    def close_file(self) -> None:
        """关闭文件（不释放端口，可继续 open_file 重打开）。"""
        if self._file_opened and self._port >= 0:
            try:
                self.playm4.PlayM4_Stop(self._port)
                self.playm4.PlayM4_CloseFile(self._port)
            except Exception:  # pragma: no cover
                pass
            self._file_opened = False

    # ------------------------------------------------------------------ #
    # 文件信息查询（基础）
    # ------------------------------------------------------------------ #

    def get_file_total_frames(self) -> int:
        try:
            n = self.playm4.PlayM4_GetFileTotalFrames(self._port)
            return int(n)
        except Exception:
            return 0

    def get_file_total_time(self) -> int:
        """返回文件总时长（毫秒）。"""
        try:
            return int(self.playm4.PlayM4_GetFileTime(self._port))
        except Exception:
            return 0

    def get_picture_size(self) -> tuple[int, int]:
        """返回 (width, height)。"""
        w = c_uint(0); h = c_uint(0)
        try:
            self.playm4.PlayM4_GetPictureSize(self._port, byref(w), byref(h))
        except Exception:
            pass
        return int(w.value), int(h.value)

    def get_frame_rate(self) -> float:
        """返回当前帧率（fps）。"""
        try:
            v = self.playm4.PlayM4_GetCurrentFrameRate(self._port)
            return float(v) / 100.0 if v > 1000 else float(v)
        except Exception:
            return 0.0

    def get_system_time(self) -> Optional[PLAYM4_SYSTEM_TIME]:
        """调用 PlayM4_GetSystemTime，拿当前帧的绝对时间（PLAYM4_SYSTEM_TIME）。

        当文件包含海康私有头时，本接口返回的是码流里携带的真实绝对时间。
        当文件是普通 mp4 时，本接口可能返回 0 或全零结构体。
        返回 None 表示调用失败。
        """
        st = PLAYM4_SYSTEM_TIME()
        try:
            ok = self.playm4.PlayM4_GetSystemTime(self._port, byref(st))
            if not ok:
                return None
        except Exception:
            return None
        return st

    # ------------------------------------------------------------------ #
    # 解码回调
    # ------------------------------------------------------------------ #

    def set_decode_callback(self, callback: Callable) -> None:
        """注册解码回调。

        Callback 签名：
            ``def cb(port, frame_index, buf_bytes, width, height, pts_ms, frame_type) -> None``
        """
        self._user_callback = callback

        def _native_cb(port, p_buf, n_size, p_frame_info, n_res1, n_res2):
            # p_buf 是 POINTER(c_char)，长度为 n_size
            try:
                fi = p_frame_info.contents
                width = int(fi.nWidth)
                height = int(fi.nHeight)
                pts = int(fi.nStamp)
                ftype = int(fi.nType)
                # 把 buffer 拷贝出来，回调返回后底层缓冲会被覆盖
                buf = string_at(p_buf, int(n_size)) if int(n_size) > 0 else b""
                with self._lock:
                    idx = self._frame_counter
                    self._frame_counter += 1
                if self._user_callback:
                    self._user_callback(int(port), idx, buf, width, height, pts, ftype)
            except Exception as e:  # pragma: no cover
                _logger.exception("解码回调异常: %s", e)

        # 必须长期持有 ctypes 回调实例，否则会被 GC 回收导致崩溃
        self._dec_cb_ref = PlayCtrl.DECCBFUNWIN(_native_cb)
        # PlayM4_SetDecCallBackExMend 优先（带用户数据），否则降级
        try:
            self.playm4.PlayM4_SetDecCallBackExMend(
                self._port, self._dec_cb_ref, c_void_p(0), c_long(0), c_void_p(0)
            )
        except AttributeError:  # pragma: no cover
            self.playm4.PlayM4_SetDecCallBackMend(self._port, self._dec_cb_ref, c_long(0))

    # ------------------------------------------------------------------ #
    # 工具
    # ------------------------------------------------------------------ #

    def _last_error(self) -> int:
        try:
            return int(self.playm4.PlayM4_GetLastError(self._port))
        except Exception:
            return -1

    def __enter__(self) -> "PlayM4Decoder":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.release_port()


__all__ = [
    "PlayM4Decoder",
    "PLAYM4_SYSTEM_TIME",
    "STREAME_REALTIME",
    "STREAME_FILE",
    "T_YV12",
    "T_RGB32",
]
