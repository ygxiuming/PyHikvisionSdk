# -*- coding: utf-8 -*-
"""统一的中文日志格式化器。

业务代码可通过 ``get_logger("xxx")`` 拿到一个已配置好的 logger，
默认输出到 stderr，格式为：

    2024-06-01 10:00:00.123 [INFO] hikvision_sdk.device: 登录成功 ...
"""

from __future__ import annotations

import logging
import sys


_FORMAT = "%(asctime)s.%(msecs)03d [%(levelname)s] %(name)s: %(message)s"
_DATEFMT = "%Y-%m-%d %H:%M:%S"

_configured = False


def configure(level: int = logging.INFO) -> None:
    """配置根日志器，仅生效一次。"""
    global _configured
    if _configured:
        return
    handler = logging.StreamHandler(stream=sys.stderr)
    handler.setFormatter(logging.Formatter(_FORMAT, datefmt=_DATEFMT))
    root = logging.getLogger("hikvision_sdk")
    root.addHandler(handler)
    root.setLevel(level)
    root.propagate = False
    _configured = True


def get_logger(name: str = "hikvision_sdk") -> logging.Logger:
    """获取已配置的 logger。"""
    configure()
    return logging.getLogger(name)
