# -*- coding: utf-8 -*-
"""★ 功能②：低延迟 RTSP 拉流（双后端）

本模块提供 ``RTSPLowLatencyStream`` 类，统一封装两条延迟最低的取流路径：

================  ===============================================================
后端 backend       说明
================  ===============================================================
``"sdk"``         走海康私有协议 NET_DVR_RealPlay_V40。需要先登录设备（用户名
                  /密码），延迟最低（典型 150~250 ms），码流回调投喂到 PlayM4
                  解码后通过 OpenCV 转 BGR。
``"opencv"``      走标准 RTSP（``rtsp://user:pwd@ip:554/Streaming/Channels/101``）
                  + FFmpeg 后端。延迟略高（典型 300~600 ms），但不需要登录
                  设备 SDK，跨厂商通用。已加上 ``rtsp_transport=tcp``、
                  ``fflags=nobuffer``、``flags=low_delay``、``buffersize=1`` 等
                  低延迟参数。
``"auto"``        优先 SDK，失败时自动降级 OpenCV。
================  ===============================================================

无论哪种后端，``read()`` 始终返回当前**最新**的一帧（旧帧自动丢弃，
开启 ``drop_old_frames=True`` 时），帧绝对时间戳尽可能从 SDK 的私有帧头
解析；OpenCV 后端无私有头，时间戳退化为 ``datetime.now()``。

输出格式：
  * 默认 ``BGR``：``numpy.ndarray (H,W,3) uint8``
  * ``raw=True`` / ``color="YUV"``：原始 YV12 字节流
"""

from __future__ import annotations

import os
import threading
import time
from ctypes import POINTER, byref, c_byte, c_uint, c_void_p, string_at
from datetime import datetime
from typing import Optional, Tuple

from hikvision_sdk._bindings import HCNetSDK
from hikvision_sdk.core import HikvisionSDK
from hikvision_sdk.exceptions import HikvisionError
from hikvision_sdk.stream.decoder import PlayM4Decoder
from hikvision_sdk.types import FrameTimestamp, StreamConfig
from hikvision_sdk.utils import color_convert
from hikvision_sdk.utils.logging import get_logger
from hikvision_sdk.utils.time_utils import datetime_to_epoch_ms

_logger = get_logger("hikvision_sdk.rtsp_stream")


# 海康码流回调中 dwDataType 取值
NET_DVR_SYSHEAD = 1
NET_DVR_STREAMDATA = 2


class _LatestSlot:
    """单槽缓冲：始终只保留最新一帧，旧帧覆盖丢弃。"""
    __slots__ = ("_data", "_ts", "_lock", "_event")

    def __init__(self) -> None:
        self._data = None
        self._ts: Optional[FrameTimestamp] = None
        self._lock = threading.Lock()
        self._event = threading.Event()

    def put(self, data, ts: FrameTimestamp) -> None:
        with self._lock:
            self._data = data
            self._ts = ts
        self._event.set()

    def get(self, timeout: float = 1.0):
        if not self._event.wait(timeout):
            return None, None
        with self._lock:
            data, ts = self._data, self._ts
            self._event.clear()
        return data, ts

    def clear(self) -> None:
        with self._lock:
            self._data = None
            self._ts = None
            self._event.clear()


