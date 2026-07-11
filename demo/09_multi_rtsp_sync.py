# -*- coding: utf-8 -*-
"""★ Demo 09：多路海康 RTSP 接入 + 流内时间戳对帧 + cv 拼接播放（最低时延版）

本脚本在一个进程内同时接入 **多路** 海康威视 RTSP 流（路数可自由设置，默认 8 路），
核心是 :func:`MultiRTSPSync.align_frames` —— 通过对比每一路每一帧的 **流内绝对
时间戳**（由海康 SDK ``PlayM4_GetSystemTime`` 从 ``NET_DVR_PRIVATE_DATA`` 私有头
解析出的设备端真实时间），挑出"同一时刻"的一组帧组成 ``list`` 返回（即**对帧**）；
服务 demo 再用 OpenCV 把这组帧拼成网格画面实时播放。

----------------  ------------------------------------------------------------
阶段             说明
----------------  ------------------------------------------------------------
1. 接入多路       一台 NVR 登录一次，N 路通道走 ``NET_DVR_RealPlay_V40`` 私有协议
                  （延迟最低 ~150-250ms），每路一个 PlayM4 端口独立解码。
2. 流内时间戳     解码回调里立即调 ``PlayM4_GetSystemTime`` 拿当前帧的设备端绝对
                  时间（年/月/日/时/分/秒/毫秒），**不是本机墙钟**。多路同源 NVR
                  共用同一设备时钟，天然可对齐。
3. 对帧(核心)     ``T = min(各路最新流内时间戳)``（最慢路的最新帧时刻，保证每路
                  都有 ≤T 的帧）；每路最近邻查找；组内最大偏差 ≤ ``TOLERANCE_MS``
                  才返回，否则等慢路追上重试，**总等待不超过 2 帧（80ms@25fps）**。
4. cv 拼接播放    ``stitch_frames`` 把对齐后的 list 按网格 letterbox 拼成大图，
                  叠加通道标签 / 参考时刻 / 最大偏差，``cv2.imshow`` 播放，按 ``q`` 退出。
----------------  ------------------------------------------------------------

★ 时延控制（25fps，1 帧 = 40ms，2 帧 = 80ms）：
  - ``TOLERANCE_MS   = 80``   组内最大偏差 ≤ 2 帧
  - ``ALIGN_TIMEOUT_MS = 80`` 单次对齐等待 ≤ 2 帧（超时丢弃该组，不堆积延迟）
  - ``BUFFER_FRAMES  = 6``    每路仅保留 ~240ms 历史（够最近邻查找，不积压）
  - PlayM4 ``display_buf = 1``（最低解码延迟）
  - 对齐轮询间隔 2ms（及时捕捉新帧）

★ 直接编辑下方【配置区】即可运行，无需命令行参数。
"""

from __future__ import annotations

import math
import os
import sys
import threading
import time
from collections import deque
from datetime import datetime
from typing import List, Optional, Sequence, Tuple

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from hikvision_sdk import (  # noqa: E402
    HikvisionSDK, Device, RTSPLowLatencyStream, FrameTimestamp,
)
from hikvision_sdk.utils import color_convert  # noqa: E402
from hikvision_sdk.utils.time_utils import datetime_to_epoch_ms  # noqa: E402


# ===================================================================== #
# ============== 配置区（直接编辑这里，无需命令行参数） ==============
# ===================================================================== #

# —— 拉流模式 ——
# "nvr"  = 同一台 NVR/设备多通道（只需填一次 IP/账号/密码，自动生成 N 路，走 SDK 私有协议）
# "urls" = 自定义任意 RTSP 地址列表（走 opencv 后端，注意：opencv 拿不到流内时间戳，
#          会退化为本机墙钟，对齐精度受限——仅作跨厂商兜底）
MODE = "nvr"

# —— 模式 nvr：NVR/设备信息（SDK 登录，走私有协议拿流内时间戳）——
NVR_IP = "192.168.1.64"
NVR_PORT = 8000              # SDK 登录端口（注意是 8000，不是 RTSP 554）
NVR_USER = "admin"
NVR_PWD = "yourpassword"
CHANNELS = 8                 # 路数（默认 8 路）
STREAM_TYPE = 0              # 0=主码流 1=子码流（子码流延迟更低、带宽更省）

