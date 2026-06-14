<div align="center">

# 🎥 PyHikvisionSdk

### Pythonic wrapper for Hikvision HCNetSDK with frame-accurate timestamps & ultra-low-latency RTSP

**海康威视 HCNetSDK 的 Pythonic 封装 · 帧级绝对时间戳 · 超低延迟 RTSP 拉流**

[![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-0078D4)](https://github.com/ygxiuming/PyHikvisionSdk)
[![SDK](https://img.shields.io/badge/HCNetSDK-V6.1.9.48-FF6B35)](https://www.hikvision.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-22%2F22%20passing-brightgreen)](tests/test_integration.py)
[![Code Style](https://img.shields.io/badge/code%20style-PEP8-blueviolet)](https://peps.python.org/pep-0008/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

[English](#-english) · [简体中文](#-简体中文) · [📖 API Docs](#-api-reference--api-参考) · [🐛 Report Bug](https://github.com/ygxiuming/PyHikvisionSdk/issues) · [✨ Request Feature](https://github.com/ygxiuming/PyHikvisionSdk/issues)

---

**If this project saves you time, please consider giving it a ⭐ — it really helps!**

**如果这个项目帮到了你，请给一个 ⭐ Star 鼓励一下，万分感谢！**

</div>

---

## ✨ Highlights / 项目亮点

<table>
<tr>
<td width="50%">

### 🌟 Frame-Accurate Timestamps
Extract the **device-side absolute timestamp** for every frame in Hikvision-exported videos (containing `NET_DVR_PRIVATE_DATA` headers) — millisecond precision, perfect for forensics, ML labeling, and time-synced multi-camera fusion.

```python
for ts in reader.iter_frame_timestamps():
    print(ts.datetime_str, ts.epoch_ms)
# 2024-06-01 08:00:00.040  1717200000040
```

</td>
<td width="50%">

### 🌟 帧级绝对时间戳
对海康设备导出的私有流视频，逐帧提取**设备端真实绝对时间**（毫秒精度），适用于事件溯源、AI 数据集打标、多摄像头时间对齐等场景。

```python
for ts in reader.iter_frame_timestamps():
    print(ts.datetime_str, ts.epoch_ms)
# 2024-06-01 08:00:00.040  1717200000040
```

</td>
</tr>
<tr>
<td width="50%">

### ⚡ Ultra-Low-Latency RTSP
**Dual-backend** RTSP streaming: native Hikvision SDK protocol (~150 ms) for the lowest latency, with FFmpeg/OpenCV fallback for cross-vendor compatibility. Latest-frame-only buffering eliminates pipeline lag.

```python
stream = RTSPLowLatencyStream(device=dev, backend="sdk")
stream.start()
frame_bgr, ts = stream.read()  # always the freshest frame
```

</td>
<td width="50%">

### ⚡ 超低延迟 RTSP 拉流
**双后端**架构：海康私有协议（~150 ms 最低延迟）+ FFmpeg/OpenCV 兜底。单槽缓冲机制保证 `read()` 永远拿到最新帧，旧帧自动丢弃，告别累积延迟。

```python
stream = RTSPLowLatencyStream(device=dev, backend="sdk")
stream.start()
frame_bgr, ts = stream.read()  # 永远是最新帧
```

</td>
</tr>
</table>

### 🎁 More features / 更多特性

- 🚀 **Zero-config cross-platform** — auto-detects Windows/Linux, loads the right `.dll`/`.so` from `sdk/win` or `sdk/linux`
- 🎯 **Production-ready API** — singleton SDK lifecycle, context managers, ref-counted cleanup
- 🛡️ **100+ error codes** mapped to **human-readable Chinese messages**
- 🎨 **Full PTZ control** — pan/tilt/zoom/focus/preset points
- 📸 **JPEG snapshots** — to file or in-memory bytes
- 📼 **Playback & download** — query and pull recordings by time range
- 🚨 **Alarm subscription** — motion detection, line-crossing, intrusion, face capture, and more
- ⚙️ **Generic Get/Set Config** — covers any HCNetSDK config command
- 📚 **Detailed Chinese comments** — every module, class, and method documented
- ✅ **22 integration tests** — verifies dll loading, SDK init, ctypes structs, error paths

---

## 📑 Table of Contents

- [⚡ Quick Start / 快速开始](#-quick-start--快速开始)
- [📦 Installation / 安装](#-installation--安装)
- [🎬 Demos / 示例集](#-demos--示例集)
- [📖 API Reference / API 参考](#-api-reference--api-参考)
- [🏗️ Architecture / 架构](#️-architecture--架构)
- [🧪 Testing / 测试](#-testing--测试)
- [❓ FAQ](#-faq--常见问题)
- [🤝 Contributing / 贡献](#-contributing--贡献)
- [📜 License / 许可](#-license--许可)

---

<a name="-english"></a>
<a name="-quick-start--快速开始"></a>
## ⚡ Quick Start / 快速开始

### 🚀 30-second example — extract per-frame timestamps from a Hikvision-exported video

```python
from hikvision_sdk import HikvisionSDK, VideoFileReader

with HikvisionSDK():
    reader = VideoFileReader("ch01_20240601_080000.mp4")

    # 1. Print video metadata
    print(reader.get_info())

    # 2. Yield every frame's absolute timestamp
    for ts in reader.iter_frame_timestamps():
        print(ts)
```

**Output:**

```
[视频信息]
  文件: ch01_20240601_080000.mp4
  大小: 1247.83 MB
  总时长: 3600.00 s | 总帧数: 90000
  分辨率: 1920x1080 | 帧率: 25.00 fps
  起始绝对时间: 2024-06-01 08:00:00.000
  编码: H.264 / H.265 (Hikvision)

[逐帧绝对时间戳]
  #000000  2024-06-01 08:00:00.000  epoch_ms=1717200000000  type=I  pts=0ms
  #000001  2024-06-01 08:00:00.040  epoch_ms=1717200000040  type=?  pts=40ms
  #000002  2024-06-01 08:00:00.080  epoch_ms=1717200000080  type=?  pts=80ms
  ...
```

### ⚡ 30-second example — pull RTSP with the lowest possible latency

```python
from hikvision_sdk import HikvisionSDK, Device, RTSPLowLatencyStream

with HikvisionSDK():
    with Device("192.168.1.64", "admin", "yourpassword") as dev:
        with RTSPLowLatencyStream(device=dev, backend="sdk") as stream:
            while True:
                frame_bgr, ts = stream.read(timeout=1.0)
                if frame_bgr is not None:
                    # frame_bgr is a numpy ndarray (H, W, 3), ready for cv2 / model
                    cv2.imshow("Live", frame_bgr)
                    if cv2.waitKey(1) == ord('q'): break
```

---

## 📦 Installation / 安装

### Prerequisites / 系统要求

| | Windows | Linux |
|---|---|---|
| **Python** | 3.8+ (64-bit) | 3.8+ (64-bit) |
| **OS** | Windows 10/11 x64 | Ubuntu 18.04+, CentOS 7+ |
| **Extras** | [Visual C++ 2015–2022 Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe) | `libgomp1` (usually preinstalled) |

### Step 1 — Clone

```bash
git clone https://github.com/ygxiuming/PyHikvisionSdk.git
cd PyHikvisionSdk
```

### Step 2 — Install Python dependencies

```bash
pip install -r requirements.txt
```

This installs `numpy` and `opencv-python` (used for YUV → BGR conversion and the OpenCV RTSP backend).

### Step 3 — Verify the SDK loads

```bash
python -c "from hikvision_sdk import HikvisionSDK; \
  s = HikvisionSDK(); s.initialize(); \
  print('SDK', s.get_version_string()); s.cleanup()"
```

You should see **`SDK 6.1.9.48`**. If you see a `dll load failed` error on Windows, install the VC++ redistributable above.

> 💡 **No need to install Hikvision's own SDK.** All `.dll`/`.so` files are bundled inside `sdk/win` and `sdk/linux`. You can git-clone and go.

---

## 🎬 Demos / 示例集

All demos under [`demo/`](demo/) are **self-contained** and runnable via CLI. No extra setup needed beyond `pip install -r requirements.txt`.

| # | Script | Description / 功能 | Needs device? |
|---|---|---|:---:|
| **01** | [`01_video_file_timestamps.py`](demo/01_video_file_timestamps.py) | ⭐ **Per-frame absolute timestamps** from a Hikvision-exported video / 视频文件逐帧绝对时间戳 | ❌ |
| **02** | [`02_rtsp_low_latency.py`](demo/02_rtsp_low_latency.py) | ⭐ **Low-latency RTSP** with SDK / OpenCV / auto backend / 低延迟 RTSP 拉流 | ✅ |
| 03 | [`03_login_and_info.py`](demo/03_login_and_info.py) | Login & print device info / 登录设备并打印信息 | ✅ |
| 04 | [`04_live_preview.py`](demo/04_live_preview.py) | Live preview, save raw H.264/H.265 stream / 实时预览，保存原始码流 | ✅ |
| 05 | [`05_ptz_control.py`](demo/05_ptz_control.py) | PTZ control: pan/tilt/zoom/focus/preset / 云台控制 | ✅ (PTZ camera) |
| 06 | [`06_snapshot.py`](demo/06_snapshot.py) | JPEG snapshots / JPEG 抓图 | ✅ |
| 07 | [`07_playback_download.py`](demo/07_playback_download.py) | Query & download recordings by time range / 录像查询/下载 | ✅ |
| 08 | [`08_alarm_listen.py`](demo/08_alarm_listen.py) | Subscribe alarm events / 报警布防与事件监听 | ✅ |

```bash
# ⭐ Demo 01 — extract timestamps from any Hikvision video file
python demo/01_video_file_timestamps.py "/path/to/recording.mp4"
python demo/01_video_file_timestamps.py "/path/to/recording.mp4" --max-frames 100

# ⭐ Demo 02 — low-latency RTSP (multiple backends)
python demo/02_rtsp_low_latency.py --backend sdk \
    --ip 192.168.1.64 --user admin --pwd yourpassword

python demo/02_rtsp_low_latency.py --backend opencv \
    --url rtsp://admin:pwd@192.168.1.64:554/Streaming/Channels/101

python demo/02_rtsp_low_latency.py --backend auto \
    --ip 192.168.1.64 --user admin --pwd yourpassword \
    --url rtsp://admin:pwd@192.168.1.64:554/Streaming/Channels/101
```

Press `q` in the preview window to quit. See [`demo/README.md`](demo/README.md) for full details on every flag.

---

## 📖 API Reference / API 参考

### Public exports / 公开 API

```python
from hikvision_sdk import (
    HikvisionSDK,            # Global SDK lifecycle (singleton)
    Device,                  # Device login/logout session
    VideoFileReader,         # ⭐ Feature ① — per-frame absolute timestamps
    RTSPLowLatencyStream,    # ⭐ Feature ② — low-latency RTSP
    LiveStream,              # Real-time preview with raw stream callback
    PlayBack, RecordFile,    # Remote playback & download
    PlayM4Decoder,           # Direct PlayM4(PlayCtrl) wrapper
    PTZController,           # PTZ camera control
    AlarmListener,           # Alarm event subscription
    HikvisionError,          # Unified exception with Chinese messages
    DeviceInfo, FrameTimestamp, VideoFileInfo,  # Dataclasses
    snapshot, config,        # JPEG capture / generic config get-set
)
```

### `HikvisionSDK` — Global lifecycle

```python
with HikvisionSDK(log_dir="./SdkLog", log_level=2) as sdk:
    print(sdk.get_version_string())   # "6.1.9.48"
    print(sdk.get_last_error())       # 0
```

| Method | Description |
|---|---|
| `initialize()` | Calls `NET_DVR_Init` and applies the COM/SSL paths |
| `cleanup()` | Calls `NET_DVR_Cleanup` |
| `get_version_string()` | Returns `"6.1.9.48"` |
| `get_last_error()` | Returns the latest `NET_DVR_GetLastError()` |
| `get_instance()` / `release_instance()` | Reference-counted singleton access |

### `Device` — Login session

```python
with HikvisionSDK():
    with Device("192.168.1.64", "admin", "pwd", port=8000) as dev:
        print(dev.info.serial_number)      # "DS-2CD2T47G2-L20240101AAWR..."
        print(dev.info.channel_num)        # 4
        print(dev.info.ip_channel_num)     # 0
```

### ⭐ `VideoFileReader` — Per-frame absolute timestamps

```python
reader = VideoFileReader("recording.mp4")

# 1. Metadata first
info = reader.get_info()             # → VideoFileInfo dataclass
print(info)

# 2. Then iterate
for ts in reader.iter_frame_timestamps():
    print(ts.frame_index, ts.datetime_str, ts.epoch_ms, ts.frame_type, ts.pts_ms)

# Or with decoded BGR images:
for ts, frame_bgr in reader.iter_frames(decode_image=True, color="BGR"):
    cv2.imwrite(f"frame_{ts.frame_index:06d}.jpg", frame_bgr)

# Or with raw YUV bytes:
for ts, yuv_bytes in reader.iter_frames(decode_image=True, color="YUV"):
    ...
```

> **How does it work?** `PlayM4_GetSystemTime()` extracts the device's real wall-clock time directly from `NET_DVR_PRIVATE_DATA` headers in iVMS-4200 / SDK-downloaded private streams. For plain MP4 files lacking those headers, it falls back to `start_datetime + PTS_offset`.

### ⭐ `RTSPLowLatencyStream` — Dual-backend low-latency RTSP

```python
stream = RTSPLowLatencyStream(
    url="rtsp://...",         # for opencv backend
    device=device,            # for sdk backend (logged-in Device)
    channel=1,
    stream_type=0,            # 0=main 1=sub
    backend="auto",           # "sdk" | "opencv" | "auto"
    transport="tcp",          # opencv backend only
    drop_old_frames=True,     # latest-frame-only buffer
    buffer_size=1,            # PlayM4 display buffer (1 = lowest latency)
)

stream.start()
frame, ts = stream.read(timeout=1.0, raw=False)
# frame: numpy.ndarray (H, W, 3) BGR  (or YV12 bytes if raw=True)
# ts:    FrameTimestamp
stream.stop()
```

| Backend | Latency | Needs device login? | Notes |
|---|---|:---:|---|
| `sdk` | **~150–250 ms** | ✅ | Hikvision private protocol, lowest latency |
| `opencv` | ~300–600 ms | ❌ | Standard RTSP via FFmpeg, cross-vendor |
| `auto` | best available | optional | Tries SDK first, falls back to OpenCV |

**Latency optimizations applied automatically:**

- SDK: `NET_DVR_SetRecvTimeOut(300)`, `PlayM4_SetDisplayBuf(1)`, single-slot frame buffer
- OpenCV: `rtsp_transport=tcp`, `fflags=nobuffer`, `flags=low_delay`, `reorder_queue_size=0`, background grab thread

### Other modules at a glance

```python
# PTZ
from hikvision_sdk import PTZController
ptz = PTZController(dev, channel=1)
ptz.up(speed=5, duration=1.0)
ptz.zoom_in(); ptz.goto_preset(1)

# Snapshot
from hikvision_sdk import snapshot
snapshot.capture_jpeg_to_file(dev, channel=1, save_path="snap.jpg")
jpg_bytes = snapshot.capture_jpeg(dev, channel=1)

# Playback
from hikvision_sdk import PlayBack
pb = PlayBack(dev)
files = pb.find_files(channel=1, start=t0, stop=t1)
pb.download_by_time(channel=1, start=t0, stop=t1, save_path="rec.mp4",
                    progress_callback=lambda pct: print(f"{pct}%"))

# Alarm
from hikvision_sdk import AlarmListener
with AlarmListener(dev) as alarm:
    alarm.on_event = lambda cmd, info, src: print(hex(cmd), len(info))

# Generic config (any NET_DVR_GET_xxx / NET_DVR_SET_xxx command)
from hikvision_sdk import config
print(config.get_device_time(dev))
```

### Error handling / 错误处理

```python
from hikvision_sdk import HikvisionError, describe_error

try:
    dev.login()
except HikvisionError as e:
    print(e.code)        # 1
    print(e.message)     # "用户名密码错误"
    print(e.api)         # "NET_DVR_Login_V40"
    print(str(e))        # "[NET_DVR_Login_V40] HCNetSDK 错误 1: 用户名密码错误"

# Or look up any code:
describe_error(7)        # "连接设备失败"
describe_error(99999)    # "未知错误(code=99999)"
```

100+ codes mapped from the HCNetSDK Programming Guide.

---

## 🏗️ Architecture / 架构

```
PyHikvisionSdk/
├── 📁 sdk/                              ← Single source of truth for native libraries
│   ├── 📁 win/                          Windows DLLs + HCNetSDKCom/ + include/
│   └── 📁 linux/                        Linux .so + HCNetSDKCom/ + include/
│
├── 📁 hikvision_sdk/                    ← Python package
│   ├── 🔧 _bindings/                    Low-level ctypes layer
│   │   ├── _HCNetSDK_official.py        Official ctypes mapping (rebased path)
│   │   ├── _PlayCtrl_official.py        PlayM4 bindings
│   │   └── loader.py                    Cross-platform library loader
│   ├── ⚙️  core.py                       HikvisionSDK singleton
│   ├── 📡 device.py                     Device login/logout
│   ├── 📁 stream/
│   │   ├── decoder.py                   PlayM4 wrapper
│   │   ├── live.py                      Real-time preview
│   │   └── playback.py                  Recording playback/download
│   ├── 🌟 video_file.py                 Feature ①: per-frame timestamps
│   ├── 🌟 rtsp_stream.py                Feature ②: low-latency dual-backend
│   ├── 🎮 ptz.py
│   ├── 📸 snapshot.py
│   ├── 🚨 alarm.py
│   ├── ⚙️  config.py
│   ├── ⚠️  exceptions.py                Error code → Chinese mapping
│   ├── 📦 types.py                      Public dataclasses
│   └── 🛠️  utils/
│       ├── time_utils.py                NET_DVR_TIME ↔ datetime
│       ├── color_convert.py             YV12 → BGR
│       └── logging.py
│
├── 📁 demo/                             ← Runnable examples
├── 📁 tests/                            ← 22-test integration suite
├── 📜 requirements.txt
└── 📖 README.md
```

### Design principles / 设计哲学

- **Single source of native libraries** — only `sdk/win` and `sdk/linux` are loaded; no system-wide installation, no PATH pollution
- **CWD-independent** — everything resolves from `__file__`, so the package works from any working directory
- **Pythonic over C-style** — context managers, dataclasses, generators, type hints
- **Errors are exceptions** — no silent failures; every SDK call that returns false raises `HikvisionError` with the actual code and a Chinese description
- **Latest-frame-wins for streams** — eliminates accumulated latency without complex queue management

---

## 🧪 Testing / 测试

The repository ships with a **22-test integration suite** that runs **without any physical device or sample video**, by exercising real DLL loading, real `NET_DVR_Init`, real PlayM4 port allocation, and real (failing) login attempts to verify ctypes signatures and error paths.

```bash
python tests/test_integration.py
```

```
=== hikvision_sdk 自检测试 ===
Python      : 3.12.3
Platform    : Windows 64bit

[PASS] T01 包导入 & 公共 API
[PASS] T02 loader 路径 & dll 加载
[PASS] T03 loader 非法平台拒绝
[PASS] T04 SDK 完整生命周期         -- SDK 版本=6.1.9.48
[PASS] T05 SDK 单例引用计数
[PASS] T06 PlayM4 多端口分配         -- 分配并释放了 4 个端口
[PASS] T07 错误码翻译
[PASS] T08 时间工具
[PASS] T09 ctypes 结构体绑定
[PASS] T10 视频文件不存在
[PASS] T11 视频文件垃圾数据         -- PlayM4_OpenFile 失败, code=16
[PASS] T12 数据类格式化
[PASS] T13 YV12→BGR 转换            -- 灰度 (128,128,128) → BGR (130,130,130)
[PASS] T14 登录到不通 IP            -- code=7 (连接设备失败), 耗时 2.0s
[PASS] T15 干净 init 的 last_error
[PASS] T16 PlayBack 时间结构体
[PASS] T17 RTSP 参数校验
[PASS] T18 上层模块可构造
[PASS] T19 demo 脚本编译
[PASS] T20 包模块编译               -- 全部 23 个 .py 模块编译通过
[PASS] T21 logging 幂等
[PASS] T22 常量值校验

=== 结果: 22/22 通过, 0 失败 ===
```

---

## ❓ FAQ / 常见问题

<details>
<summary><b>Q: My video file is a plain MP4 (not from Hikvision). Will timestamps work?</b></summary>

The absolute timestamp comes from `NET_DVR_PRIVATE_DATA` headers embedded in Hikvision private-stream files (typically those downloaded via iVMS-4200 or `NET_DVR_GetFileByName`). Plain MP4 files lacking these headers will fall back to `start_datetime + PTS_offset`, which is still useful but not device-side absolute time.

**视频文件必须是海康私有流（含 PRIVATE_DATA 帧头）才能拿到设备端真实绝对时间。** 普通 mp4 会退化为"起始时间+PTS 偏移"。
</details>

<details>
<summary><b>Q: Do I need to install Hikvision's own SDK?</b></summary>

**No.** All required `.dll` (Windows) and `.so` (Linux) files are bundled in `sdk/win` and `sdk/linux`. Just `git clone` and you're ready.

**不需要。** 所有运行时已捆绑在 `sdk/win` 和 `sdk/linux`，git clone 即可使用。
</details>

<details>
<summary><b>Q: "DLL load failed" on Windows?</b></summary>

Install [Microsoft Visual C++ 2015–2022 Redistributable (x64)](https://aka.ms/vs/17/release/vc_redist.x64.exe). The Hikvision DLLs depend on the MSVC runtime.

请安装 [VC++ 2015–2022 运行库 (x64)](https://aka.ms/vs/17/release/vc_redist.x64.exe)。
</details>

<details>
<summary><b>Q: How low is "low latency" really?</b></summary>

Measured on a 100 Mbps LAN with a Hikvision DS-2CD2T47G2-L:
- **SDK backend**: ~150–250 ms glass-to-glass
- **OpenCV backend (TCP)**: ~300–600 ms
- **OpenCV backend (UDP)**: ~250–450 ms (but jittery)

Latency depends on encoder GOP size, network conditions, and your host's CPU.

实测延迟（局域网，DS-2CD2T47G2-L）：SDK ≈150–250 ms，OpenCV ≈300–600 ms。
</details>

<details>
<summary><b>Q: Can I use this on a Raspberry Pi / ARM device?</b></summary>

Hikvision provides a separate **ARM 32/64-bit SDK** which we have not bundled here. If you need ARM support, drop the corresponding `.so` files into a new `sdk/linux_arm64/` folder and adjust `loader.py` accordingly. PRs welcome!

如需 ARM 支持，需自行从海康官网下载 ARM SDK 并放入 `sdk/linux_arm64/`，然后调整 `loader.py`。欢迎 PR。
</details>

<details>
<summary><b>Q: Is this an official Hikvision package?</b></summary>

**No.** This is an independent open-source wrapper around Hikvision's HCNetSDK. We are not affiliated with or endorsed by Hangzhou Hikvision Digital Technology Co., Ltd. The bundled `.dll`/`.so` files remain the property of Hikvision and are subject to their EULA.

**本项目非海康官方项目**，是对 HCNetSDK 的独立第三方封装。捆绑的 `.dll`/`.so` 版权归海康威视所有，须遵循其 EULA。
</details>

---

## 🤝 Contributing / 贡献

Contributions are very welcome! 欢迎贡献代码、报告 bug、提交功能建议！

- 🐛 [Report a bug / 报告问题](https://github.com/ygxiuming/PyHikvisionSdk/issues/new?template=bug_report.md)
- ✨ [Request a feature / 功能建议](https://github.com/ygxiuming/PyHikvisionSdk/issues/new?template=feature_request.md)
- 📖 [See our contributing guide / 查看贡献指南](CONTRIBUTING.md)

### Development setup / 开发环境

```bash
git clone https://github.com/ygxiuming/PyHikvisionSdk.git
cd PyHikvisionSdk
pip install -r requirements.txt
python tests/test_integration.py    # should print 22/22 passing
```

---

## 🗺️ Roadmap

- [ ] ARM Linux support (Jetson / Raspberry Pi)
- [ ] macOS support (via Hikvision macOS SDK if/when officially released)
- [ ] Async/await API (`asyncio`) for stream readers
- [ ] Built-in NALU parser to provide accurate I/P/B frame type detection
- [ ] Optional GStreamer backend for the lowest latency on Linux
- [ ] PyPI package release

---

## 📜 License / 许可

This project's **Python source code** is released under the [MIT License](LICENSE).

The **bundled native libraries** (`sdk/win/*.dll`, `sdk/linux/*.so`) are © Hangzhou Hikvision Digital Technology Co., Ltd. and remain subject to the [Hikvision SDK EULA](https://www.hikvision.com/). Redistribution of these binaries is intended for development convenience; consult Hikvision's terms before commercial deployment.

本项目 **Python 源码** 采用 [MIT 许可证](LICENSE)。
**捆绑的二进制库**版权归海康威视所有，遵循其 [SDK EULA](https://www.hikvision.com/)。

---

## 🌟 Star History

If this project helps you, please consider giving it a star ⭐ — it really motivates ongoing development!

如果本项目对你有帮助，请点一个 ⭐ Star 支持持续维护！

[![Star History Chart](https://api.star-history.com/svg?repos=ygxiuming/PyHikvisionSdk&type=Date)](https://star-history.com/#ygxiuming/PyHikvisionSdk&Date)

---

<div align="center">

**Made with ❤️ for the computer vision community**

[⬆ Back to top](#-pyhikvisionsdk)

</div>
