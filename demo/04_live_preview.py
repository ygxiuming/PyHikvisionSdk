# -*- coding: utf-8 -*-
"""Demo 04：实时预览（原始码流回调，并保存前 N 字节到文件）。

与 demo 02 的区别：本 demo 直接拿 **原始 H.264/H.265 码流字节**（NET_DVR_RealPlay
回调），可用于：保存原始 ts/h264 流；自定义解码器；GB28181 转发等。

用法::

    python demo/04_live_preview.py --ip 192.168.1.64 --user admin --pwd 12345 \
        --save-raw out.h264 --duration 10
"""

from __future__ import annotations

import argparse
import os
import sys
import time

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from hikvision_sdk import HikvisionSDK, Device, LiveStream  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--ip", required=True)
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--user", required=True)
    p.add_argument("--pwd", required=True)
    p.add_argument("--channel", type=int, default=1)
    p.add_argument("--stream-type", type=int, default=0)
    p.add_argument("--save-raw", default="", help="保存原始码流到此文件")
    p.add_argument("--duration", type=float, default=10.0, help="持续秒数")
    args = p.parse_args()

    out_fp = open(args.save_raw, "wb") if args.save_raw else None
    sys_head_total = 0
    stream_data_total = 0

    def on_data(data_type: int, data: bytes) -> None:
        nonlocal sys_head_total, stream_data_total
        if data_type == 1:                # NET_DVR_SYSHEAD
            sys_head_total += len(data)
        elif data_type == 2:              # NET_DVR_STREAMDATA
            stream_data_total += len(data)
        if out_fp is not None:
            out_fp.write(data)

    with HikvisionSDK():
        with Device(args.ip, args.user, args.pwd, port=args.port) as dev:
            stream = LiveStream(dev, channel=args.channel, stream_type=args.stream_type)
            stream.set_data_callback(on_data)
            stream.start()
            try:
                t0 = time.time()
                while time.time() - t0 < args.duration:
                    time.sleep(1.0)
                    print(f"  [{time.time() - t0:.1f}s] sys_head={sys_head_total} B "
                          f"stream={stream_data_total} B")
            finally:
                stream.stop()
                if out_fp is not None:
                    out_fp.close()
                    print(f"已保存到 {args.save_raw}")


if __name__ == "__main__":
    main()
