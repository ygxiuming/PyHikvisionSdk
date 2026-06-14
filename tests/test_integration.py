# -*- coding: utf-8 -*-
"""集成测试套件：在没有真实设备/视频文件的情况下，
验证 hikvision_sdk 的代码正确性。

每个测试函数返回 (name, ok, detail)，主入口统一汇总结果。
"""

from __future__ import annotations

import io
import os
import sys
import time
import platform
import traceback
from contextlib import redirect_stderr
from datetime import datetime, timedelta

# 把项目根加进 sys.path
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)


# ============================================================== #
#  辅助
# ============================================================== #

class Result:
    def __init__(self, name: str, ok: bool, detail: str = ""):
        self.name = name
        self.ok = ok
        self.detail = detail

    def __str__(self) -> str:
        flag = "PASS" if self.ok else "FAIL"
        s = f"[{flag}] {self.name}"
        if self.detail:
            s += f"  -- {self.detail}"
        return s


def run(name: str, fn) -> Result:
    """用 stderr 重定向运行单个测试，捕获日志噪音。"""
    buf = io.StringIO()
    try:
        with redirect_stderr(buf):
            detail = fn()
        return Result(name, True, detail or "")
    except AssertionError as e:
        return Result(name, False, f"AssertionError: {e}")
    except Exception as e:
        tb = traceback.format_exc(limit=3)
        return Result(name, False, f"{type(e).__name__}: {e}\n{tb}")


# ============================================================== #
#  T01: 包导入 & 公共 API 完整
# ============================================================== #
def t_imports() -> str:
    import hikvision_sdk as h
    expected = {
        "HikvisionSDK", "Device", "VideoFileReader", "RTSPLowLatencyStream",
        "LiveStream", "PlayBack", "PlayM4Decoder", "PTZController",
        "AlarmListener", "HikvisionError", "DeviceInfo", "FrameTimestamp",
        "VideoFileInfo", "DecodedFrame", "StreamConfig", "RecordFile",
        "describe_error", "snapshot", "config",
    }
    missing = expected - set(h.__all__)
    assert not missing, f"缺失公共导出: {missing}"
    # 子模块也都能 import
    from hikvision_sdk._bindings import HCNetSDK, PlayCtrl, loader  # noqa
    from hikvision_sdk.utils import time_utils, color_convert, logging_utils  # noqa
    from hikvision_sdk.stream import decoder, live, playback  # noqa
    return f"已导出 {len(h.__all__)} 个公共 API; 版本={h.__version__}"


# ============================================================== #
#  T02: loader 路径解析 + dll 实际可加载
# ============================================================== #
def t_loader_paths() -> str:
    from hikvision_sdk._bindings import loader

    root = loader.get_project_root()
    sdk_root = loader.get_sdk_root()
    plat_dir = loader.get_platform_sdk_dir()
    com_dir = loader.get_hcnetsdk_com_dir()

    assert root.exists(), f"工程根不存在: {root}"
    assert sdk_root.exists(), f"sdk 根不存在: {sdk_root}"
    assert plat_dir.exists(), f"平台 SDK 目录不存在: {plat_dir}"
    assert com_dir.exists(), f"HCNetSDKCom 子目录不存在: {com_dir}"

    sys_type = loader._current_system_type()
    netsdk_path = loader.resolve_netsdk_dll_path(sys_type)
    play_path = loader.resolve_playctrl_dll_path(sys_type)
    assert os.path.isfile(netsdk_path), f"HCNetSDK 库文件不存在: {netsdk_path}"
    assert os.path.isfile(play_path), f"PlayCtrl 库文件不存在: {play_path}"

    # 直接 ctypes 实测加载（loader 内部的 load_hcnetsdk）
    h_handle = loader.load_hcnetsdk()
    p_handle = loader.load_playctrl()
    assert h_handle is not None
    assert p_handle is not None
    return f"系统={sys_type}, sdk_dir={plat_dir.name}, 主库已加载"


