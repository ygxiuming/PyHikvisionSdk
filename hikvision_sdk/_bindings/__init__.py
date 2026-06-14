# -*- coding: utf-8 -*-
"""底层 ctypes 绑定层。

外部代码请通过本包的更高层 API（``hikvision_sdk.core``、``hikvision_sdk.device``
等）使用，本子包仅做最薄的 ctypes 类型映射，等价于官方 Demo 中的 ``HCNetSDK.py``
和 ``PlayCtrl.py``。

为了保持与海康官方头文件 ``HCNetSDK.h`` / ``plaympeg4.h`` 的命名一致，
我们直接以 ``HCNetSDK`` 与 ``PlayCtrl`` 这两个子模块对外暴露。
"""

from . import loader  # noqa: F401
from . import _HCNetSDK_official as HCNetSDK  # noqa: F401
from . import _PlayCtrl_official as PlayCtrl  # noqa: F401

__all__ = ["loader", "HCNetSDK", "PlayCtrl"]