# —— 模式 urls：自定义 RTSP 地址列表（路数 = 列表长度）——
# 仅当你需要混合多台不同设备时才用此模式；此时无法拿到流内时间戳。
# RTSP_URLS = [
#     "rtsp://admin:pwd@192.168.1.64:554/Streaming/Channels/101",
#     "rtsp://admin:pwd@192.168.1.64:554/Streaming/Channels/201",
#     "rtsp://admin:pwd@192.168.1.64:554/Streaming/Channels/301",
#     "rtsp://admin:pwd@192.168.1.64:554/Streaming/Channels/401",
#     "rtsp://admin:pwd@192.168.1.65:554/Streaming/Channels/101",
#     "rtsp://admin:pwd@192.168.1.66:554/Streaming/Channels/101",
#     "rtsp://admin:pwd@192.168.1.67:554/Streaming/Channels/101",
#     "rtsp://admin:pwd@192.168.1.68:554/Streaming/Channels/101",
# ]
RTSP_URLS: List[str] = []

# —— 对帧参数（时延敏感，按 25fps 两帧 = 80ms 设定）——
TOLERANCE_MS = 80.0          # 组内最大时间偏差（毫秒）≤ 2 帧
ALIGN_TIMEOUT_MS = 80.0      # 单次对齐最长等待（毫秒）≤ 2 帧（超时丢弃该组）
BUFFER_FRAMES = 6            # 每路环形缓冲保留帧数（~240ms 历史，够最近邻查找）
MIN_ADVANCE_MS = 1.0         # 相邻两组参考时刻最小间隔，避免慢路没出新帧时重复返回

# —— 播放参数 ——
TILE_W = 480                 # 单格宽
TILE_H = 270                 # 单格高
GRID: Optional[Tuple[int, int]] = (4, 2)   # (cols, rows)；None = 自动近方形
TARGET_FPS = 25.0            # 播放目标帧率
NO_DISPLAY = False           # True = 不弹窗，仅打印对帧统计
RUN_SECONDS = 0.0            # >0 = 运行指定秒数后退出；0 = 直到按 q

# ===================================================================== #
# ========================== 配置区结束 ========================== #
# ===================================================================== #


# ===================================================================== #
# 1. 单路 SDK 流（流内时间戳版）：继承 RTSPLowLatencyStream，override 解码回调
# ===================================================================== #
class _SDKStreamWithStreamTime(RTSPLowLatencyStream):
    """SDK 后端拉流，但解码回调里调 ``PlayM4_GetSystemTime`` 拿流内绝对时间戳。

    与父类 ``RTSPLowLatencyStream`` 的唯一区别：父类用 ``datetime.now()`` 打戳
    （本机墙钟），本类用 ``PlayM4_GetSystemTime`` 从海康私有头
    ``NET_DVR_PRIVATE_DATA`` 解析**设备端真实绝对时间**——这才是多路对齐的正确
    时间基准（多路同源 NVR 共用同一设备时钟）。

    额外维护一个小环形缓冲（``BUFFER_FRAMES`` 帧），供对帧做最近邻查找；
    父类的单槽 ``_slot`` 不再使用。
    """

    def __init__(self, device: Device, channel: int, stream_type: int,
                 buffer_frames: int, buffer_size: int = 1):
        super().__init__(
            url=None,
            device=device,
            channel=channel,
            stream_type=stream_type,
            backend="sdk",
            drop_old_frames=True,
            buffer_size=buffer_size,
        )
        self._history: "deque[Tuple[Tuple[bytes, int, int], FrameTimestamp]]" = deque(
            maxlen=max(2, int(buffer_frames))
        )
        self._hlock = threading.Lock()
        self._ts_ok = 0          # 成功拿到流内时间戳的次数
        self._ts_fallback = 0    # 退化为本机时间的次数

    # -- override：解码回调里拿流内时间戳，写入 _history 而非 _slot --
    def _on_decoded_frame_sdk(self, port, idx, buf, w, h, pts_ms, ftype):
        ts = self._stream_timestamp(idx, pts_ms)
        if w <= 0 or h <= 0 or not buf:
            return
        with self._hlock:
            self._history.append(((buf, w, h), ts))

    def _stream_timestamp(self, idx: int, pts_ms: int) -> FrameTimestamp:
        """调 PlayM4_GetSystemTime 拿流内绝对时间；失败则退化为本机时间。"""
        st = None
        if self._decoder is not None:
            try:
                st = self._decoder.get_system_time()
            except Exception:
                st = None
        if st is not None and int(st.dwYear) >= 1970:
            try:
                dt = datetime(
                    year=int(st.dwYear), month=int(st.dwMon), day=int(st.dwDay),
                    hour=int(st.dwHour), minute=int(st.dwMin), second=int(st.dwSec),
                    microsecond=int(st.dwMs) * 1000,
                )
                self._ts_ok += 1
                return FrameTimestamp(
                    frame_index=idx, datetime=dt,
                    epoch_ms=datetime_to_epoch_ms(dt),
                    frame_type="?", pts_ms=int(pts_ms),
                )
            except ValueError:
                pass
        # 兜底：流内时间不可用时用本机墙钟（仅跨厂商 opencv 模式会走到这里）
        now = datetime.now()
        self._ts_fallback += 1
        return FrameTimestamp(
            frame_index=idx, datetime=now,
            epoch_ms=datetime_to_epoch_ms(now),
            frame_type="?", pts_ms=int(pts_ms),
        )

    # -- 供对帧使用：快照历史缓冲 --
    def snapshot(self) -> List[Tuple[Tuple[bytes, int, int], FrameTimestamp]]:
        with self._hlock:
            return list(self._history)

    def latest_ts(self) -> Optional[FrameTimestamp]:
        with self._hlock:
            return self._history[-1][1] if self._history else None