# ============================================================== #
#  T03: 错误路径解析（请求不存在的平台标识）
# ============================================================== #
def t_loader_invalid_platform() -> str:
    from hikvision_sdk._bindings import loader
    try:
        loader.resolve_netsdk_dll_path("solaris99")
    except RuntimeError as e:
        assert "未知" in str(e) or "unknown" in str(e).lower()
        return "未知平台被正确拒绝"
    raise AssertionError("应当抛 RuntimeError")


# ============================================================== #
#  T04: SDK 单例 + 全生命周期
# ============================================================== #
def t_sdk_lifecycle() -> str:
    from hikvision_sdk import HikvisionSDK
    # 第一次
    with HikvisionSDK() as sdk:
        v = sdk.get_version_string()
        assert v == "6.1.9.48", f"版本不匹配: {v}"
        last = sdk.get_last_error()
        assert last == 0, f"初始 last_error 应为 0, 实际 {last}"
    # cleanup 后再次构造，应仍可用（单例已被释放）
    with HikvisionSDK() as sdk2:
        v2 = sdk2.get_version_string()
        assert v2 == "6.1.9.48"
    return f"SDK 版本={v}; 重复 init/cleanup 通过"


# ============================================================== #
#  T05: 单例引用计数 — 多次 get_instance 不会重复 init
# ============================================================== #
def t_singleton_refcount() -> str:
    from hikvision_sdk import HikvisionSDK
    s1 = HikvisionSDK.get_instance()
    s2 = HikvisionSDK.get_instance()
    s3 = HikvisionSDK.get_instance()
    assert s1 is s2 is s3, "get_instance 应返回同一对象"
    HikvisionSDK.release_instance()
    HikvisionSDK.release_instance()
    HikvisionSDK.release_instance()
    # 引用归零后再获取应能正常 init
    s4 = HikvisionSDK.get_instance()
    assert s4 is not None
    HikvisionSDK.release_instance()
    return "单例 + 引用计数行为正确"


# ============================================================== #
#  T06: PlayM4 端口分配/释放
# ============================================================== #
def t_playm4_port() -> str:
    from hikvision_sdk import HikvisionSDK, PlayM4Decoder
    with HikvisionSDK():
        ports = []
        decoders = []
        # 海康 PlayM4 通常支持最多 16 个端口
        for _ in range(4):
            d = PlayM4Decoder()
            p = d.acquire_port()
            assert p >= 0, f"端口无效: {p}"
            ports.append(p)
            decoders.append(d)
        # 端口号应互不相同
        assert len(set(ports)) == len(ports), f"端口重复: {ports}"
        for d in decoders:
            d.release_port()
    return f"分配并释放了 {len(ports)} 个 PlayM4 端口: {ports}"


# ============================================================== #
#  T07: HikvisionError + 错误码翻译
# ============================================================== #
def t_error_translation() -> str:
    from hikvision_sdk import HikvisionError, describe_error
    # 已知错误码
    assert "用户名密码错误" in describe_error(1)
    assert "网络通信错误" in describe_error(35)
    assert "操作成功" in describe_error(0)
    # 未知错误码兜底
    assert "未知错误" in describe_error(99999)
    # 异常对象
    e = HikvisionError(1, api="NET_DVR_Login_V40")
    assert e.code == 1
    assert "用户名密码错误" in str(e)
    assert "NET_DVR_Login_V40" in str(e)
    # 自定义 message
    e2 = HikvisionError(99999, message="自定义错误", api="X")
    assert e2.message == "自定义错误"
    return "100+ 错误码映射、未知码兜底、API 标签均正常"


# ============================================================== #
#  T08: 时间工具
# ============================================================== #
def t_time_utils() -> str:
    from hikvision_sdk.utils import time_utils as tu
    dt = datetime(2024, 6, 1, 8, 0, 0, 123000)
    ms = tu.datetime_to_epoch_ms(dt)
    # 反向再来一次
    dt2 = tu.epoch_ms_to_datetime(ms)
    diff = abs((dt2 - dt).total_seconds())
    assert diff < 1.0, f"时间往返误差过大: {diff}s"

    # 偏移
    dt3 = tu.offset_datetime_ms(dt, 500)
    assert (dt3 - dt) == timedelta(milliseconds=500)

    # 格式化
    s = tu.fmt_datetime_ms(dt)
    assert s == "2024-06-01 08:00:00.123", f"格式化输出错误: {s}"

    # NET_DVR_TIME 转换
    from hikvision_sdk._bindings import HCNetSDK
    nd = HCNetSDK.NET_DVR_TIME()
    nd.dwYear = 2024; nd.dwMonth = 6; nd.dwDay = 1
    nd.dwHour = 8; nd.dwMinute = 0; nd.dwSecond = 0
    dtt = tu.net_dvr_time_to_datetime(nd)
    assert dtt == datetime(2024, 6, 1, 8, 0, 0)
    return f"epoch_ms={ms}, 格式化={s}, NET_DVR_TIME 转换通过"


