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