# ===================================================================== #
# 2. 单路 opencv 流（urls 模式兜底，本机墙钟时间戳）
# ===================================================================== #
class _OpenCVStreamWrapper:
    """opencv 后端的薄包装：把 RTSPLowLatencyStream 的单槽包成历史缓冲。

    仅用于 MODE="urls"。注意：opencv 后端拿不到流内时间戳，时间戳是本机墙钟，
    多路对齐精度受各路拉流延迟差影响。
    """

    def __init__(self, url: str, transport: str, buffer_frames: int):
        self._s = RTSPLowLatencyStream(
            url=url, device=None, backend="opencv",
            transport=transport, drop_old_frames=True, buffer_size=1,
        )
        self._history: "deque[Tuple[object, FrameTimestamp]]" = deque(
            maxlen=max(2, int(buffer_frames))
        )
        self._hlock = threading.Lock()
        self._grab: Optional[threading.Thread] = None
        self._stopped = threading.Event()

    def start(self) -> None:
        self._s.start()
        self._stopped.clear()
        self._grab = threading.Thread(target=self._loop, name="opencv-grab", daemon=True)
        self._grab.start()

    def stop(self) -> None:
        self._stopped.set()
        try:
            self._s.stop()
        except Exception:
            pass

    def _loop(self) -> None:
        while not self._stopped.is_set():
            try:
                frame, ts = self._s.read(timeout=1.0)
            except Exception:
                time.sleep(0.01)
                continue
            if frame is None or ts is None:
                continue
            with self._hlock:
                self._history.append((frame, ts))

    def snapshot(self) -> List[Tuple[object, FrameTimestamp]]:
        with self._hlock:
            return list(self._history)

    def latest_ts(self) -> Optional[FrameTimestamp]:
        with self._hlock:
            return self._history[-1][1] if self._history else None