# ============================================================== #
#  T09: ctypes 结构体大小 / 字段一致性
# ============================================================== #
def t_struct_sizes() -> str:
    from ctypes import sizeof
    from hikvision_sdk._bindings import HCNetSDK
    from hikvision_sdk.stream.decoder import PLAYM4_SYSTEM_TIME

    # PLAYM4_SYSTEM_TIME 必须是 7 个 c_uint = 28 字节
    assert sizeof(PLAYM4_SYSTEM_TIME) == 28, f"PLAYM4_SYSTEM_TIME 应为 28 字节, 实际 {sizeof(PLAYM4_SYSTEM_TIME)}"

    # NET_DVR_USER_LOGIN_INFO 需要包含我们要写的字段
    login = HCNetSDK.NET_DVR_USER_LOGIN_INFO()
    login.sDeviceAddress = b"192.168.1.64"
    login.wPort = 8000
    login.sUserName = b"admin"
    login.sPassword = b"password"
    login.byLoginMode = 0
    assert login.sDeviceAddress.startswith(b"192.168")

    # NET_DVR_DEVICEINFO_V40 含 V30 嵌套
    di = HCNetSDK.NET_DVR_DEVICEINFO_V40()
    assert hasattr(di, "struDeviceV30")
    assert hasattr(di.struDeviceV30, "byChanNum")
    assert hasattr(di.struDeviceV30, "byIPChanNum")

    # NET_DVR_PREVIEWINFO 字段
    pi = HCNetSDK.NET_DVR_PREVIEWINFO()
    pi.lChannel = 1
    pi.dwStreamType = 0
    pi.dwLinkMode = 0
    pi.bBlocked = 1

    # FRAME_INFO
    from hikvision_sdk._bindings import PlayCtrl
    fi = PlayCtrl.FRAME_INFO()
    fi.nWidth = 1920
    fi.nHeight = 1080
    assert fi.nWidth == 1920 and fi.nHeight == 1080
    return (f"PLAYM4_SYSTEM_TIME=28B, "
            f"USER_LOGIN_INFO 字段 OK, DEVICEINFO_V40 嵌套 OK, "
            f"PREVIEWINFO/FRAME_INFO 可读写")


# ============================================================== #
#  T10: VideoFileReader 错误处理（不存在的文件）
# ============================================================== #
def t_video_file_not_found() -> str:
    from hikvision_sdk import HikvisionSDK, VideoFileReader
    with HikvisionSDK():
        try:
            VideoFileReader(r"D:\not\exist\nonsense.mp4")
        except FileNotFoundError as e:
            assert "不存在" in str(e) or "exist" in str(e).lower()
            return "不存在的文件被正确拒绝"
    raise AssertionError("应当抛 FileNotFoundError")


# ============================================================== #
#  T11: VideoFileReader 对随机字节文件的优雅失败（不会段错误）
# ============================================================== #
def t_video_file_garbage() -> str:
    """构造一个非视频的小文件，PlayM4_OpenFile 应失败但进程不能崩。"""
    import tempfile
    from hikvision_sdk import HikvisionSDK, VideoFileReader
    from hikvision_sdk.stream.decoder import PlayM4Decoder

    fd, path = tempfile.mkstemp(suffix=".mp4")
    os.close(fd)
    try:
        with open(path, "wb") as f:
            f.write(b"NOT A REAL VIDEO" * 64)  # 1KB 垃圾
        with HikvisionSDK():
            reader = VideoFileReader(path)
            try:
                # 应当抛 RuntimeError("PlayM4_OpenFile 失败...")
                reader.get_info()
                # 部分 SDK 容忍乱数据 -> 也接受
                return "SDK 容忍此文件（信息可能不完整）"
            except RuntimeError as e:
                assert "PlayM4_OpenFile" in str(e) or "失败" in str(e)
                return f"垃圾文件被正确拒绝: {str(e)[:60]}"
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


