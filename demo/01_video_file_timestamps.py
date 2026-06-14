# -*- coding: utf-8 -*-
"""★ Demo 01：读取海康私有流视频文件 + 逐帧绝对时间戳

用法::

    python demo/01_video_file_timestamps.py "D:/records/ch01.mp4"
    python demo/01_video_file_timestamps.py "D:/records/ch01.mp4" --max-frames 200

输出：先打印视频信息，再逐帧打印
``#帧序号  绝对时间(YYYY-MM-DD HH:MM:SS.mmm)  epoch_ms=...  type=I/P/?  pts=...ms``
"""

from __future__ import annotations

import argparse
import os
import sys

# 把项目根加进 sys.path，便于直接 `python demo/xxx.py` 运行
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from hikvision_sdk import HikvisionSDK, VideoFileReader  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="读取海康视频文件并逐帧输出绝对时间戳")
    parser.add_argument("video_path", help="本地视频文件路径（海康私有流，含 PRIVATE_DATA 头最佳）")
    parser.add_argument("--max-frames", type=int, default=0,
                        help="最多输出多少帧（0=不限制）")
    parser.add_argument("--save-frames", default="",
                        help="若指定目录，则把解码后的 BGR 帧保存为 .jpg")
    args = parser.parse_args()

    if args.save_frames:
        os.makedirs(args.save_frames, exist_ok=True)

    with HikvisionSDK():
        reader = VideoFileReader(args.video_path)

        # ---- 第一步：先打印视频元信息 ----
        info = reader.get_info()
        print(info)
        print("")
        print("[逐帧绝对时间戳]")

        # ---- 第二步：逐帧迭代 ----
        if args.save_frames:
            try:
                import cv2  # type: ignore
            except ImportError:
                print("[警告] 未安装 opencv-python，无法保存帧图片，仅输出时间戳。")
                cv2 = None

            for ft, image in reader.iter_frames(decode_image=True, color="BGR"):
                print(" ", ft)
                if cv2 is not None and image is not None:
                    out_path = os.path.join(
                        args.save_frames, f"frame_{ft.frame_index:06d}.jpg"
                    )
                    cv2.imwrite(out_path, image)
                if args.max_frames and ft.frame_index + 1 >= args.max_frames:
                    break
        else:
            for ft in reader.iter_frame_timestamps():
                print(" ", ft)
                if args.max_frames and ft.frame_index + 1 >= args.max_frames:
                    break

    print("\n[完成]")


if __name__ == "__main__":
    main()
