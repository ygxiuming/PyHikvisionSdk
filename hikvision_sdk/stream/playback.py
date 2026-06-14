# -*- coding: utf-8 -*-
"""按时间区间或文件名远程回放/下载录像。

提供两种典型用法：
  1. ``PlayBack.find_files(...)`` 查询某通道一段时间内的录像文件清单；
  2. ``PlayBack.download_by_time(...)`` 直接按时间段把录像下载到本地。

由于官方提供的 ``HCNetSDK.py`` 绑定**未包含**回放相关结构体，
本文件在此就地补充最常用的几个（NET_DVR_TIME / NET_DVR_FILECOND_V40 /
NET_DVR_FINDDATA_V30 / NET_DVR_PLAYCOND）。
"""

from __future__ import annotations

import os
import time
from ctypes import (
    POINTER, Structure, byref, c_byte, c_char, c_int, c_uint, c_ulong, c_ushort,
)
from datetime import datetime
from typing import List, Optional

from hikvision_sdk._bindings import HCNetSDK
from hikvision_sdk.exceptions import HikvisionError
from hikvision_sdk.utils.logging import get_logger

_logger = get_logger("hikvision_sdk.stream.playback")


# ---------------------------------------------------------------------------
# 回放专用结构体（HCNetSDK.h 中的简化版）
# ---------------------------------------------------------------------------
class _NET_DVR_TIME(Structure):
    """与 HCNetSDK.h 中 NET_DVR_TIME 一致：6 个 DWORD 字段。"""
    _fields_ = [
        ("dwYear", c_uint),
        ("dwMonth", c_uint),
        ("dwDay", c_uint),
        ("dwHour", c_uint),
        ("dwMinute", c_uint),
        ("dwSecond", c_uint),
    ]


class _NET_DVR_FILECOND_V40(Structure):
    """文件查询条件（V40）。"""
    _fields_ = [
        ("lChannel", c_int),
        ("dwFileType", c_uint),
        ("dwIsLocked", c_uint),
        ("dwUseCardNo", c_uint),
        ("sCardNumber", c_byte * 32),
        ("struStartTime", _NET_DVR_TIME),
        ("struStopTime", _NET_DVR_TIME),
        ("byDrawFrame", c_byte),
        ("byFindType", c_byte),
        ("byQuickSearch", c_byte),
        ("byRes2", c_byte),
        ("dwStreamType", c_uint),
        ("byRes3", c_byte * 32),
    ]


class _NET_DVR_FINDDATA_V30(Structure):
    """文件查询结果（V30）。"""
    _fields_ = [
        ("sFileName", c_char * 100),
        ("struStartTime", _NET_DVR_TIME),
        ("struStopTime", _NET_DVR_TIME),
        ("dwFileSize", c_uint),
        ("sCardNum", c_char * 32),
        ("byLocked", c_byte),
        ("byFileType", c_byte),
        ("byRes", c_byte * 2),
    ]


class _NET_DVR_PLAYCOND(Structure):
    """按时间段下载/回放的条件。"""
    _fields_ = [
        ("dwChannel", c_uint),
        ("struStartTime", _NET_DVR_TIME),
        ("struStopTime", _NET_DVR_TIME),
        ("byDrawFrame", c_byte),
        ("byStreamType", c_byte),
        ("byRes", c_byte * 6),
    ]


# 文件查询返回值
NET_DVR_FILE_SUCCESS = 1000
NET_DVR_FILE_NOFIND = 1001
NET_DVR_ISFINDING = 1002
NET_DVR_NOMOREFILE = 1003
NET_DVR_FILE_EXCEPTION = 1004


def _to_struct_time(dt: datetime) -> _NET_DVR_TIME:
    s = _NET_DVR_TIME()
    s.dwYear = dt.year
    s.dwMonth = dt.month
    s.dwDay = dt.day
    s.dwHour = dt.hour
    s.dwMinute = dt.minute
    s.dwSecond = dt.second
    return s


def _from_struct_time(s: _NET_DVR_TIME) -> datetime:
    return datetime(int(s.dwYear), int(s.dwMonth), int(s.dwDay),
                    int(s.dwHour), int(s.dwMinute), int(s.dwSecond))


# ---------------------------------------------------------------------------
# 录像查询
# ---------------------------------------------------------------------------
class RecordFile:
    """单条录像文件信息。"""
    __slots__ = ("name", "start", "stop", "size_bytes", "locked", "file_type")

    def __init__(self, name: str, start: datetime, stop: datetime,
                 size_bytes: int, locked: bool, file_type: int):
        self.name = name
        self.start = start
        self.stop = stop
        self.size_bytes = size_bytes
        self.locked = locked
        self.file_type = file_type

    @property
    def duration_seconds(self) -> int:
        return int((self.stop - self.start).total_seconds())

    def __repr__(self) -> str:
        s = self.start.strftime("%Y-%m-%d %H:%M:%S")
        e = self.stop.strftime("%H:%M:%S")
        return (f"RecordFile(name={self.name}, {s} -> {e}, "
                f"{self.size_bytes / 1024 / 1024:.2f} MB)")


