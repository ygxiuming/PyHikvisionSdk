# -*- coding: utf-8 -*-
"""Demo 03：登录设备 + 打印基本信息。

用法::

    python demo/03_login_and_info.py --ip 192.168.1.64 --user admin --pwd 12345
"""

from __future__ import annotations

import argparse
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from hikvision_sdk import HikvisionSDK, Device  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--ip", required=True)
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--user", required=True)
    p.add_argument("--pwd", required=True)
    args = p.parse_args()

    with HikvisionSDK() as sdk:
        print(f"SDK 版本: {sdk.get_version_string()}")
        with Device(args.ip, args.user, args.pwd, port=args.port) as dev:
            info = dev.info
            print("====== 设备信息 ======")
            print(f"  序列号       : {info.serial_number}")
            print(f"  user_id      : {info.user_id}")
            print(f"  设备类型代号 : {info.device_type}")
            print(f"  模拟通道数   : {info.channel_num}")
            print(f"  IP 通道数    : {info.ip_channel_num}")
            print(f"  起始通道     : {info.start_channel}")
            print(f"  IP 起始通道  : {info.start_ip_channel}")
            print(f"  音频通道数   : {info.audio_channel_num}")
            print(f"  零通道数     : {info.zero_channel_num}")
            print(f"  报警输入数   : {info.alarm_in_num}")
            print(f"  报警输出数   : {info.alarm_out_num}")
            print(f"  硬盘数       : {info.disk_num}")


if __name__ == "__main__":
    main()
