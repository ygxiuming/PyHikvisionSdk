# -*- coding: utf-8 -*-
"""JPEG 抓图（NET_DVR_CaptureJPEGPicture_NEW）。"""

from __future__ import annotations

import os
from ctypes import POINTER, Structure, byref, c_byte, c_uint, create_string_buffer
from typing import Optional, Tuple

from hikvision_sdk.exceptions import HikvisionError
from hikvision_sdk.utils.logging import get_logger

_logger = get_logger("hikvision_sdk.snapshot")


class _NET_DVR_JPEGPARA(Structure):
    """JPEG 抓图参数。"""
    _fields_ = [
        ("wPicSize", c_uint),     # 0=CIF 1=QCIF 2=4CIF 3=D1 4=UXGA 5=SVGA 6=HD720P
        ("wPicQuality", c_uint),  # 0=最佳 1=较好 2=一般
    ]


# 图像尺寸常量
PIC_SIZE_CIF = 0
PIC_SIZE_QCIF = 1
PIC_SIZE_4CIF = 2
PIC_SIZE_D1 = 3
PIC_SIZE_UXGA = 4
PIC_SIZE_SVGA = 5
PIC_SIZE_HD720P = 6
PIC_SIZE_VGA = 7
PIC_SIZE_XVGA = 8
PIC_SIZE_HD900P = 9
PIC_SIZE_HD1080P = 0xff


def capture_jpeg_to_file(device, channel: int, save_path: str,
                         pic_size: int = PIC_SIZE_HD1080P, quality: int = 0) -> str:
    """抓图并保存为 JPEG 文件。"""
    save_path = os.path.abspath(save_path)
    os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)
    para = _NET_DVR_JPEGPARA()
    para.wPicSize = int(pic_size)
    para.wPicQuality = int(quality)
    start_chan = int(getattr(device.info, "start_channel", 1) or 1)
    real_chan = start_chan + (int(channel) - 1)

    ok = device.netsdk.NET_DVR_CaptureJPEGPicture(
        device.user_id, real_chan, byref(para), save_path.encode("utf-8")
    )
    if not ok:
        code = int(device.netsdk.NET_DVR_GetLastError())
        raise HikvisionError(code, api="NET_DVR_CaptureJPEGPicture")
    _logger.info("抓图成功: %s", save_path)
    return save_path


def capture_jpeg(device, channel: int, max_size: int = 2 * 1024 * 1024,
                 pic_size: int = PIC_SIZE_HD1080P, quality: int = 0) -> bytes:
    """抓图并直接返回 JPEG 字节流（不落盘）。"""
    para = _NET_DVR_JPEGPARA()
    para.wPicSize = int(pic_size)
    para.wPicQuality = int(quality)
    start_chan = int(getattr(device.info, "start_channel", 1) or 1)
    real_chan = start_chan + (int(channel) - 1)

    buf = create_string_buffer(int(max_size))
    written = c_uint(0)
    ok = device.netsdk.NET_DVR_CaptureJPEGPicture_NEW(
        device.user_id, real_chan, byref(para),
        buf, int(max_size), byref(written)
    )
    if not ok:
        code = int(device.netsdk.NET_DVR_GetLastError())
        raise HikvisionError(code, api="NET_DVR_CaptureJPEGPicture_NEW")
    return buf.raw[: int(written.value)]


__all__ = [
    "capture_jpeg_to_file", "capture_jpeg",
    "PIC_SIZE_CIF", "PIC_SIZE_QCIF", "PIC_SIZE_4CIF", "PIC_SIZE_D1",
    "PIC_SIZE_UXGA", "PIC_SIZE_SVGA", "PIC_SIZE_HD720P", "PIC_SIZE_VGA",
    "PIC_SIZE_XVGA", "PIC_SIZE_HD900P", "PIC_SIZE_HD1080P",
]