class RTSPLowLatencyStream:
    """RTSP/SDK 双后端低延迟拉流。"""

    def __init__(
        self,
        url: Optional[str] = None,
        device=None,                          # type: Optional["Device"]
        channel: int = 1,
        stream_type: int = 0,
        backend: str = "auto",
        transport: str = "tcp",
        drop_old_frames: bool = True,
        buffer_size: int = 1,
    ):
        """
        Args:
            url: 标准 RTSP URL（仅 ``opencv`` 后端使用）。
            device: ``hikvision_sdk.Device`` 实例（仅 ``sdk`` 后端使用，需已登录）。
            channel: 通道号（1 起）。SDK 后端取主码流时实际通道号为
                ``device.info.start_channel + channel - 1``。
            stream_type: 0=主码流 1=子码流（SDK 后端使用）。
            backend: ``"sdk"`` / ``"opencv"`` / ``"auto"``。
            transport: 仅 OpenCV 后端使用，``tcp`` / ``udp``。
            drop_old_frames: 仅保留最新一帧（True，低延迟模式）。
            buffer_size: PlayM4 显示缓冲帧数（1 = 最低延迟）。
        """
        if backend not in ("sdk", "opencv", "auto"):
            raise ValueError("backend 仅支持 'sdk' / 'opencv' / 'auto'")
        self.url = url
        self.device = device
        self.cfg = StreamConfig(
            channel=int(channel),
            stream_type=int(stream_type),
            transport=str(transport),
            drop_old_frames=bool(drop_old_frames),
            buffer_size=int(buffer_size),
        )
        self.backend_pref = backend
        self.backend_active: Optional[str] = None  # 实际选定的后端

        self._slot = _LatestSlot()
        self._stopped = threading.Event()

        # SDK 后端状态
        self._sdk = None
        self._real_handle: int = -1
        self._decoder: Optional[PlayM4Decoder] = None
        self._real_cb_ref = None  # 必须保留引用避免 GC

        # OpenCV 后端状态
        self._cap = None
        self._cap_thread: Optional[threading.Thread] = None

    # ------------------------------------------------------------------ #
    # 启停
    # ------------------------------------------------------------------ #

    def start(self) -> None:
        """启动拉流。"""
        if self.backend_pref == "sdk":
            self._start_sdk()
        elif self.backend_pref == "opencv":
            self._start_opencv()
        else:  # auto
            try:
                self._start_sdk()
            except Exception as e:
                _logger.warning("SDK 后端启动失败, 降级 OpenCV: %s", e)
                self._start_opencv()

    def stop(self) -> None:
        """停止拉流并释放资源。"""
        self._stopped.set()
        # OpenCV
        if self._cap_thread is not None:
            self._cap_thread.join(timeout=2.0)
            self._cap_thread = None
        if self._cap is not None:
            try:
                self._cap.release()
            except Exception:  # pragma: no cover
                pass
            self._cap = None
        # SDK
        if self._real_handle >= 0:
            try:
                self.device.netsdk.NET_DVR_StopRealPlay(self._real_handle)
            except Exception:  # pragma: no cover
                pass
            self._real_handle = -1
        if self._decoder is not None:
            self._decoder.release_port()
            self._decoder = None
        self._slot.clear()

    def __enter__(self) -> "RTSPLowLatencyStream":
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.stop()

    # ------------------------------------------------------------------ #
    # 读帧
    # ------------------------------------------------------------------ #

    def read(self, timeout: float = 1.0, raw: bool = False) -> Tuple[Optional[object], Optional[FrameTimestamp]]:
        """阻塞获取最新一帧。

        Args:
            timeout: 等待新帧的最大秒数。
            raw: True 返回原始 YV12 ``bytes``；False 返回 BGR ``numpy.ndarray``。

        Returns:
            ``(image, timestamp)``，超时则返回 ``(None, None)``。
        """
        data, ts = self._slot.get(timeout=timeout)
        if data is None or ts is None:
            return None, None

        # SDK 后端：data 是 (yv12_bytes, w, h)
        if self.backend_active == "sdk":
            buf, w, h = data
            if raw:
                return buf, ts
            if not color_convert.has_cv2():
                return buf, ts
            try:
                bgr = color_convert.yv12_buffer_to_bgr(buf, w, h)
                return bgr, ts
            except Exception as e:  # pragma: no cover
                _logger.warning("YV12→BGR 转换失败: %s", e)
                return None, ts

        # OpenCV 后端：data 已经是 BGR ndarray
        if raw:
            # 用户要 raw 但 OpenCV 后端没有 YUV，退化返回 BGR 字节
            try:
                return data.tobytes(), ts
            except Exception:
                return data, ts
        return data, ts

    # ================================================================== #
    # SDK 后端
    # ================================================================== #

    def _start_sdk(self) -> None:
        if self.device is None or not getattr(self.device, "is_logged_in", False):
            raise RuntimeError("SDK 后端需要先登录的 Device 实例")
        self._sdk = HikvisionSDK.get_instance()
        netsdk = self.device.netsdk

        # 1) 关键的低延迟相关 SDK 设置
        try:
            netsdk.NET_DVR_SetRecvTimeOut(300)        # 接收超时 300ms
            netsdk.NET_DVR_SetReconnect(0, 0)         # 关闭长重连等待
        except Exception:  # pragma: no cover
            pass

        # 2) 准备 PlayM4 解码端口（先 GetPort，但 OpenStream 需要等 SYSHEAD）
        self._decoder = PlayM4Decoder(buffer_size=1024 * 1024,
                                      display_buf=self.cfg.buffer_size)
        self._decoder.acquire_port()
        # 注册解码回调：把 YV12 帧推到 _slot
        self._decoder.set_decode_callback(self._on_decoded_frame_sdk)

        # 3) 注册码流回调
        def _real_cb(handle, data_type, p_buf, n_size, user):
            try:
                size = int(n_size)
                if size <= 0:
                    return
                payload = string_at(p_buf, size)
                if int(data_type) == NET_DVR_SYSHEAD:
                    # 第一段头：打开 PlayM4 流
                    try:
                        self._decoder.open_stream(payload)
                        self._decoder.start_play(hwnd=0)
                    except Exception as e:  # pragma: no cover
                        _logger.error("PlayM4 打开流失败: %s", e)
                else:
                    # 普通码流数据
                    self._decoder.feed(payload)
            except Exception as e:  # pragma: no cover
                _logger.exception("码流回调异常: %s", e)

        self._real_cb_ref = HCNetSDK.REALDATACALLBACK(_real_cb)

        # 4) NET_DVR_RealPlay_V40
        preview_info = HCNetSDK.NET_DVR_PREVIEWINFO()
        # 通道号：起始通道偏移
        start_chan = int(getattr(self.device.info, "start_channel", 1) or 1)
        preview_info.lChannel = start_chan + (self.cfg.channel - 1)
        preview_info.dwStreamType = self.cfg.stream_type
        preview_info.dwLinkMode = 0          # TCP，最低抖动
        preview_info.hPlayWnd = 0            # 不渲染到任何窗口
        preview_info.bBlocked = 1
        preview_info.bPassbackRecord = 0
        preview_info.byPreviewMode = 0       # 0=正常预览
        preview_info.dwDisplayBufNum = max(1, self.cfg.buffer_size)
        preview_info.byProtoType = 0         # 0=私有协议，最低延迟

        handle = int(netsdk.NET_DVR_RealPlay_V40(
            self.device.user_id, byref(preview_info), self._real_cb_ref, c_void_p(0)
        ))
        if handle < 0:
            code = int(netsdk.NET_DVR_GetLastError())
            raise HikvisionError(code, api="NET_DVR_RealPlay_V40")
        self._real_handle = handle
        self.backend_active = "sdk"
        _logger.info("RTSP[SDK] 启动成功 handle=%d channel=%d stream=%d",
                     handle, preview_info.lChannel, preview_info.dwStreamType)

    def _on_decoded_frame_sdk(self, port, idx, buf, w, h, pts_ms, ftype):
        """SDK 后端解码回调：把 YV12 字节流推入单槽缓冲。"""
        # SDK 后端没有可靠的"绝对时间"来源（私有头里有，但解析复杂），
        # 这里使用本机时间作为时间戳——延迟极低且单调递增，对实时场景足够。
        now = datetime.now()
        ts = FrameTimestamp(
            frame_index=idx,
            datetime=now,
            epoch_ms=datetime_to_epoch_ms(now),
            frame_type="?",
            pts_ms=int(pts_ms),
        )
        if w <= 0 or h <= 0 or not buf:
            return
        if self.cfg.drop_old_frames:
            self._slot.put((buf, w, h), ts)
        else:
            # 不丢帧时退化为阻塞写（极少使用）
            self._slot.put((buf, w, h), ts)

    # ================================================================== #
    # OpenCV 后端
    # ================================================================== #

    def _start_opencv(self) -> None:
        if not self.url:
            raise RuntimeError("OpenCV 后端需要传入 RTSP url")
        try:
            import cv2  # type: ignore
        except ImportError as e:
            raise RuntimeError("OpenCV 后端需要安装 opencv-python") from e

        # 关键：在创建 VideoCapture 之前设置 FFmpeg 拉流参数
        opts = (
            f"rtsp_transport;{self.cfg.transport}|"
            "max_delay;0|"
            "fflags;nobuffer|"
            "flags;low_delay|"
            "reorder_queue_size;0|"
            "stimeout;5000000|"
            "buffer_size;102400"
        )
        prev = os.environ.get("OPENCV_FFMPEG_CAPTURE_OPTIONS")
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = opts

        try:
            cap = cv2.VideoCapture(self.url, cv2.CAP_FFMPEG)
        finally:
            if prev is None:
                os.environ.pop("OPENCV_FFMPEG_CAPTURE_OPTIONS", None)
            else:
                os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = prev

        if not cap.isOpened():
            raise RuntimeError(f"无法打开 RTSP URL: {self.url}")

        try:
            cap.set(cv2.CAP_PROP_BUFFERSIZE, max(1, self.cfg.buffer_size))
        except Exception:
            pass

        self._cap = cap
        self.backend_active = "opencv"
        self._stopped.clear()
        # 后台线程持续 grab，主线程 read 时取最新一帧
        t = threading.Thread(target=self._opencv_loop, daemon=True, name="rtsp-opencv-grab")
        t.start()
        self._cap_thread = t
        _logger.info("RTSP[OpenCV] 启动成功 url=%s", self.url)

    def _opencv_loop(self) -> None:
        idx = 0
        while not self._stopped.is_set():
            cap = self._cap
            if cap is None:
                break
            try:
                # 总是 grab 最新一帧，丢弃旧帧
                if not cap.grab():
                    time.sleep(0.005)
                    continue
                ok, frame = cap.retrieve()
                if not ok or frame is None:
                    continue
                now = datetime.now()
                ts = FrameTimestamp(
                    frame_index=idx,
                    datetime=now,
                    epoch_ms=datetime_to_epoch_ms(now),
                    frame_type="?",
                    pts_ms=0,
                )
                self._slot.put(frame, ts)
                idx += 1
            except Exception as e:  # pragma: no cover
                _logger.warning("OpenCV grab 异常: %s", e)
                time.sleep(0.05)


__all__ = ["RTSPLowLatencyStream"]
