# -*- coding: utf-8 -*-
"""Demo 07：按时间段查询并下载录像。

用法::

    python demo/07_playback_download.py --ip 192.168.1.64 --user admin --pwd 12345 \
        --channel 1 --start "2024-06-01 08:00:00" --end "2024-06-01 08:05:00" \
        --output ch01_20240601_080000.mp4
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from hikvision_sdk import HikvisionSDK, Device, PlayBack  # noqa: E402


def parse_dt(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--ip", required=True)
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--user", required=True)
    p.add_argument("--pwd", required=True)
    p.add_argument("--channel", type=int, default=1)
    p.add_argument("--start", required=True, help='"YYYY-MM-DD HH:MM:SS"')
    p.add_argument("--end", required=True, help='"YYYY-MM-DD HH:MM:SS"')
    p.add_argument("--output", required=True)
    p.add_argument("--list-only", action="store_true",
                   help="只查询，不下载")
    args = p.parse_args()

    start = parse_dt(args.start)
    end = parse_dt(args.end)

    with HikvisionSDK():
        with Device(args.ip, args.user, args.pwd, port=args.port) as dev:
            pb = PlayBack(dev)
            files = pb.find_files(args.channel, start, end)
            print(f"查询到 {len(files)} 个录像文件:")
            for f in files:
                print(" ", f)
            if args.list_only:
                return

            def on_progress(pct: int) -> None:
                print(f"  下载进度: {pct}%")

            path = pb.download_by_time(
                channel=args.channel,
                start=start, stop=end,
                save_path=args.output,
                progress_callback=on_progress,
            )
            print(f"录像已保存到: {path}")


if __name__ == "__main__":
    main()
