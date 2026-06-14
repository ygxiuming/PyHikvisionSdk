# -*- coding: utf-8 -*-
"""Demo 06：JPEG 抓图。

用法::

    python demo/06_snapshot.py --ip 192.168.1.64 --user admin --pwd 12345 \
        --output snapshot.jpg
"""

from __future__ import annotations

import argparse
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from hikvision_sdk import HikvisionSDK, Device  # noqa: E402
from hikvision_sdk import snapshot as snap  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--ip", required=True)
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--user", required=True)
    p.add_argument("--pwd", required=True)
    p.add_argument("--channel", type=int, default=1)
    p.add_argument("--output", default="snapshot.jpg")
    p.add_argument("--bytes", action="store_true",
                   help="走 NEW 接口直接返回字节流，不落盘")
    args = p.parse_args()

    with HikvisionSDK():
        with Device(args.ip, args.user, args.pwd, port=args.port) as dev:
            if args.bytes:
                data = snap.capture_jpeg(dev, channel=args.channel)
                print(f"抓图成功，jpeg 字节数 = {len(data)}")
                with open(args.output, "wb") as f:
                    f.write(data)
                print(f"已写入 {args.output}")
            else:
                path = snap.capture_jpeg_to_file(
                    dev, channel=args.channel, save_path=args.output
                )
                print(f"抓图保存到 {path}")


if __name__ == "__main__":
    main()
