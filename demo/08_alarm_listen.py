# -*- coding: utf-8 -*-
"""Demo 08：报警布防 + 事件监听。

用法::

    python demo/08_alarm_listen.py --ip 192.168.1.64 --user admin --pwd 12345 \
        --duration 60

运行后会持续监听 ``--duration`` 秒，把所有上报的报警事件以
``[事件] cmd=0xXXXX, info=NN bytes`` 的形式打印出来。
"""

from __future__ import annotations

import argparse
import os
import sys
import time

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from hikvision_sdk import HikvisionSDK, Device, AlarmListener  # noqa: E402


# 常见命令码 → 中文（来自 HCNetSDK.h），未列出的会用十六进制原样打印
_CMD_NAMES = {
    0x1100: "移动侦测",
    0x1101: "信号丢失",
    0x1102: "视频遮挡",
    0x1106: "硬盘满",
    0x1108: "硬盘故障",
    0x4000: "传感器报警",
    0x4001: "通用报警 V40",
    0x4006: "通道异常",
    0x70d:  "VCA 越界",
    0x710:  "区域入侵",
    0x711:  "进入区域",
    0x712:  "离开区域",
    0x90c:  "人脸抓拍",
}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--ip", required=True)
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--user", required=True)
    p.add_argument("--pwd", required=True)
    p.add_argument("--duration", type=float, default=60.0)
    args = p.parse_args()

    with HikvisionSDK():
        with Device(args.ip, args.user, args.pwd, port=args.port) as dev:
            alarm = AlarmListener(dev)

            def on_event(cmd: int, info_bytes: bytes, alarmer):
                name = _CMD_NAMES.get(cmd, "未知")
                print(f"[事件] cmd=0x{cmd:04x} ({name}) "
                      f"info_size={len(info_bytes)} B")

            alarm.on_event = on_event
            alarm.start()
            try:
                t0 = time.time()
                print(f"开始侦听 {args.duration:.0f} 秒...")
                while time.time() - t0 < args.duration:
                    time.sleep(1.0)
            finally:
                alarm.stop()
                print("已撤防")


if __name__ == "__main__":
    main()
