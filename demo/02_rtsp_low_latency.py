# -*- coding: utf-8 -*-
"""★ Demo 02：低延迟 RTSP 拉流（双后端可切换）

用法（SDK 后端，最低延迟）::

    python demo/02_rtsp_low_latency.py \
        --backend sdk --ip 192.168.1.64 --user admin --pwd 12345

用法（OpenCV/FFmpeg 后端，标准 RTSP）::

    python demo/02_rtsp_low_latency.py \
        --backend opencv \
        --url rtsp://admin:12345@192.168.1.64:554/Streaming/Channels/101

按 ``q`` 键退出。
"""

from __future__ import annotations

import argparse
import os
import sys
import time

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from hikvision_sdk import HikvisionSDK, Device, RTSPLowLatencyStream  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="低延迟 RTSP 拉流 demo")
    parser.add_argument("--backend", choices=["sdk", "opencv", "auto"], default="auto",
                        help="拉流后端")
    parser.add_argument("--url", default="",
                        help="RTSP URL（OpenCV 后端使用）")
    parser.add_argument("--ip", default="192.168.1.64", help="设备 IP（SDK 后端）")
    parser.add_argument("--port", type=int, default=8000, help="设备 SDK 端口")
    parser.add_argument("--user", default="admin", help="用户名（SDK 后端）")
    parser.add_argument("--pwd", default="12345", help="密码（SDK 后端）")
    parser.add_argument("--channel", type=int, default=1, help="通道号（1 起）")
    parser.add_argument("--stream-type", type=int, default=0,
                        help="0=主码流 1=子码流")
    parser.add_argument("--no-display", action="store_true",
                        help="不打开窗口预览，仅打印延迟统计")
    parser.add_argument("--seconds", type=float, default=0,
                        help="运行多少秒后自动退出（0=直到按 q）")
    args = parser.parse_args()

    try:
        import cv2  # type: ignore
    except ImportError:
        cv2 = None
        if not args.no_display:
            print("[警告] 未安装 opencv-python，自动启用 --no-display")
            args.no_display = True

    with HikvisionSDK() as _:
        # SDK 后端需要 Device 实例；OpenCV 后端不需要登录设备。
        if args.backend in ("sdk", "auto"):
            device = Device(args.ip, args.user, args.pwd, port=args.port)
            device.login()
        else:
            device = None

        try:
            stream = RTSPLowLatencyStream(
                url=args.url or None,
                device=device,
                channel=args.channel,
                stream_type=args.stream_type,
                backend=args.backend,
                drop_old_frames=True,
                buffer_size=1,
            )
            stream.start()
            print(f"[拉流启动] 实际后端 = {stream.backend_active}")

            t0 = time.time()
            count = 0
            last_log = t0
            while True:
                frame, ts = stream.read(timeout=2.0)
                if frame is None:
                    print("[超时] 未收到新帧")
                    if args.seconds and time.time() - t0 >= args.seconds:
                        break
                    continue

                count += 1
                # 每秒打印一次帧率/延迟
                now = time.time()
                if now - last_log >= 1.0:
                    fps = count / (now - last_log)
                    latency_ms = (now * 1000) - ts.epoch_ms
                    print(f"  [统计] 实测 fps={fps:.1f}  采样延迟≈{latency_ms:.0f} ms  "
                          f"frame#{ts.frame_index}  时间={ts.datetime_str}")
                    count = 0
                    last_log = now

                if not args.no_display and cv2 is not None:
                    # frame 是 BGR numpy
                    cv2.imshow("Hikvision RTSP Low Latency", frame)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break

                if args.seconds and time.time() - t0 >= args.seconds:
                    break

            stream.stop()
            print("[拉流停止]")
        finally:
            if cv2 is not None and not args.no_display:
                try:
                    cv2.destroyAllWindows()
                except Exception:
                    pass
            if device is not None:
                device.logout()


if __name__ == "__main__":
    main()