# ===================================================================== #
# 3. 多路同步器：管理 N 路流 + 核心 align_frames() 对帧函数（严格 2 帧时延）
# ===================================================================== #
class MultiRTSPSync:
    """多路 RTSP 同步拉流 + 帧级时间对齐（流内时间戳）。

    每路维护一个小环形缓冲；``align_frames`` 取参考时刻 ``T = min(各路最新流内
    时间戳)``，每路最近邻查找，组内最大偏差 ≤ ``tolerance_ms`` 才返回，总等待
    ≤ ``timeout_ms``。
    """

    def __init__(self, streams: Sequence, names: Sequence[str]):
        self.streams: List = list(streams)
        self.n: int = len(self.streams)
        self.names: List[str] = list(names)

    def start(self) -> None:
        for i, s in enumerate(self.streams):
            s.start()
            print(f"  [接入] {self.names[i]}  ({i + 1}/{self.n})")

    def stop(self) -> None:
        for s in self.streams:
            try:
                s.stop()
            except Exception:
                pass

    def __enter__(self) -> "MultiRTSPSync":
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.stop()

    # ------------------------------------------------------------------ #
    # ★ 核心：对帧函数（流内时间戳，严格 2 帧时延）
    # ------------------------------------------------------------------ #
    def align_frames(
        self,
        tolerance_ms: float,
        timeout_ms: float,
        min_advance_ms: float = 0.0,
        last_ref_epoch_ms: Optional[int] = None,
    ) -> Tuple[Optional[List[Tuple[object, FrameTimestamp]]], Optional[int]]:
        """**对帧**：通过对比每一路每一帧的流内时间戳，挑出"同一时刻"的一组帧。

        算法
        ----
        1. 快照每路缓冲；任一路为空则等待（轮询 2ms，直到 timeout）。
        2. 参考时刻 ``T = min(各路最新帧 epoch_ms)``——"最慢一路"的最新时刻，
           保证每路缓冲里都存在 ``epoch_ms <= T`` 的帧，使"最接近 T 的帧"在
           每路都有定义；同时让对齐组尽可能贴近"现在"（最低时延）。
        3. 去重：要求 ``T - last_ref >= min_advance_ms``（慢路没出新帧时跳过）。
        4. 每路在其缓冲里做最近邻查找（``|epoch_ms - T|`` 最小），按路序组成 list。
        5. 校验整组最大偏差 ``max_dev <= tolerance_ms``：
             * 满足 → 返回 ``(list, T)``；
             * 不满足 → sleep 2ms 重试（慢路会持续出帧，T 推进，偏差收敛）；
             * 超过 ``timeout_ms`` → 返回 ``(None, None)``（丢弃该组，不堆积延迟）。

        Parameters
        ----------
        tolerance_ms:
            组内最大允许偏差（毫秒）。25fps 建议 80（2 帧）。
        timeout_ms:
            单次对齐最长等待（毫秒）。不超过 2 帧 = 80ms，保证不堆积延迟。
        min_advance_ms:
            相邻两组 T 的最小间隔，避免重复返回同一组。
        last_ref_epoch_ms:
            上一次返回的 T，配合 min_advance_ms 去重。

        Returns
        -------
        ``(aligned_list, T)``：``aligned_list[i] = (frame_i, FrameTimestamp_i)``；
        超时则 ``(None, None)``。其中 ``frame_i`` 对 SDK 模式是 ``(yv12_bytes, w, h)``，
        对 opencv 模式是 BGR ``ndarray``。
        """
        deadline = time.monotonic() + timeout_ms / 1000.0
        while True:
            snaps = [s.snapshot() for s in self.streams]
            # 1) 每路至少一帧
            if any(len(s) == 0 for s in snaps):
                if time.monotonic() >= deadline:
                    return None, None
                time.sleep(0.002)
                continue

            # 2) T = min(各路最新) —— 最慢路的最新帧时刻
            latest_epochs = [s[-1][1].epoch_ms for s in snaps]
            ref_t = min(latest_epochs)

            # 3) 去重
            if (last_ref_epoch_ms is not None
                    and ref_t - last_ref_epoch_ms < min_advance_ms):
                if time.monotonic() >= deadline:
                    return None, None
                time.sleep(0.002)
                continue

            # 4) 每路最近邻 → list
            aligned: List[Tuple[object, FrameTimestamp]] = []
            max_dev = 0
            for s in snaps:
                best_frame, best_ts = min(
                    s, key=lambda item: abs(item[1].epoch_ms - ref_t)
                )
                aligned.append((best_frame, best_ts))
                dev = abs(best_ts.epoch_ms - ref_t)
                if dev > max_dev:
                    max_dev = dev

            # 5) 偏差校验
            if max_dev <= tolerance_ms:
                return aligned, ref_t

            if time.monotonic() >= deadline:
                return None, None
            time.sleep(0.002)

    def per_channel_latest(self) -> List[Optional[FrameTimestamp]]:
        return [s.latest_ts() for s in self.streams]


