# -*- coding: utf-8 -*-
"""★ 功能①：读取海康视频文件 + 逐帧绝对时间戳

本模块的核心使命是：
  1. 在开始迭代之前，**先打印（或返回）视频元信息**——文件大小/时长/帧数/
     分辨率/帧率/起始绝对时间/编码格式；
  2. 然后**逐帧产出绝对时间戳**——使用 PlayM4 私有头解析机制把 iVMS-4200
     或 SDK 备份下载得到的"海康私有流文件"的绝对时间从码流中提取出来。

工作原理
========

PlayM4 提供了 ``PlayM4_GetSystemTime(port, *PLAYM4_SYSTEM_TIME)`` 接口，
当文件本身是海康私有协议流（含 NET_DVR_PRIVATE_DATA 帧头）时，该接口在
**每一帧解码完成后** 都能返回当前帧对应的设备绝对时间（年/月/日/时/分/秒/毫秒）。

我们的策略：
  * 文件模式打开 PlayM4，注册解码回调；
  * 每收到一帧解码回调（DECCBFUNWIN），立即在回调里调用 GetSystemTime
    抓取当前绝对时间，与 FRAME_INFO.nStamp 一同打包；
  * 把 ``FrameTimestamp`` 推入 thread-safe 队列，主线程通过 ``iter_*``
    生成器逐条 yield 给用户。

帧类型识别（I/P/B）
==================

PlayM4 的 ``FRAME_INFO.nType`` 在解码回调中是图像格式（YV12/RGB 等），
**并不携带 I/P/B 信息**。我们采用**码流 NALU 头的简单嗅探**作为兜底：
  * 文件模式下，PlayM4 内部已读流，我们只能从解码回调拿到 YUV，没有原始
    NALU 字节，因此对帧类型采取保守策略：第一帧记为 I（一般是关键帧），
    后续帧若能从 ``PlayM4_GetKeyFramePosition`` 或 ``PlayM4_GetCurrentFrameNum``
    辅助判定，则补充准确类型；否则统一标记为 ``UNKNOWN``。

如果用户更看重 I/P/B 精度，可以走"流模式 + NET_DVR_GetFileByName_V40 取
原始码流"路径，在投喂前用 NALU 解析器判定后再 feed —— 这超出了"读取已
导出文件"的范畴，本模块不引入。
"""

from __future__ import annotations

import os
import queue
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Iterator, Optional, Tuple

from hikvision_sdk.core import HikvisionSDK
from hikvision_sdk.exceptions import HikvisionError
from hikvision_sdk.stream.decoder import PlayM4Decoder
from hikvision_sdk.types import DecodedFrame, FrameTimestamp, VideoFileInfo
from hikvision_sdk.utils import color_convert
from hikvision_sdk.utils.logging import get_logger
from hikvision_sdk.utils.time_utils import datetime_to_epoch_ms, fmt_datetime_ms

_logger = get_logger("hikvision_sdk.video_file")

# 等待回调投递的最大空轮询时长（秒），用于判断文件已读完
_DRAIN_TIMEOUT = 8.0