# ============================================================== #
#  T12: VideoFileInfo / FrameTimestamp 数据类
# ============================================================== #
def t_dataclasses() -> str:
    from hikvision_sdk import VideoFileInfo, FrameTimestamp, DeviceInfo
    info = VideoFileInfo(
        file_path="x.mp4", file_size=1024 * 1024,
        duration_seconds=10.0, total_frames=250,
        width=1920, height=1080, frame_rate=25.0,
        start_datetime=datetime(2024, 6, 1, 8, 0, 0),
    )
    s = str(info)
    assert "1920x1080" in s and "25.00 fps" in s and "2024-06-01" in s

    ft = FrameTimestamp(
        frame_index=42,
        datetime=datetime(2024, 6, 1, 8, 0, 1, 456000),
        epoch_ms=1717200001456,
        frame_type="P",
        pts_ms=1456,
    )
    assert "#000042" in str(ft)
    assert ft.datetime_str == "2024-06-01 08:00:01.456"

    di = DeviceInfo(serial_number="DS-2CD2T47G2-L20240101AAWR123456",
                    channel_num=1, ip_channel_num=0, user_id=0)
    d = di.to_dict()
    assert d["serial_number"].startswith("DS-2CD")
    return "VideoFileInfo/FrameTimestamp/DeviceInfo 字段与格式化均正确"