class PlayBack:
    """远程回放/下载封装。"""

    def __init__(self, device):
        self.device = device
        self.netsdk = device.netsdk

    # ------------------------------------------------------------------ #
    # 录像文件查询
    # ------------------------------------------------------------------ #

    def find_files(
        self,
        channel: int,
        start: datetime,
        stop: datetime,
        stream_type: int = 0,
        max_files: int = 5000,
    ) -> List[RecordFile]:
        """查询某通道在指定时间段内的录像文件。"""
        cond = _NET_DVR_FILECOND_V40()
        start_chan = int(getattr(self.device.info, "start_channel", 1) or 1)
        cond.lChannel = start_chan + (int(channel) - 1)
        cond.dwFileType = 0xFF       # 0xFF=全部类型
        cond.dwIsLocked = 0xFF
        cond.dwUseCardNo = 0
        cond.struStartTime = _to_struct_time(start)
        cond.struStopTime = _to_struct_time(stop)
        cond.dwStreamType = int(stream_type)

        find_handle = int(self.netsdk.NET_DVR_FindFile_V40(
            self.device.user_id, byref(cond)
        ))
        if find_handle < 0:
            code = int(self.netsdk.NET_DVR_GetLastError())
            raise HikvisionError(code, api="NET_DVR_FindFile_V40")

        results: List[RecordFile] = []
        try:
            while len(results) < max_files:
                fd = _NET_DVR_FINDDATA_V30()
                rc = int(self.netsdk.NET_DVR_FindNextFile_V30(find_handle, byref(fd)))
                if rc == NET_DVR_ISFINDING:
                    time.sleep(0.05)
                    continue
                if rc == NET_DVR_FILE_SUCCESS:
                    name = bytes(fd.sFileName).split(b"\x00", 1)[0].decode("utf-8", errors="replace")
                    results.append(RecordFile(
                        name=name,
                        start=_from_struct_time(fd.struStartTime),
                        stop=_from_struct_time(fd.struStopTime),
                        size_bytes=int(fd.dwFileSize),
                        locked=bool(fd.byLocked),
                        file_type=int(fd.byFileType),
                    ))
                    continue
                if rc in (NET_DVR_NOMOREFILE, NET_DVR_FILE_NOFIND, NET_DVR_FILE_EXCEPTION):
                    break
                # 其他未知码：跳出
                break
        finally:
            try:
                self.netsdk.NET_DVR_FindClose_V30(find_handle)
            except Exception:  # pragma: no cover
                pass
        return results

    # ------------------------------------------------------------------ #
    # 按时间段下载录像
    # ------------------------------------------------------------------ #

    def download_by_time(
        self,
        channel: int,
        start: datetime,
        stop: datetime,
        save_path: str,
        stream_type: int = 0,
        progress_callback=None,
        poll_interval: float = 0.5,
    ) -> str:
        """按时间段把录像下载到本地。

        Args:
            channel: 通道号（1 起）。
            start, stop: 时间段。
            save_path: 本地保存路径（建议 ``.mp4``）。
            stream_type: 0=主码流 1=子码流。
            progress_callback: 可选 ``callback(percent: int)``。
            poll_interval: 进度轮询间隔（秒）。

        Returns:
            下载文件的绝对路径。
        """
        save_path = os.path.abspath(save_path)
        os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)

        cond = _NET_DVR_PLAYCOND()
        start_chan = int(getattr(self.device.info, "start_channel", 1) or 1)
        cond.dwChannel = start_chan + (int(channel) - 1)
        cond.struStartTime = _to_struct_time(start)
        cond.struStopTime = _to_struct_time(stop)
        cond.byStreamType = int(stream_type)

        handle = int(self.netsdk.NET_DVR_GetFileByTime_V40(
            self.device.user_id, save_path.encode("utf-8"), byref(cond)
        ))
        if handle < 0:
            code = int(self.netsdk.NET_DVR_GetLastError())
            raise HikvisionError(code, api="NET_DVR_GetFileByTime_V40")

        # 启动下载
        if not self.netsdk.NET_DVR_PlayBackControl_V40(
            handle, 1, 0, 0, 0, 0  # 1 = NET_DVR_PLAYSTART
        ):
            code = int(self.netsdk.NET_DVR_GetLastError())
            try:
                self.netsdk.NET_DVR_StopGetFile(handle)
            except Exception:
                pass
            raise HikvisionError(code, api="NET_DVR_PlayBackControl_V40(START)")

        try:
            while True:
                pos = int(self.netsdk.NET_DVR_GetDownloadPos(handle))
                if pos == 100 or pos == 200:        # 完成
                    break
                if pos == -1 or pos > 200:           # 失败
                    code = int(self.netsdk.NET_DVR_GetLastError())
                    raise HikvisionError(code, api="NET_DVR_GetDownloadPos")
                if progress_callback:
                    progress_callback(min(int(pos), 100))
                time.sleep(poll_interval)
        finally:
            try:
                self.netsdk.NET_DVR_StopGetFile(handle)
            except Exception:  # pragma: no cover
                pass
        if progress_callback:
            progress_callback(100)
        _logger.info("下载完成: %s", save_path)
        return save_path


__all__ = ["PlayBack", "RecordFile"]
