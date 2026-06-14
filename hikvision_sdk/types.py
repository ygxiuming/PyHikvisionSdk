# -*- coding: utf-8 -*-
"""面向用户的数据类。

把底层 ctypes 结构体翻译成更易用的 Python ``dataclass``，
让上层代码不必直接接触 ctypes 类型。
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, Tuple


@dataclass
class DeviceInfo:
    """登录后从设备返回的基本信息。"""

    serial_number: str = ""        # 设备序列号
    device_type: int = 0           # 设备类型代号
    channel_num: int = 0           # 模拟通道总数
    ip_channel_num: int = 0        # 数字（IP）通道总数
    start_channel: int = 1         # 起始通道号
    start_ip_channel: int = 1      # IP 起始通道号
    audio_channel_num: int = 0     # 音频通道数
    zero_channel_num: int = 0      # 零通道编码数
    alarm_in_num: int = 0          # 报警输入数
    alarm_out_num: int = 0         # 报警输出数
    disk_num: int = 0              # 硬盘数
    user_id: int = -1              # 登录返回的 userID

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class FrameTimestamp:
    """单帧的绝对时间戳信息（功能①输出的核心结构）。"""

    frame_index: int               # 帧序号（自 0 开始）
    datetime: datetime             # 绝对时间（datetime 对象）
    epoch_ms: int                  # Unix 毫秒时间戳
    frame_type: str                # 帧类型: I / P / B / 未知
    pts_ms: int                    # 相对 PTS（毫秒），由 PlayM4 给出

    @property
    def datetime_str(self) -> str:
        """格式化为 ``YYYY-MM-DD HH:MM:SS.mmm``。"""
        return self.datetime.strftime("%Y-%m-%d %H:%M:%S.") + f"{self.datetime.microsecond // 1000:03d}"

    def __str__(self) -> str:
        return (
            f"#{self.frame_index:06d}  {self.datetime_str}  "
            f"epoch_ms={self.epoch_ms}  type={self.frame_type}  pts={self.pts_ms}ms"
        )


@dataclass
class VideoFileInfo:
    """海康视频文件元信息。"""

    file_path: str
    file_size: int                       # 文件字节数
    duration_seconds: float              # 总时长（秒）
    total_frames: int                    # 总帧数
    width: int
    height: int
    frame_rate: float                    # 平均帧率
    start_datetime: Optional[datetime]   # 文件起始绝对时间（首帧）
    codec: str = "H.264"                 # 编码格式（多数海康设备默认 H.264）

    @property
    def resolution(self) -> Tuple[int, int]:
        return self.width, self.height

    def __str__(self) -> str:
        size_mb = self.file_size / (1024 * 1024)
        start = self.start_datetime.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] if self.start_datetime else "未知"
        return (
            f"[视频信息]\n"
            f"  文件: {self.file_path}\n"
            f"  大小: {size_mb:.2f} MB ({self.file_size} bytes)\n"
            f"  总时长: {self.duration_seconds:.2f} s\n"
            f"  总帧数: {self.total_frames}\n"
            f"  分辨率: {self.width}x{self.height}\n"
            f"  帧率: {self.frame_rate:.2f} fps\n"
            f"  起始绝对时间: {start}\n"
            f"  编码: {self.codec}"
        )


@dataclass
class DecodedFrame:
    """解码后输出的一帧图像（YUV / BGR）。"""

    frame_index: int
    width: int
    height: int
    pts_ms: int                          # 相对 PTS（PlayM4 给出，毫秒）
    timestamp: Optional[FrameTimestamp]  # 绝对时间戳（如能解析）
    data: object                         # numpy.ndarray（BGR）或 bytes（YUV）
    is_yuv: bool = False                 # True=raw YUV bytes, False=BGR numpy


@dataclass
class StreamConfig:
    """实时预览/RTSP 拉流的统一参数。"""

    channel: int = 1                # 通道号（1 起）
    stream_type: int = 0            # 0=主码流 1=子码流 2=三码流
    link_mode: int = 0              # 0=TCP 1=UDP 2=多播 3=RTP 4=RTP/RTSP 5=RTP/HTTP
    blocked: int = 1                # 阻塞取流（1=阻塞，0=非阻塞）
    transport: str = "tcp"          # 仅 OpenCV 后端使用：tcp/udp
    drop_old_frames: bool = True    # 旧帧丢弃，仅保留最新（低延迟模式）
    buffer_size: int = 1            # 解码缓冲帧数（1 = 最低延迟）

    def is_main_stream(self) -> bool:
        return self.stream_type == 0