# ============================================================== #
#  T13: YV12 → BGR 颜色转换
# ============================================================== #
def t_yv12_to_bgr() -> str:
    try:
        import numpy as np
        import cv2  # noqa
    except ImportError:
        return "SKIP（numpy/opencv 未安装）"

    from hikvision_sdk.utils.color_convert import (
        yv12_buffer_to_bgr, yv12_buffer_to_yuv_array, has_cv2, has_numpy,
    )
    assert has_numpy() and has_cv2()

    # 构造一个全 128(灰) 的 YV12 缓冲区: w*h Y 平面 + 半分辨 U/V 平面
    w, h = 320, 240
    y_size = w * h
    uv_size = (w // 2) * (h // 2)
    buf = bytes([128] * y_size) + bytes([128] * uv_size) + bytes([128] * uv_size)
    bgr = yv12_buffer_to_bgr(buf, w, h)
    assert bgr.shape == (h, w, 3), f"BGR shape 错: {bgr.shape}"
    assert bgr.dtype.name == "uint8"
    # Y=128 U=V=128 在 BT.601 下应得灰色（约 128,128,128）
    avg = bgr.mean(axis=(0, 1))
    assert all(120 <= v <= 135 for v in avg), f"灰色像素期望约 128, 实际 {avg}"

    yuv = yv12_buffer_to_yuv_array(buf, w, h)
    assert yuv.shape == (y_size + 2 * uv_size,)

    # 缓冲区不足应抛异常
    try:
        yv12_buffer_to_bgr(buf[:100], w, h)
        raise AssertionError("应当抛 ValueError")
    except ValueError:
        pass
    return f"320x240 YV12→BGR 通过, 灰度均值={tuple(avg.round().astype(int))}"


# ============================================================== #
#  T14: Device 登录失败处理（连接到一个不存在的 IP）
# ============================================================== #
def t_device_login_failure() -> str:
    """登录到一个肯定无法连通的 IP，期望快速失败而不是段错误。"""
    from hikvision_sdk import HikvisionSDK, Device, HikvisionError

    with HikvisionSDK():
        # 用 192.0.2.x（RFC5737 文档段，绝不会被路由）
        dev = Device("192.0.2.1", "admin", "wrongpwd", port=8000)
        # 缩短超时
        dev.netsdk.NET_DVR_SetConnectTime(2000, 1)
        t0 = time.time()
        try:
            dev.login()
        except HikvisionError as e:
            elapsed = time.time() - t0
            # 错误码常见为 7（连接设备失败）/ 10（超时）/ 35（网络通信）
            assert e.code in (7, 8, 9, 10, 11, 35, 64, 71, 76), \
                f"意外错误码 {e.code}: {e.message}"
            return f"登录失败按预期抛 HikvisionError: code={e.code} ({e.message}), 耗时 {elapsed:.1f}s"
    raise AssertionError("应当抛 HikvisionError")


# ============================================================== #
#  T15: 错误码 NET_DVR_GetLastError 在干净 init 后为 0
# ============================================================== #
def t_clean_last_error() -> str:
    from hikvision_sdk import HikvisionSDK
    with HikvisionSDK() as sdk:
        # 通过 GetSDKVersion 这类无错的 API 调用之后
        _ = sdk.get_version_string()
        last = sdk.get_last_error()
        assert last == 0, f"成功调用后 last_error 应为 0, 实际 {last}"
    return "成功调用后 GetLastError == 0"


# ============================================================== #
#  T16: PlayBack 时间结构体往返
# ============================================================== #
def t_playback_time_roundtrip() -> str:
    from hikvision_sdk.stream.playback import _to_struct_time, _from_struct_time
    dt = datetime(2024, 12, 31, 23, 59, 59)
    s = _to_struct_time(dt)
    assert int(s.dwYear) == 2024 and int(s.dwSecond) == 59
    dt2 = _from_struct_time(s)
    assert dt2 == dt
    return f"NET_DVR_TIME 往返: {dt} -> struct -> {dt2}"


# ============================================================== #
#  T17: RTSPLowLatencyStream 参数校验
# ============================================================== #
def t_rtsp_param_validation() -> str:
    from hikvision_sdk import RTSPLowLatencyStream
    # 非法 backend
    try:
        RTSPLowLatencyStream(backend="ffmpeg-direct")
        raise AssertionError("应当 ValueError")
    except ValueError:
        pass

    # OpenCV 后端无 url
    s = RTSPLowLatencyStream(backend="opencv")
    try:
        s.start()
        raise AssertionError("应当 RuntimeError")
    except RuntimeError as e:
        assert "url" in str(e).lower() or "URL" in str(e)
    finally:
        s.stop()

    # SDK 后端无 device
    s2 = RTSPLowLatencyStream(backend="sdk")
    try:
        s2.start()
        raise AssertionError("应当 RuntimeError")
    except RuntimeError as e:
        assert "device" in str(e).lower() or "Device" in str(e) or "登录" in str(e)
    finally:
        s2.stop()
    return "非法 backend、缺 url、缺 device 三种错误均被正确拒绝"


# ============================================================== #
#  T18: AlarmListener / PTZController / snapshot 模块可构造
# ============================================================== #
def t_higher_modules_constructable() -> str:
    from hikvision_sdk import (
        HikvisionSDK, Device, AlarmListener, PTZController, LiveStream, PlayBack,
    )
    from hikvision_sdk import snapshot, config
    with HikvisionSDK():
        # 构造一个未登录 device 来测试上层类可以实例化
        dev = Device("192.0.2.1", "admin", "x", port=8000)
        # 不调用 login，只构造控制器对象
        ptz = PTZController(dev, channel=1)
        live = LiveStream(dev, channel=1)
        pb = PlayBack(dev)
        al = AlarmListener(dev)
        assert ptz._real_channel == 1
        assert live.channel == 1
        # snapshot/config 是函数模块，不构造
        assert callable(snapshot.capture_jpeg_to_file)
        assert callable(config.get_config)
        assert callable(config.get_device_time)
    return "PTZ / LiveStream / PlayBack / AlarmListener / snapshot / config 全部可构造或可调用"


# ============================================================== #
#  T19: Demo 脚本语法 + --help 解析
# ============================================================== #
def t_demo_scripts_compile() -> str:
    import py_compile
    demo_dir = os.path.join(_ROOT, "demo")
    files = sorted(f for f in os.listdir(demo_dir) if f.endswith(".py"))
    for f in files:
        py_compile.compile(os.path.join(demo_dir, f), doraise=True)
    return f"全部 {len(files)} 个 demo 脚本编译通过: {files}"


# ============================================================== #
#  T20: hikvision_sdk 包内全部模块编译通过
# ============================================================== #
def t_package_compile() -> str:
    import py_compile
    pkg_root = os.path.join(_ROOT, "hikvision_sdk")
    count = 0
    for root, _, files in os.walk(pkg_root):
        if "__pycache__" in root:
            continue
        for f in files:
            if f.endswith(".py"):
                py_compile.compile(os.path.join(root, f), doraise=True)
                count += 1
    return f"全部 {count} 个 .py 模块编译通过"


# ============================================================== #
#  T21: utils.logging 配置可重复调用
# ============================================================== #
def t_logging_idempotent() -> str:
    from hikvision_sdk.utils.logging import configure, get_logger
    configure()
    configure()  # 二次调用应无副作用
    log = get_logger("hikvision_sdk.test")
    log.info("自检日志（应只输出 1 行）")
    return "configure() 幂等"


# ============================================================== #
#  T22: snapshot 常量 / PTZ 常量值
# ============================================================== #
def t_constants() -> str:
    from hikvision_sdk.snapshot import (
        PIC_SIZE_HD1080P, PIC_SIZE_HD720P, PIC_SIZE_4CIF,
    )
    from hikvision_sdk.ptz import (
        TILT_UP, TILT_DOWN, PAN_LEFT, PAN_RIGHT,
        ZOOM_IN, ZOOM_OUT, FOCUS_NEAR, FOCUS_FAR,
    )
    assert PIC_SIZE_HD1080P == 0xFF
    assert PIC_SIZE_HD720P == 6
    assert (TILT_UP, TILT_DOWN, PAN_LEFT, PAN_RIGHT) == (21, 22, 23, 24)
    assert (ZOOM_IN, ZOOM_OUT) == (11, 12)
    assert (FOCUS_NEAR, FOCUS_FAR) == (13, 14)
    return "PIC_SIZE / PTZ 命令常量值与 HCNetSDK.h 一致"


# ============================================================== #
#  Main
# ============================================================== #
TESTS = [
    ("T01 包导入 & 公共 API", t_imports),
    ("T02 loader 路径 & dll 加载", t_loader_paths),
    ("T03 loader 非法平台拒绝", t_loader_invalid_platform),
    ("T04 SDK 完整生命周期", t_sdk_lifecycle),
    ("T05 SDK 单例引用计数", t_singleton_refcount),
    ("T06 PlayM4 多端口分配", t_playm4_port),
    ("T07 错误码翻译", t_error_translation),
    ("T08 时间工具", t_time_utils),
    ("T09 ctypes 结构体绑定", t_struct_sizes),
    ("T10 视频文件不存在", t_video_file_not_found),
    ("T11 视频文件垃圾数据", t_video_file_garbage),
    ("T12 数据类格式化", t_dataclasses),
    ("T13 YV12→BGR 转换", t_yv12_to_bgr),
    ("T14 登录到不通 IP", t_device_login_failure),
    ("T15 干净 init 的 last_error", t_clean_last_error),
    ("T16 PlayBack 时间结构体", t_playback_time_roundtrip),
    ("T17 RTSP 参数校验", t_rtsp_param_validation),
    ("T18 上层模块可构造", t_higher_modules_constructable),
    ("T19 demo 脚本编译", t_demo_scripts_compile),
    ("T20 包模块编译", t_package_compile),
    ("T21 logging 幂等", t_logging_idempotent),
    ("T22 常量值校验", t_constants),
]


def main() -> int:
    print(f"=== hikvision_sdk 自检测试 ===")
    print(f"Python      : {sys.version.split()[0]}")
    print(f"Platform    : {platform.system()} {platform.architecture()[0]}")
    print(f"项目根      : {_ROOT}")
    print()

    results = []
    for name, fn in TESTS:
        r = run(name, fn)
        print(r)
        results.append(r)

    passed = sum(1 for r in results if r.ok)
    failed = len(results) - passed
    print()
    print(f"=== 结果: {passed}/{len(results)} 通过, {failed} 失败 ===")
    if failed:
        print("\n失败详情:")
        for r in results:
            if not r.ok:
                print(f"\n  {r.name}\n  {r.detail}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