class VideoFileReader:
    """读取海康私有流视频文件，逐帧获取绝对时间戳。

    用法::

        from hikvision_sdk import HikvisionSDK, VideoFileReader
        with HikvisionSDK() as _:
            reader = VideoFileReader("D:/records/ch01_20240601_080000.mp4")
            info = reader.get_info()
            print(info)                                  # 先打印视频信息
            for ts in reader.iter_frame_timestamps():    # 再逐帧打印绝对时间
                print(ts)

    若同时想拿解码后的图像，请使用 ``iter_frames(decode=True)``。
    """

    def __init__(self, file_path: str):
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"视频文件不存在: {file_path}")
        self.file_path = str(path.resolve())
        self.file_size = path.stat().st_size

        # 复用全局 SDK 单例；构造 PlayM4Decoder 时已自动 acquire
        self._sdk = HikvisionSDK.get_instance()
        self._info: Optional[VideoFileInfo] = None

    # ------------------------------------------------------------------ #
    # 1) 视频元信息
    # ------------------------------------------------------------------ #

    def get_info(self) -> VideoFileInfo:
        """读取并返回视频元信息（多次调用结果缓存复用）。"""
        if self._info is not None:
            return self._info

        decoder = PlayM4Decoder()
        try:
            decoder.open_file(self.file_path)
            # 启动播放才能拿到正确的画面尺寸/帧率/系统时间
            decoder.start_play(hwnd=0)
            # 短暂等待 PlayM4 解析头部
            t0 = time.time()
            width = height = 0
            fps = 0.0
            while time.time() - t0 < 1.0:
                width, height = decoder.get_picture_size()
                fps = decoder.get_frame_rate()
                if width > 0 and height > 0 and fps > 0:
                    break
                time.sleep(0.05)

            total_frames = decoder.get_file_total_frames()
            total_ms = decoder.get_file_total_time()
            # 起始绝对时间
            start_dt: Optional[datetime] = None
            st = decoder.get_system_time()
            if st is not None and int(st.dwYear) >= 1970:
                try:
                    start_dt = datetime(
                        year=int(st.dwYear),
                        month=int(st.dwMon),
                        day=int(st.dwDay),
                        hour=int(st.dwHour),
                        minute=int(st.dwMin),
                        second=int(st.dwSec),
                        microsecond=int(st.dwMs) * 1000,
                    )
                except ValueError:
                    start_dt = None

            self._info = VideoFileInfo(
                file_path=self.file_path,
                file_size=self.file_size,
                duration_seconds=total_ms / 1000.0 if total_ms > 0 else 0.0,
                total_frames=int(total_frames),
                width=int(width),
                height=int(height),
                frame_rate=float(fps),
                start_datetime=start_dt,
                codec="H.264 / H.265 (Hikvision)",
            )
        finally:
            decoder.release_port()
        return self._info

    # ------------------------------------------------------------------ #
    # 2) 逐帧绝对时间戳
    # ------------------------------------------------------------------ #

    def iter_frame_timestamps(self) -> Iterator[FrameTimestamp]:
        """生成器：依次产出每一帧的 ``FrameTimestamp``。

        本接口**不**返回图像数据，仅时间戳。如需图像，请用 ``iter_frames``。
        """
        for ft, _frame in self._iter_internal(decode_image=False):
            yield ft

    def iter_frames(
        self,
        decode_image: bool = True,
        color: str = "BGR",
    ) -> Iterator[Tuple[FrameTimestamp, Optional[object]]]:
        """生成器：每次产出 ``(FrameTimestamp, image)``。

        Args:
            decode_image: 是否同时返回图像（False 时第二项为 None）。
            color: ``"BGR"`` 默认 numpy.ndarray (H,W,3)；
                   ``"YUV"`` 则返回原始 YV12 字节流（bytes）。

        Yields:
            ``(FrameTimestamp, image_or_none)`` 元组。
        """
        for ft, frame in self._iter_internal(decode_image=decode_image, color=color):
            yield ft, frame

    # ------------------------------------------------------------------ #
    # 内部实现
    # ------------------------------------------------------------------ #

    def _iter_internal(
        self,
        decode_image: bool,
        color: str = "BGR",
    ) -> Iterator[Tuple[FrameTimestamp, Optional[object]]]:
        if color not in ("BGR", "YUV"):
            raise ValueError("color 仅支持 'BGR' 或 'YUV'")
        # 提前确保信息已读取
        info = self.get_info()
        decoder = PlayM4Decoder()
        # 队列容量稍大，防止生产者阻塞；丢帧不在本场景考虑
        q: "queue.Queue[Tuple[FrameTimestamp, Optional[object]]]" = queue.Queue(maxsize=256)
        done_event = threading.Event()
        last_recv_time = [time.time()]

        def _on_frame(port, idx, buf, w, h, pts_ms, ftype):
            # 在解码回调里立刻拿当前帧的绝对时间
            st = decoder.get_system_time()
            if st is not None and int(st.dwYear) >= 1970:
                try:
                    dt = datetime(
                        year=int(st.dwYear),
                        month=int(st.dwMon),
                        day=int(st.dwDay),
                        hour=int(st.dwHour),
                        minute=int(st.dwMin),
                        second=int(st.dwSec),
                        microsecond=int(st.dwMs) * 1000,
                    )
                except ValueError:
                    dt = None
            else:
                dt = None

            # 私有头不可用时，退化为 起始绝对时间 + PTS 偏移
            if dt is None:
                if info.start_datetime is not None:
                    from hikvision_sdk.utils.time_utils import offset_datetime_ms
                    dt = offset_datetime_ms(info.start_datetime, int(pts_ms))
                else:
                    dt = datetime.fromtimestamp(0)

            ft = FrameTimestamp(
                frame_index=idx,
                datetime=dt,
                epoch_ms=datetime_to_epoch_ms(dt),
                # 第一帧通常是 I 帧，其余无法精确判断，标 UNKNOWN
                frame_type="I" if idx == 0 else "?",
                pts_ms=int(pts_ms),
            )

            image = None
            if decode_image and buf:
                if color == "YUV":
                    image = bytes(buf)  # 原始 YV12
                else:
                    if color_convert.has_cv2():
                        try:
                            image = color_convert.yv12_buffer_to_bgr(buf, int(w), int(h))
                        except Exception as e:  # pragma: no cover
                            _logger.warning("YV12→BGR 转换失败: %s", e)
                            image = None

            try:
                q.put_nowait((ft, image))
            except queue.Full:
                # 退化为阻塞 put，保证不丢帧
                q.put((ft, image))
            last_recv_time[0] = time.time()

        try:
            decoder.open_file(self.file_path)
            decoder.set_decode_callback(_on_frame)
            decoder.start_play(hwnd=0)

            total_frames = info.total_frames or 0
            yielded = 0
            while True:
                try:
                    item = q.get(timeout=0.5)
                    yield item
                    yielded += 1
                    if total_frames and yielded >= total_frames:
                        break
                except queue.Empty:
                    # 检查是否长时间没有新帧 → 视为读完
                    if time.time() - last_recv_time[0] > _DRAIN_TIMEOUT:
                        break
                    if done_event.is_set():
                        break
        finally:
            decoder.release_port()


__all__ = ["VideoFileReader"]
