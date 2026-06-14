# -*- coding: utf-8 -*-
"""YUV → BGR 颜色空间转换工具。

PlayM4 解码回调输出的图像数据默认为 YV12（即 I420 的 U/V 平面互换变体），
其内存布局为：

    [Y 平面: width * height]
    [V 平面: (width/2) * (height/2)]
    [U 平面: (width/2) * (height/2)]

OpenCV 的 ``cv2.cvtColor`` 提供了 ``COLOR_YUV2BGR_YV12`` 常量可直接转换。
"""

from __future__ import annotations

from typing import Optional

try:
    import numpy as np  # type: ignore
except ImportError:  # pragma: no cover
    np = None  # type: ignore

try:
    import cv2  # type: ignore
except ImportError:  # pragma: no cover
    cv2 = None  # type: ignore


def yv12_buffer_to_bgr(buf: bytes, width: int, height: int) -> "np.ndarray":
    """把 YV12 缓冲区转成 BGR ``numpy.ndarray``。

    Args:
        buf: 长度为 ``width * height * 3 // 2`` 的字节流（YV12）。
        width: 图像宽度。
        height: 图像高度。

    Returns:
        形状为 ``(height, width, 3)`` 的 BGR uint8 数组。
    """
    if np is None or cv2 is None:
        raise RuntimeError("需要 numpy 与 opencv-python 才能进行 YV12→BGR 转换")
    expected = width * height * 3 // 2
    if len(buf) < expected:
        raise ValueError(
            f"YV12 缓冲区长度不足: 期望 {expected} 字节, 实际 {len(buf)}"
        )
    yuv = np.frombuffer(buf[:expected], dtype=np.uint8).reshape(height * 3 // 2, width)
    # PlayM4 输出的是 YV12（YYYY VV UU），cv2 用 COLOR_YUV2BGR_YV12 即可
    bgr = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR_YV12)
    return bgr


def yv12_buffer_to_yuv_array(buf: bytes, width: int, height: int) -> "np.ndarray":
    """直接把 YV12 缓冲区包成 numpy 数组（不做颜色转换）。"""
    if np is None:
        raise RuntimeError("需要 numpy 才能创建 YUV 数组")
    expected = width * height * 3 // 2
    if len(buf) < expected:
        raise ValueError(
            f"YV12 缓冲区长度不足: 期望 {expected} 字节, 实际 {len(buf)}"
        )
    return np.frombuffer(buf[:expected], dtype=np.uint8).copy()


def has_cv2() -> bool:
    """是否安装了 opencv-python。"""
    return cv2 is not None


def has_numpy() -> bool:
    """是否安装了 numpy。"""
    return np is not None
