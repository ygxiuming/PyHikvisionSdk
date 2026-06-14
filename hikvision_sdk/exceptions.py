# -*- coding: utf-8 -*-
"""海康 SDK 异常体系与错误码翻译。

错误码摘录自《设备网络SDK编程指南》。这里覆盖最常见的 100+ 个错误码，
未列出的错误码会以 ``未知错误(code=<n>)`` 兜底返回，并保留原始 code 字段。
"""

from __future__ import annotations

from typing import Optional


# 错误码 → 中文描述。
# 注：完整列表请参考 SDK 头文件 HCNetSDK.h 中以 NET_DVR_ 开头的常量及附带文档。
_ERROR_CODE_TABLE = {
    0: "操作成功",
    1: "用户名密码错误",
    2: "权限不足",
    3: "SDK 未初始化",
    4: "通道号错误",
    5: "连接到设备的用户数超过最大",
    6: "版本不匹配",
    7: "连接设备失败",
    8: "向设备发送失败",
    9: "从设备接收数据失败",
    10: "从设备接收数据超时",
    11: "传送的数据有误",
    12: "调用 SDK 操作失败",
    13: "调用系统 API 操作失败",
    14: "文件打开错误",
    15: "文件打开失败",
    16: "文件已经打开",
    17: "文件尚未打开",
    18: "查找文件错误",
    19: "找不到文件",
    20: "缓冲区太小",
    21: "上一次的命令还没有执行完",
    22: "用户密码输入次数过多被锁定",
    23: "数据已经存在",
    24: "数据未准备好",
    25: "用户对应的资源不存在",
    27: "设备类型不匹配",
    28: "语言不匹配",
    29: "设备未关闭",
    30: "找不到对应序列号设备",
    31: "登录到设备的用户数达到最大",
    32: "操作不支持",
    33: "命令执行失败",
    34: "创建文件失败",
    35: "网络通信错误",
    36: "设备版本不支持的命令",
    37: "命令所需要的硬件不支持",
    38: "用户已存在",
    39: "用户对应通道权限不存在",
    40: "找不到节点",
    41: "目录无效",
    42: "找不到进程",
    43: "数据正在解析",
    44: "数据未解析完",
    47: "用户不存在",
    48: "数字证书是否过期",
    49: "未授权 IP",
    50: "未注册",
    51: "用户已经登录其他设备",
    52: "解析配置文件失败",
    53: "其他错误",
    54: "客户端 IP 地址错误",
    55: "无监控点",
    56: "登录用户上限超出",
    57: "操作类型出错",
    58: "操作对象不存在",
    59: "操作通道不支持",
    60: "操作数据未准备好",
    61: "句柄关闭失败",
    62: "对应通道无录像文件",
    63: "操作不支持设备的请求",
    64: "网络繁忙",
    71: "Socket 连接错误",
    72: "Socket 监听错误",
    73: "Socket 发送错误",
    74: "Socket 接收错误",
    75: "Socket 无连接",
    76: "Socket 接收超时",
    77: "Socket 发送超时",
    78: "Socket 监听超时",
    79: "用户被列入黑名单",
    80: "设备繁忙",
    81: "解码板繁忙",
    82: "通道异常",
    84: "操作权限被禁用",
    85: "智能算法库不存在",
    86: "弱密码",
    87: "无效模式",
    91: "硬件错误",
    96: "需要双重验证",
    97: "需要单点登录",
    99: "用户被锁定",
    102: "OEM 失败",
    103: "无效授权",
    105: "时间戳过期",
    106: "重定向",
    112: "请求频次超过限制",
    113: "用户密码默认值",
    114: "码流被加密",
    115: "缺少 RSA 密钥",
    116: "RSA 密钥错误",
    400: "参数错误",
    401: "无效会话",
    402: "RTSP 服务器错误",
    410: "设备升级中",
    411: "请求超时",
    426: "需要安全验证",
}


class HikvisionError(Exception):
    """海康 SDK 调用失败时抛出的统一异常。

    Attributes:
        code: SDK 返回的错误码（NET_DVR_GetLastError 的值）。
        message: 错误描述（中文）。
        api: 触发错误的 SDK 函数名（可选，便于日志定位）。
    """

    def __init__(self, code: int, message: Optional[str] = None, api: Optional[str] = None):
        self.code = int(code)
        self.api = api
        if message is None:
            message = _ERROR_CODE_TABLE.get(self.code, f"未知错误(code={self.code})")
        self.message = message
        super().__init__(self._format())

    def _format(self) -> str:
        prefix = f"[{self.api}] " if self.api else ""
        return f"{prefix}HCNetSDK 错误 {self.code}: {self.message}"


def describe_error(code: int) -> str:
    """根据错误码返回中文描述（不抛异常，仅查询）。"""
    return _ERROR_CODE_TABLE.get(int(code), f"未知错误(code={code})")


def raise_if_failed(ok_flag: bool, sdk_handle, api: str) -> None:
    """便捷断言：当 SDK 调用失败时抛 HikvisionError。

    Args:
        ok_flag: SDK 函数返回的布尔（一般 ``True`` 代表成功）。
        sdk_handle: 已加载的 HCNetSDK ctypes 库句柄，用于查询 GetLastError。
        api: 当前调用的 API 名称，用于错误信息。
    """
    if ok_flag:
        return
    code = int(sdk_handle.NET_DVR_GetLastError())
    raise HikvisionError(code, api=api)
