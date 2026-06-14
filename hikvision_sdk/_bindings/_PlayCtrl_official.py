# -*- coding: utf-8 -*-
"""
PlayCtrl(PlayM4) 库的 ctypes 绑定。

本文件基于海康官方 Demo（CH-HCNetSDKV6.1.9.48 Linux Python 示例）改造，
仅修改 .dll/.so 的查找路径来源，使其指向工程根目录下的 sdk/win 或 sdk/linux，
其余结构体、回调签名保持与官方一致，便于直接复用 SDK 文档中的字段说明。
"""

import os
from ctypes import (
    Structure, POINTER, c_long, c_char, c_char_p,
    cdll, windll, CFUNCTYPE, WINFUNCTYPE,
)

# 复用 HCNetSDK 模块里检测好的平台信息，避免重复检测
from hikvision_sdk._bindings._HCNetSDK_official import (
    sys_platform, system_type, C_DWORD,
)
from hikvision_sdk._bindings.loader import resolve_playctrl_dll_path as _resolve_playctrl_dll_path


# 根据平台选择函数调用约定与库加载器
if sys_platform == 'linux':
    load_library = cdll.LoadLibrary
    fun_ctype = CFUNCTYPE
elif sys_platform == 'windows':
    load_library = windll.LoadLibrary
    fun_ctype = WINFUNCTYPE
else:
    raise RuntimeError("************不支持的平台**************")


# PlayM4(PlayCtrl) 动态库的绝对路径，由 loader 统一解析
playM4dllpath = _resolve_playctrl_dll_path(system_type)


# ---------------------------------------------------------------------------
# 帧信息结构体（PlayM4 解码回调使用）
# ---------------------------------------------------------------------------
class FRAME_INFO(Structure):
    """解码输出的视频帧信息。

    字段说明（与 plaympeg4.h 中 FRAME_INFO 一致）：
      - nWidth      : 图像宽度，单位像素
      - nHeight     : 图像高度，单位像素
      - nStamp      : 时间戳，单位毫秒（PlayM4 内部相对时间）
      - nType       : 数据类型（T_YV12=3, T_RGB32=7 等，参考 plaympeg4.h）
      - nFrameRate  : 当前码流帧率
      - dwFrameNum  : 帧序号（自 1 开始递增）
    """
    _fields_ = [
        ('nWidth', c_long),
        ('nHeight', c_long),
        ('nStamp', c_long),
        ('nType', c_long),
        ('nFrameRate', c_long),
        ('dwFrameNum', C_DWORD),
    ]


LPFRAME_INFO = POINTER(FRAME_INFO)

# 显示回调：PlayM4_SetDisplayCallBack 使用，参数为 (port, buf, size, w, h, type, stamp, reserved)
DISPLAYCBFUN = fun_ctype(None, c_long, c_char_p, c_long, c_long, c_long, c_long, c_long, c_long)
# 解码回调：PlayM4_SetDecCallBackMend 使用，参数为 (port, buf, size, frameInfo*, user, reserved)
DECCBFUNWIN = fun_ctype(None, c_long, POINTER(c_char), c_long, POINTER(FRAME_INFO), c_long, c_long)
