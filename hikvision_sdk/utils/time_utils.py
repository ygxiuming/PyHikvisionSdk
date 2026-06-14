# -*- coding: utf-8 -*-
"""海康私有时间结构体与 datetime 之间的转换。

海康 SDK 中用到的时间结构体主要有两种：

  - ``NET_DVR_TIME``：YYYY/MM/DD HH:MM:SS（秒级精度）
  - ``NET_DVR_TIME_EX``：增加了毫秒字段，部分回放/私有头里使用
  - ``NET_DVR_TIME_V30``：兼容字段，结构与 NET_DVR_TIME 类似

对于"导出录像文件每帧的绝对时间戳"，海康在私有协议里把
帧的绝对时间打进了 ``FRAME_INFO.nStamp``（相对毫秒）配合
``PlayM4_GetSystemTime``（绝对时间结构体）一起使用。
"""

from __future__ import annotations

import time
from datetime import datetime, timezone, timedelta
from typing import Optional


def net_dvr_time_to_datetime(ndt) -> datetime:
    """把 ``NET_DVR_TIME`` 结构体转成 ``datetime``（按本地时区解释）。"""
    return datetime(
        year=int(ndt.dwYear),
        month=int(ndt.dwMonth),
        day=int(ndt.dwDay),
        hour=int(ndt.dwHour),
        minute=int(ndt.dwMinute),
        second=int(ndt.dwSecond),
    )


def net_dvr_time_ex_to_datetime(ndt_ex) -> datetime:
    """把 ``NET_DVR_TIME_EX`` 结构体转成 ``datetime``，含毫秒。"""
    base = datetime(
        year=int(ndt_ex.wYear),
        month=int(ndt_ex.byMonth),
        day=int(ndt_ex.byDay),
        hour=int(ndt_ex.byHour),
        minute=int(ndt_ex.byMinute),
        second=int(ndt_ex.bySecond),
    )
    ms = int(getattr(ndt_ex, "wMilliSec", 0) or 0)
    return base.replace(microsecond=ms * 1000)


def datetime_to_epoch_ms(dt: datetime) -> int:
    """``datetime`` 转 Unix 毫秒时间戳。

    若 ``dt`` 是 naive datetime，按本地时区解释（与海康设备行为一致）。
    """
    if dt.tzinfo is None:
        ts = time.mktime(dt.timetuple()) + dt.microsecond / 1_000_000.0
    else:
        ts = dt.timestamp()
    return int(ts * 1000)


def epoch_ms_to_datetime(ms: int, tz: Optional[timezone] = None) -> datetime:
    """Unix 毫秒时间戳转 ``datetime``。"""
    seconds = ms / 1000.0
    if tz is None:
        return datetime.fromtimestamp(seconds)
    return datetime.fromtimestamp(seconds, tz=tz)


def offset_datetime_ms(base: datetime, ms: int) -> datetime:
    """在某个绝对时间基础上加 ``ms`` 毫秒。"""
    return base + timedelta(milliseconds=ms)


def fmt_datetime_ms(dt: datetime) -> str:
    """格式化为 ``YYYY-MM-DD HH:MM:SS.mmm``（毫秒精度）。"""
    return dt.strftime("%Y-%m-%d %H:%M:%S.") + f"{dt.microsecond // 1000:03d}"


def now_local() -> datetime:
    """返回当前本地时间。"""
    return datetime.now()