# ===================================================================== #
# 4. cv 拼接：把对齐后的 list 拼成一幅网格大图
# ===================================================================== #
def _resize_letterbox(img, tw: int, th: int, border_value=(0, 0, 0)):
    """把任意分辨率帧等比缩放到 (tw, th) 内并补黑边，避免拉伸畸变。"""
    import cv2  # type: ignore
    import numpy as np  # type: ignore
    h, w = img.shape[:2]
    if w == 0 or h == 0:
        return np.full((th, tw, 3), border_value, dtype=img.dtype)
    scale = min(tw / w, th / h)
    nw = max(1, int(round(w * scale)))
    nh = max(1, int(round(h * scale)))
    resized = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_AREA)
    canvas = np.full((th, tw, 3), border_value, dtype=img.dtype)
    canvas[(th - nh) // 2:(th - nh) // 2 + nh,
           (tw - nw) // 2:(tw - nw) // 2 + nw] = resized
    return canvas


def stitch_frames(
    frames: Sequence,
    n: int,
    names: Sequence[str],
    grid: Optional[Tuple[int, int]] = None,
    tile_w: int = 480,
    tile_h: int = 270,
    gap: int = 4,
    border_value=(0, 0, 0),
):
    """把 ``frames`` 按网格拼成一幅大图（letterbox 保比例 + 通道标签）。"""
    import cv2  # type: ignore
    import numpy as np  # type: ignore

    if grid is None:
        cols = max(1, int(math.ceil(math.sqrt(n))))
        rows = max(1, int(math.ceil(n / cols)))
    else:
        cols, rows = int(grid[0]), int(grid[1])
    cols, rows = max(1, cols), max(1, rows)
    slots = cols * rows

    tiles = []
    for i in range(slots):
        if i < len(frames) and frames[i] is not None:
            tile = _resize_letterbox(frames[i], tile_w, tile_h, border_value)
            label = names[i] if i < len(names) else f"CH{i + 1}"
            cv2.putText(tile, label, (8, 22), cv2.FONT_HERSHEY_SIMPLEX,
                        0.6, (0, 255, 0), 2, cv2.LINE_AA)
        else:
            tile = np.full((tile_h, tile_w, 3), border_value, dtype=np.uint8)
            cv2.putText(tile, "N/A", (tile_w // 2 - 24, tile_h // 2 + 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (80, 80, 80), 2, cv2.LINE_AA)
        tiles.append(tile)

    gap_strip = np.full((tile_h, gap, 3), border_value, dtype=np.uint8)
    rows_img = []
    for r in range(rows):
        row_tiles = [tiles[r * cols + c] for c in range(cols)]
        row_img = row_tiles[0]
        for t in row_tiles[1:]:
            row_img = np.concatenate([row_img, gap_strip, t], axis=1)
        rows_img.append(row_img)
    gap_row = np.full((gap, rows_img[0].shape[1], 3), border_value, dtype=np.uint8)
    mosaic = rows_img[0]
    for ri in rows_img[1:]:
        mosaic = np.concatenate([mosaic, gap_row, ri], axis=0)
    return mosaic


# ===================================================================== #
# 5. 通道构建：从配置区变量生成 (stream, name) 列表
# ===================================================================== #
def build_channels(buffer_frames: int):
    """根据 MODE 构建流对象列表与名称列表。

    Returns
    -------
    ``(streams, names, need_sdk_ctx, device)``：
        ``need_sdk_ctx`` 表示是否需要在 ``HikvisionSDK()`` 上下文里运行；
        ``device`` 为已登录的 Device（nvr 模式），停止时由调用方 logout。
    """
    if MODE == "nvr":
        # SDK 后端：一台 NVR 登录一次，N 路通道
        dev = Device(NVR_IP, NVR_USER, NVR_PWD, port=NVR_PORT)
        dev.login()
        names = [f"CH{i + 1}" for i in range(CHANNELS)]
        streams = [
            _SDKStreamWithStreamTime(
                device=dev, channel=i + 1,
                stream_type=STREAM_TYPE, buffer_frames=buffer_frames,
            )
            for i in range(CHANNELS)
        ]
        return streams, names, True, dev

    # urls 模式（opencv 兜底）
    if not RTSP_URLS:
        raise ValueError("MODE='urls' 但 RTSP_URLS 为空，请填入地址或改 MODE='nvr'")
    names = [f"URL{i + 1}" for i in range(len(RTSP_URLS))]
    streams = [
        _OpenCVStreamWrapper(url=u, transport="tcp", buffer_frames=buffer_frames)
        for u in RTSP_URLS
    ]
    return streams, names, False, None


# ===================================================================== #
# 6. main：服务 demo —— 对帧 → cv 拼接 → 播放
# ===================================================================== #
def main() -> None:
    # 1) opencv 依赖（拼接播放用）
    cv2 = None
    if not NO_DISPLAY:
        try:
            import cv2  # type: ignore
        except ImportError:
            print("[警告] 未安装 opencv-python，自动启用 NO_DISPLAY")
    if cv2 is None and not NO_DISPLAY:
        print("[警告] 无 cv2，仅打印对帧统计")

    # 2) 构建通道
    streams, names, need_sdk, device = build_channels(BUFFER_FRAMES)
    n = len(streams)
    print(f"[多路 RTSP] 共 {n} 路  MODE={MODE}")
    print(f"[对帧参数] tolerance={TOLERANCE_MS}ms  timeout={ALIGN_TIMEOUT_MS}ms  "
          f"buffer={BUFFER_FRAMES}帧  (25fps 2帧=80ms)")

    # 3) 启动（nvr 模式需在 HikvisionSDK() 上下文里）
    def _run():
        sync = MultiRTSPSync(streams, names)
        sync.start()
        last_ref: Optional[int] = None
        t0 = time.time()
        last_log = t0
        shown = 0
        print("[对帧播放] 等待各路首帧 ...")
        try:
            while True:
                # —— ★ 核心：对帧（流内时间戳，2 帧时延约束）——
                aligned, ref_t = sync.align_frames(
                    tolerance_ms=TOLERANCE_MS,
                    timeout_ms=ALIGN_TIMEOUT_MS,
                    min_advance_ms=MIN_ADVANCE_MS,
                    last_ref_epoch_ms=last_ref,
                )

                if RUN_SECONDS and time.time() - t0 >= RUN_SECONDS:
                    break

                if aligned is None or ref_t is None:
                    # 对齐超时（某路掉队 >2 帧），跳过这组，不堆积延迟
                    continue

                last_ref = ref_t
                shown += 1

                # 统计
                devs = [abs(ft.epoch_ms - ref_t) for _, ft in aligned]
                max_dev = max(devs) if devs else 0
                now = time.time()
                if now - last_log >= 1.0:
                    fps = shown / (now - last_log)
                    ref_dt = datetime.fromtimestamp(ref_t / 1000.0).strftime(
                        "%H:%M:%S.") + f"{(ref_t % 1000):03d}"
                    # 流内时间戳命中率（仅 SDK 模式有意义）
                    hit = ""
                    if MODE == "nvr":
                        ok = sum(getattr(s, "_ts_ok", 0) for s in streams)
                        fb = sum(getattr(s, "_ts_fallback", 0) for s in streams)
                        tot = ok + fb
                        hit = f"  流内时间戳={ok}/{tot}" if tot else ""
                    print(f"  [统计] fps={fps:.1f}  REF={ref_dt}  "
                          f"max_dev={max_dev}ms{hit}")
                    shown = 0
                    last_log = now

                if cv2 is not None:
                    # SDK 模式：aligned[i] 的 frame 是 (yv12_bytes, w, h)，需转 BGR
                    # opencv 模式：frame 已是 BGR ndarray
                    frames_bgr = []
                    for fr, _ts in aligned:
                        if isinstance(fr, tuple):
                            buf, w, h = fr
                            if color_convert.has_cv2():
                                try:
                                    bgr = color_convert.yv12_buffer_to_bgr(buf, w, h)
                                except Exception:
                                    bgr = None
                            else:
                                bgr = None
                            frames_bgr.append(bgr)
                        else:
                            frames_bgr.append(fr)

                    mosaic = stitch_frames(
                        frames_bgr, n, names,
                        grid=GRID, tile_w=TILE_W, tile_h=TILE_H,
                    )
                    ref_dt = datetime.fromtimestamp(ref_t / 1000.0).strftime(
                        "%Y-%m-%d %H:%M:%S.") + f"{(ref_t % 1000):03d}"
                    import cv2 as _cv2  # type: ignore
                    _cv2.putText(mosaic,
                                 f"REF {ref_dt}  dev={max_dev}ms  N={n}",
                                 (10, 22), _cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                                 (0, 255, 255), 2, _cv2.LINE_AA)
                    _cv2.imshow("Multi-RTSP Sync (press q to quit)", mosaic)
                    wait_ms = max(1, int(1000 / max(1.0, TARGET_FPS)))
                    if _cv2.waitKey(wait_ms) & 0xFF == ord("q"):
                        break
        except KeyboardInterrupt:
            print("\n[中断] Ctrl-C，退出 ...")
        finally:
            sync.stop()
            if cv2 is not None:
                try:
                    import cv2 as _cv2  # type: ignore
                    _cv2.destroyAllWindows()
                except Exception:
                    pass
            print("[完成] 已停止全部拉流")

    try:
        if need_sdk:
            with HikvisionSDK():
                _run()
        else:
            _run()
    finally:
        if device is not None:
            try:
                device.logout()
            except Exception:
                pass


if __name__ == "__main__":
    main()
