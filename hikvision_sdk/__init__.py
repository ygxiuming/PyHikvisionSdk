# -*- coding: utf-8 -*-
"""hikvision_sdk —— 海康威视 HCNetSDK 的纯 Python 封装

模块速览
========

* :class:`hikvision_sdk.HikvisionSDK`  —— SDK 单例（初始化/清理）
* :class:`hikvision_sdk.Device`        —— 设备登录登出
* :class:`hikvision_sdk.VideoFileReader` —— ★ 功能①：读取本地视频文件并
  逐帧获取绝对时间戳
* :class:`hikvision_sdk.RTSPLowLatencyStream` —— ★ 功能②：低延迟 RTSP/SDK
  双后端拉流
* :class:`hikvision_sdk.LiveStream`    —— 实时预览（原始码流回调）
* :class:`hikvision_sdk.PlayBack`      —— 远程录像查询/下载
* :class:`hikvision_sdk.PTZController` —— 云台控制
* :mod:`hikvision_sdk.snapshot`        —— JPEG 抓图
* :class:`hikvision_sdk.AlarmListener` —— 报警布防/事件监听
* :mod:`hikvision_sdk.config`          —— 通用远程参数 Get/Set

整个项目所有海康动态库**仅**依赖工程根目录下的 ``sdk/win`` 与 ``sdk/linux``，
两个原始解压目录可以删除而不影响功能。
"""

from .core import HikvisionSDK
from .device import Device
from .exceptions import HikvisionError, describe_error
from .types import (
    DeviceInfo, FrameTimestamp, VideoFileInfo, DecodedFrame, StreamConfig,
)
from .video_file import VideoFileReader
from .rtsp_stream import RTSPLowLatencyStream
from .stream import LiveStream, PlayBack, PlayM4Decoder, RecordFile
from .ptz import PTZController
from .alarm import AlarmListener
from . import snapshot, config

__all__ = [
    "HikvisionSDK",
    "Device",
    "HikvisionError",
    "describe_error",
    "DeviceInfo",
    "FrameTimestamp",
    "VideoFileInfo",
    "DecodedFrame",
    "StreamConfig",
    "VideoFileReader",
    "RTSPLowLatencyStream",
    "LiveStream",
    "PlayBack",
    "PlayM4Decoder",
    "RecordFile",
    "PTZController",
    "AlarmListener",
    "snapshot",
    "config",
]

__version__ = "1.0.0"
