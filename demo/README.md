# Demo 示例集合

每个脚本都可以**独立**运行，统一通过命令行参数传入设备信息。

> 运行前提：
> 1. 项目根目录已有 `sdk/win` 与 `sdk/linux`（包含全部 dll/so）
> 2. 已安装 Python 依赖：`pip install -r ../requirements.txt`
> 3. **Windows** 上若运行报"找不到 dll"，请先安装 Visual C++ 2015–2022 运行库
>    （海康 dll 依赖 MSVC 运行时）。

| 脚本 | 功能 | 是否需要联机设备 |
|---|---|---|
| `01_video_file_timestamps.py` | ★ **功能①**：读取本地海康视频文件并逐帧输出绝对时间戳 | 否（只需视频文件） |
| `02_rtsp_low_latency.py`      | ★ **功能②**：低延迟 RTSP 拉流，支持 SDK / OpenCV 双后端 | 是 |
| `03_login_and_info.py`        | 登录设备并打印基本信息 | 是 |
| `04_live_preview.py`          | 实时预览，回调收原始 H.264/H.265 码流 | 是 |
| `05_ptz_control.py`           | 云台控制（方向/变倍/聚焦/预置点） | 是（需要球机） |
| `06_snapshot.py`              | JPEG 抓图（落盘或字节流） | 是 |
| `07_playback_download.py`     | 远程查询/下载录像 | 是（设备有录像） |
| `08_alarm_listen.py`          | 报警布防 + 事件监听 | 是 |
| `09_multi_rtsp_sync.py`       | ★ **功能③**：多路 RTSP 接入 + 流内时间戳对帧 + cv 拼接播放（默认 8 路，配置区变量驱动） | 是 |

---

## ★ Demo 01 — 文件逐帧绝对时间戳

```bash
python 01_video_file_timestamps.py "D:/records/ch01_20240601_080000.mp4"
python 01_video_file_timestamps.py "D:/records/ch01.mp4" --max-frames 200
python 01_video_file_timestamps.py "D:/records/ch01.mp4" --save-frames out_jpgs/
```

输出示例：

```
[视频信息]
  文件: D:\records\ch01_20240601_080000.mp4
  大小: 1247.83 MB (1308482048 bytes)
  总时长: 3600.00 s
  总帧数: 90000
  分辨率: 1920x1080
  帧率: 25.00 fps
  起始绝对时间: 2024-06-01 08:00:00.000
  编码: H.264 / H.265 (Hikvision)

[逐帧绝对时间戳]
  #000000  2024-06-01 08:00:00.000  epoch_ms=1717200000000  type=I  pts=0ms
  #000001  2024-06-01 08:00:00.040  epoch_ms=1717200000040  type=?  pts=40ms
  ...
```

> **关于绝对时间戳来源**：
> - 当文件是 iVMS-4200 / SDK 备份下载的 **海康私有流**（含 `NET_DVR_PRIVATE_DATA` 帧头）
>   时，PlayM4 直接从码流里读出每帧的绝对时间，**精度毫秒级、与设备本地时间一致**。
> - 当文件是普通 mp4，PlayM4 无法返回绝对时间，本模块会退化为 "起始时间 + PTS 偏移"。

---

## ★ Demo 02 — 低延迟 RTSP 拉流

```bash
# SDK 后端（最低延迟，推荐）：
python 02_rtsp_low_latency.py --backend sdk --ip 192.168.1.64 \
    --user admin --pwd "yourpassword" --channel 1 --stream-type 0

# OpenCV/FFmpeg 后端（标准 RTSP）：
python 02_rtsp_low_latency.py --backend opencv \
    --url "rtsp://admin:yourpassword@192.168.1.64:554/Streaming/Channels/101"

# auto = 优先 SDK，失败自动降级 OpenCV：
python 02_rtsp_low_latency.py --backend auto --ip 192.168.1.64 \
    --user admin --pwd "yourpassword" \
    --url "rtsp://admin:yourpassword@192.168.1.64:554/Streaming/Channels/101"
```

按 `q` 键退出预览窗口。

低延迟优化已经做的事情：
- SDK 后端：`NET_DVR_SetRecvTimeOut(300)`、关闭长重连、`PlayM4_SetDisplayBuf(1)`、解码回调使用单槽缓冲（旧帧覆盖丢弃）
- OpenCV 后端：`OPENCV_FFMPEG_CAPTURE_OPTIONS=rtsp_transport=tcp;fflags=nobuffer;flags=low_delay;reorder_queue_size=0;buffer_size=102400`、后台 grab + 主线程取最新一帧

