# -*- coding: utf-8 -*-
"""Demo 05：云台控制（PTZ）。

用法::

    python demo/05_ptz_control.py --ip 192.168.1.64 --user admin --pwd 12345 \
        --action up --duration 1.0 --speed 5
"""

from __future__ import annotations

import argparse
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from hikvision_sdk import HikvisionSDK, Device, PTZController  # noqa: E402


_ACTIONS = ["up", "down", "left", "right",
            "zoom_in", "zoom_out", "focus_near", "focus_far"]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--ip", required=True)
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--user", required=True)
    p.add_argument("--pwd", required=True)
    p.add_argument("--channel", type=int, default=1)
    p.add_argument("--action", choices=_ACTIONS + ["preset_goto", "preset_set"],
                   default="up")
    p.add_argument("--duration", type=float, default=0.8)
    p.add_argument("--speed", type=int, default=4)
    p.add_argument("--preset-index", type=int, default=1)
    args = p.parse_args()

    with HikvisionSDK():
        with Device(args.ip, args.user, args.pwd, port=args.port) as dev:
            ptz = PTZController(dev, channel=args.channel)
            if args.action in _ACTIONS:
                getattr(ptz, args.action)(speed=args.speed, duration=args.duration)
                print(f"动作 {args.action} 完成")
            elif args.action == "preset_goto":
                ptz.goto_preset(args.preset_index)
                print(f"调用预置点 {args.preset_index}")
            elif args.action == "preset_set":
                ptz.set_preset(args.preset_index)
                print(f"设置预置点 {args.preset_index}")


if __name__ == "__main__":
    main()
