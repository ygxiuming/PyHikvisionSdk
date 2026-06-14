# -*- coding: utf-8 -*-
"""云台 (PTZ) 控制封装。

调用 ``NET_DVR_PTZControlWithSpeed_Other``，常用命令码（来自 HCNetSDK.h）：

================  ====  ================================================
命令              代号   含义
================  ====  ================================================
TILT_UP           21    向上
TILT_DOWN         22    向下
PAN_LEFT          23    向左
PAN_RIGHT         24    向右
UP_LEFT           25    左上
UP_RIGHT          26    右上
DOWN_LEFT         27    左下
DOWN_RIGHT        28    右下
ZOOM_IN           11    变倍+
ZOOM_OUT          12    变倍-
FOCUS_NEAR        13    聚焦近
FOCUS_FAR         14    聚焦远
IRIS_OPEN         15    光圈+
IRIS_CLOSE        16    光圈-
================  ====  ================================================

预置点：``NET_DVR_PTZPreset_Other(user_id, channel, cmd, preset_index)``，
cmd: 8=GOTO_PRESET 39=SET_PRESET 40=CLE_PRESET。
"""

from __future__ import annotations

import time
from typing import Optional

from hikvision_sdk.exceptions import HikvisionError
from hikvision_sdk.utils.logging import get_logger

_logger = get_logger("hikvision_sdk.ptz")


# 命令常量
TILT_UP = 21
TILT_DOWN = 22
PAN_LEFT = 23
PAN_RIGHT = 24
UP_LEFT = 25
UP_RIGHT = 26
DOWN_LEFT = 27
DOWN_RIGHT = 28
ZOOM_IN = 11
ZOOM_OUT = 12
FOCUS_NEAR = 13
FOCUS_FAR = 14
IRIS_OPEN = 15
IRIS_CLOSE = 16

# 预置点命令
PRESET_GOTO = 39
PRESET_SET = 8
PRESET_CLE = 9


class PTZController:
    """云台控制。"""

    def __init__(self, device, channel: int = 1):
        self.device = device
        self.netsdk = device.netsdk
        self.channel = int(channel)

    # 通道号转换：用户的 1 表示首通道
    @property
    def _real_channel(self) -> int:
        start = int(getattr(self.device.info, "start_channel", 1) or 1)
        return start + self.channel - 1

    def _ctrl(self, cmd: int, stop: int, speed: int) -> None:
        ok = self.netsdk.NET_DVR_PTZControlWithSpeed_Other(
            self.device.user_id, self._real_channel,
            int(cmd), int(stop), int(speed)
        )
        if not ok:
            code = int(self.netsdk.NET_DVR_GetLastError())
            raise HikvisionError(code, api="NET_DVR_PTZControlWithSpeed_Other")

    def move(self, direction: int, speed: int = 4, duration: float = 0.5) -> None:
        """按方向运动指定时长后停止。

        Args:
            direction: 命令常量（TILT_UP / PAN_LEFT 等）。
            speed: 1~7，速度。
            duration: 持续秒数。<0 表示不自动停止（需手动调用 stop）。
        """
        self._ctrl(direction, 0, speed)
        if duration > 0:
            time.sleep(duration)
            self.stop(direction, speed)

    def stop(self, direction: int, speed: int = 4) -> None:
        """停止某方向运动。"""
        self._ctrl(direction, 1, speed)

    # ------------------------------------------------------------------ #
    # 便捷方向方法
    # ------------------------------------------------------------------ #

    def up(self, speed=4, duration=0.5):     self.move(TILT_UP, speed, duration)
    def down(self, speed=4, duration=0.5):   self.move(TILT_DOWN, speed, duration)
    def left(self, speed=4, duration=0.5):   self.move(PAN_LEFT, speed, duration)
    def right(self, speed=4, duration=0.5):  self.move(PAN_RIGHT, speed, duration)

    def zoom_in(self, speed=4, duration=0.5):  self.move(ZOOM_IN, speed, duration)
    def zoom_out(self, speed=4, duration=0.5): self.move(ZOOM_OUT, speed, duration)

    def focus_near(self, speed=4, duration=0.5): self.move(FOCUS_NEAR, speed, duration)
    def focus_far(self, speed=4, duration=0.5):  self.move(FOCUS_FAR, speed, duration)

    # ------------------------------------------------------------------ #
    # 预置点
    # ------------------------------------------------------------------ #

    def goto_preset(self, preset_index: int) -> None:
        ok = self.netsdk.NET_DVR_PTZPreset_Other(
            self.device.user_id, self._real_channel, PRESET_GOTO, int(preset_index)
        )
        if not ok:
            code = int(self.netsdk.NET_DVR_GetLastError())
            raise HikvisionError(code, api="NET_DVR_PTZPreset_Other(GOTO)")

    def set_preset(self, preset_index: int) -> None:
        ok = self.netsdk.NET_DVR_PTZPreset_Other(
            self.device.user_id, self._real_channel, PRESET_SET, int(preset_index)
        )
        if not ok:
            code = int(self.netsdk.NET_DVR_GetLastError())
            raise HikvisionError(code, api="NET_DVR_PTZPreset_Other(SET)")

    def clear_preset(self, preset_index: int) -> None:
        ok = self.netsdk.NET_DVR_PTZPreset_Other(
            self.device.user_id, self._real_channel, PRESET_CLE, int(preset_index)
        )
        if not ok:
            code = int(self.netsdk.NET_DVR_GetLastError())
            raise HikvisionError(code, api="NET_DVR_PTZPreset_Other(CLE)")


__all__ = ["PTZController",
           "TILT_UP", "TILT_DOWN", "PAN_LEFT", "PAN_RIGHT",
           "UP_LEFT", "UP_RIGHT", "DOWN_LEFT", "DOWN_RIGHT",
           "ZOOM_IN", "ZOOM_OUT", "FOCUS_NEAR", "FOCUS_FAR",
           "IRIS_OPEN", "IRIS_CLOSE"]