---

## ★ Demo 09 — 多路 RTSP 接入 + 流内时间戳对帧 + cv 拼接播放（最低时延版）

在一个进程内同时接入**多路**海康 RTSP 流（默认 8 路），核心是 `MultiRTSPSync.align_frames()`
**对帧函数**：通过对比每一路每一帧的**流内绝对时间戳**（由海康 SDK `PlayM4_GetSystemTime` 从
`NET_DVR_PRIVATE_DATA` 私有头解析出的设备端真实时间，**不是本机墙钟**），挑出"同一时刻"的一组帧
组成 `list` 返回；服务 demo 再用 OpenCV 拼成网格画面实时播放。

**无需命令行参数**——直接编辑脚本顶部【配置区】变量即可。

### 时间戳来源（关键）

| 模式 | 后端 | 时间戳来源 | 是否流内时间 |
|---|---|---|---|
| `nvr`（默认/推荐） | SDK 私有协议 `NET_DVR_RealPlay_V40` | `PlayM4_GetSystemTime` 从私有头解析 | ✅ 设备端绝对时间 |
| `urls`（跨厂商兜底） | opencv/FFmpeg | 本机墙钟 `datetime.now()` | ❌ 受拉流延迟差影响 |

> `nvr` 模式下一台 NVR 登录一次，N 路通道走私有协议，多路共用同一设备时钟，天然可对齐。

### 对帧算法（`align_frames`）—— 严格 2 帧时延

1. 参考时刻 `T = min(各路最新流内时间戳)`——"最慢一路"的最新帧时刻，保证每路都有 `≤T` 的帧，
   且让对齐组尽可能贴近"现在"（最低时延）。
2. 每路在环形缓冲（`BUFFER_FRAMES=6`，约 240ms 历史）里做最近邻查找，按路序组成 `list`。
3. 组内最大偏差 `max_dev ≤ TOLERANCE_MS`（80ms）才返回；否则 sleep 2ms 重试，**总等待不超过
   `ALIGN_TIMEOUT_MS`（80ms）**——超时丢弃该组，**不堆积延迟**。

> 25fps 下 1 帧 = 40ms，2 帧 = 80ms。`TOLERANCE_MS`、`ALIGN_TIMEOUT_MS` 均设为 80，保证对帧
> 消耗与等待都不超过 2 帧。

### 配置区（脚本顶部变量，直接编辑）

```python
MODE = "nvr"                # "nvr"=同设备多通道(SDK,流内时间戳) / "urls"=自定义地址(opencv)

# nvr 模式
NVR_IP = "192.168.1.64"
NVR_PORT = 8000             # SDK 端口（不是 RTSP 554）
NVR_USER = "admin"
NVR_PWD = "yourpassword"
CHANNELS = 8                # 路数
STREAM_TYPE = 0             # 0=主码流 1=子码流

# urls 模式（跨厂商兜底，时间戳退化为本机墙钟）
RTSP_URLS = []

# 对帧参数（25fps 两帧 = 80ms）
TOLERANCE_MS = 80.0         # 组内最大偏差 ≤ 2 帧
ALIGN_TIMEOUT_MS = 80.0     # 单次对齐等待 ≤ 2 帧（超时丢弃，不堆积）
BUFFER_FRAMES = 6           # 每路保留 ~240ms 历史

# 播放参数
TILE_W, TILE_H = 480, 270
GRID = (4, 2)               # (cols, rows)
TARGET_FPS = 25.0
```

### 运行

```bash
python demo/09_multi_rtsp_sync.py
```

按 `q` 键退出预览窗口。运行时会打印每秒统计：实测 fps、参考时刻（流内时间）、组内最大偏差、
流内时间戳命中率。

### 时延控制总结

| 项 | 值 | 说明 |
|---|---|---|
| SDK 后端端到端 | ~150–250 ms | 私有协议，最低延迟 |
| `TOLERANCE_MS` | 80 ms | 组内最大偏差 ≤ 2 帧 |
| `ALIGN_TIMEOUT_MS` | 80 ms | 对齐等待 ≤ 2 帧，超时丢弃 |
| `BUFFER_FRAMES` | 6 | 每路 ~240ms 历史，够最近邻查找 |
| PlayM4 `display_buf` | 1 | 最低解码延迟 |
| 对齐轮询间隔 | 2 ms | 及时捕捉新帧 |
