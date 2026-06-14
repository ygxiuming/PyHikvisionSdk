# -*- coding: utf-8 -*-
# @Time : 2024/8/6 16:31
# @Author : sdk007

import os
import platform
import re
from ctypes import *
from enum import Enum


def system_get_platform_info():
    sys_platform = platform.system().lower().strip()
    python_bit = platform.architecture()[0]
    python_bit_num = re.findall(r'(\d+)\w*', python_bit)[0]
    return sys_platform, python_bit_num


sys_platform, python_bit_num = system_get_platform_info()
system_type = sys_platform + python_bit_num

if sys_platform == 'linux':
    load_library = cdll.LoadLibrary
    fun_ctype = CFUNCTYPE
elif sys_platform == 'windows':
    load_library = windll.LoadLibrary
    fun_ctype = WINFUNCTYPE
else:
    print("************涓嶆敮鎸佺殑骞冲彴**************")
    exit(0)

# ---------------------------------------------------------------------------
# 路径解析说明：
# 原始官方 Demo 把 .dll/.so 放在与本文件同级的 ./lib/ 目录中。
# 本项目把所有运行时统一收纳到工程根目录下的 sdk/win 与 sdk/linux 中，
# 由 hikvision_sdk._bindings.loader 模块根据当前操作系统组装绝对路径。
# 因此这里不再硬编码路径，而是从 loader 中获取。
# ---------------------------------------------------------------------------
from hikvision_sdk._bindings.loader import resolve_netsdk_dll_path as _resolve_netsdk_dll_path  # noqa: E402

netsdkdllpath = _resolve_netsdk_dll_path(system_type)

C_LLONG_DICT = {'windows64': c_longlong, 'windows32': c_long, 'linux32': c_long, 'linux64': c_long}
C_LONG_DICT = {'windows64': c_long, 'windows32': c_long, 'linux32': c_int, 'linux64': c_int}
C_LDWORD_DICT = {'windows64': c_longlong, 'windows32': c_ulong, 'linux32': c_long, 'linux64': c_long}
C_DWORD_DICT = {'windows64': c_ulong, 'windows32': c_ulong, 'linux32': c_uint, 'linux64': c_uint}
C_HWND_DICT = {'windows64': c_void_p, 'windows32': c_void_p, 'linux32': c_uint, 'linux64': c_uint}

C_LLONG = C_LLONG_DICT[system_type]
C_LONG = C_LONG_DICT[system_type]
C_LDWORD = C_LDWORD_DICT[system_type]
C_DWORD = C_DWORD_DICT[system_type]
# C_BOOL = c_int
# C_UINT = c_uint
# C_BYTE = c_ubyte
# C_ENUM = c_int

C_HWND = C_HWND_DICT[system_type]
C_WORD = c_ushort
C_USHORT = c_ushort
C_SHORT = c_short
# C_LONG = c_int
C_BYTE = c_ubyte
C_UINT = c_uint
C_LPVOID = c_void_p
C_HANDLE = c_void_p
C_LPDWORD = POINTER(c_uint)
C_UINT64 = c_ulonglong
C_INT64 = c_longlong
C_BOOL = c_int

NET_DVR_GET_NETCFG = 102  # 鑾峰彇缃戠粶鍙傛暟
NET_DVR_GET_NETCFG_V50 = 1015  # 鑾峰彇缃戠粶鍙傛暟
NET_DVR_SET_NETCFG_V50 = 1016  # 璁剧疆缃戠粶鍙傛暟

# 鐮佹祦鍥炶皟鏁版嵁绫诲瀷
NET_DVR_SYSHEAD = 1
NET_DVR_STREAMDATA = 2
NET_DVR_AUDIOSTREAMDATA = 3
NET_DVR_PRIVATE_DATA = 112


# 鏋氫妇瀹氫箟
# SDK鏈湴鍙傛暟绫诲瀷鏋氫妇
class NET_SDK_LOCAL_CFG_TYPE(Enum):
    NET_SDK_LOCAL_CFG_TYPE_TCP_PORT_BIND = 0  # 鏈湴TCP绔彛缁戝畾閰嶇疆锛屽搴旂粨鏋勪綋NET_DVR_LOCAL_TCP_PORT_BIND_CFG
    NET_SDK_LOCAL_CFG_TYPE_UDP_PORT_BIND = 1  # 鏈湴UDP绔彛缁戝畾閰嶇疆锛屽搴旂粨鏋勪綋NET_DVR_LOCAL_UDP_PORT_BIND_CFG
    NET_SDK_LOCAL_CFG_TYPE_MEM_POOL = 2  # 鍐呭瓨姹犳湰鍦伴厤缃紝瀵瑰簲缁撴瀯浣揘ET_DVR_LOCAL_MEM_POOL_CFG
    NET_SDK_LOCAL_CFG_TYPE_MODULE_RECV_TIMEOUT = 3  # 鎸夋ā鍧楅厤缃秴鏃舵椂闂达紝瀵瑰簲缁撴瀯浣揘ET_DVR_LOCAL_MODULE_RECV_TIMEOUT_CFG
    NET_SDK_LOCAL_CFG_TYPE_ABILITY_PARSE = 4  # 鏄惁浣跨敤鑳藉姏闆嗚В鏋愬簱锛屽搴旂粨鏋勪綋NET_DVR_LOCAL_ABILITY_PARSE_CFG
    NET_SDK_LOCAL_CFG_TYPE_TALK_MODE = 5  # 瀵硅妯″紡锛屽搴旂粨鏋勪綋NET_DVR_LOCAL_TALK_MODE_CFG
    NET_SDK_LOCAL_CFG_TYPE_PROTECT_KEY = 6  # 瀵嗛挜璁剧疆锛屽搴旂粨鏋勪綋NET_DVR_LOCAL_PROTECT_KEY_CFG
    NET_SDK_LOCAL_CFG_TYPE_CFG_VERSION = 7  # 鐢ㄤ簬娴嬭瘯鐗堟湰澶寸殑璁惧绔吋瀹规儏NET_DVR_LOCAL_MEM_POOL_CFG鍐? 鍙湁鍦ㄨ缃弬鏁版椂鎵嶈捣浣滅敤銆?
    NET_SDK_LOCAL_CFG_TYPE_RTSP_PARAMS = 8  # rtsp鍙傛暟閰嶇疆锛屽浜庣粨鏋勪綋NET_DVR_RTSP_PARAMS_CFG
    NET_SDK_LOCAL_CFG_TYPE_SIMXML_LOGIN = 9  # 鍦ㄧ櫥褰曟椂浣跨敤妯℃嫙鑳藉姏琛ュ厖support瀛楁, 瀵瑰簲缁撴瀯NET_DVR_SIMXML_LOGIN
    NET_SDK_LOCAL_CFG_TYPE_CHECK_DEV = 10  # 蹇冭烦浜や簰闂撮殧鏃堕棿
    NET_SDK_LOCAL_CFG_TYPE_SECURITY = 11  # SDK鏈瀹夊叏閰嶇疆锛?
    NET_SDK_LOCAL_CFG_TYPE_EZVIZLIB_PATH = 12  # 閰嶇疆钀ょ煶浜戦€氫俊搴撳湴鍧€锛?
    NET_SDK_LOCAL_CFG_TYPE_CHAR_ENCODE = 13  # 13.閰嶇疆瀛楃缂栫爜鐩稿叧澶勭悊鍥炶皟
    NET_SDK_LOCAL_CFG_TYPE_PROXYS = 14  # 璁剧疆鑾峰彇浠?
    NET_DVR_LOCAL_CFG_TYPE_LOG = 15  # 鏃ュ織鍙傛暟閰嶇疆  NET_DVR_LOCAL_LOG_CFG
    NET_DVR_LOCAL_CFG_TYPE_STREAM_CALLBACK = 16  # 鐮佹祦鍥炶皟鍙傛暟閰嶇疆 NET_DVR_LOCAL_STREAM_CALLBACK_CFG
    NET_DVR_LOCAL_CFG_TYPE_GENERAL = 17  # 閫氱敤鍙傛暟閰嶇疆 NET_DVR_LOCAL_GENERAL_CFG
    NET_DVR_LOCAL_CFG_TYPE_PTZ = 17  # PTZ鏄惁鎺ユ敹璁惧杩斿洖閰嶇疆
    NET_DVR_LOCAL_CFG_MESSAGE_CALLBACK_V51 = 19  # 鎶ヨV51鍥炶皟鐩稿叧鏈湴閰嶇疆,瀵瑰簲缁撴瀯浣撲负NET_DVR_MESSAGE_CALLBACK_PARAM_V51 銆?浠呭NET_DVR_SetDVRMessageCallBack_V51浠ヤ笂鐗堟湰鏈夋晥)
    NET_SDK_LOCAL_CFG_CERTIFICATION = 20  # 閰嶇疆鍜岃瘉涔︾浉鍏崇殑鍙傛暟锛屽搴旂粨鏋勪綋缁撴瀯浣揘ET_DVR_LOCAL_CERTIFICATION
    NET_SDK_LOCAL_CFG_PORT_MULTIPLEX = 21  # 绔彛澶嶇敤锛屽搴旂粨鏋勪綋NET_DVR_LOCAL_PORT_MULTI_CFG
    NET_SDK_LOCAL_CFG_ASYNC = 22  # 寮傛閰嶇疆锛屽搴旂粨鏋勪綋NET_DVR_LOCAL_ASYNC_CFG
    NET_SDK_P2P_LOGIN_2C = 23
    NET_SDK_P2P_LOGIN_2B = 24
    NET_SDK_P2P_LOGOUT = 25
    NET_SDK_AUDIOCAST_CFG = 26  # 閰嶇疆骞挎挱閲囨牱鐜?,瀵瑰簲缁撴瀯浣揘ET_LOCAL_AUDIOCAST_CFG


# 璁剧疆SDK鍒濆鍖栧弬鏁扮被鍨嬫灇涓?
class NET_SDK_INIT_CFG_TYPE(Enum):
    NET_SDK_INIT_CFG_TYPE_CHECK_MODULE_COM = 0  # 澧炲姞瀵瑰繀椤诲簱鐨勬鏌?
    NET_SDK_INIT_CFG_ABILITY = 1  # sdk鏀寔鐨勪笟鍔＄殑鑳藉姏闆?
    NET_SDK_INIT_CFG_SDK_PATH = 2  # 璁剧疆HCNetSDK搴撴墍鍦ㄧ洰褰?
    NET_SDK_INIT_CFG_LIBEAY_PATH = 3  # 璁剧疆OpenSSL鐨刲ibeay32.dll/libcrypto.so/libcrypto.dylib鎵€鍦ㄨ矾寰?
    NET_SDK_INIT_CFG_SSLEAY_PATH = 4  # 璁剧疆OpenSSL鐨剆sleay32.dll/libssl.so/libssl.dylib鎵€鍦ㄨ矾寰?


# 浜嬩欢绫诲瀷鏋氫妇
class ALARM_LCOMMAND_ENUM(Enum):
    COMM_ALARM_ACS = 0x5002  # 闂ㄧ涓绘満鎶ヨ淇℃伅,瀵瑰簲鏁版嵁绫诲瀷缁撴瀯浣擄細NET_DVR_ACS_ALARM_INFO
    COMM_ID_INFO_ALARM = 0x5200  # 闂ㄧ韬唤璇佸埛鍗′俊鎭?瀵瑰簲鏁版嵁绫诲瀷缁撴瀯浣擄細NET_DVR_ID_CARD_INFO_ALARM
    COMM_ALARM_V30 = 0x4000  # 绉诲姩渚︽祴銆佽棰戜涪澶便€侀伄鎸°€両O淇″彿閲忕瓑鎶ヨ淇℃伅(V3.0浠ヤ笂鐗堟湰鏀寔鐨勮澶?,瀵瑰簲鏁版嵁绫诲瀷缁撴瀯浣擄細NET_DVR_ALARMINFO_V30
    COMM_ISAPI_ALARM = 0x6009  # 鏅鸿兘妫€娴嬫姤璀?灏佽缁撴瀯浣擄紝鍥剧墖鏁版嵁鍒嗙),瀵瑰簲鏁版嵁绫诲瀷缁撴瀯浣擄細NET_DVR_ALARM_ISAPI_INFO
    COMM_UPLOAD_FACESNAP_RESULT = 0x1112  # 浜鸿劯鎶撴媿缁撴灉淇℃伅,瀵瑰簲鏁版嵁绫诲瀷缁撴瀯浣擄細NET_VCA_FACESNAP_RESULT
    COMM_SNAP_MATCH_ALARM = 0x2902  # 浜鸿劯姣斿缁撴灉淇℃伅,瀵瑰簲鏁版嵁绫诲瀷缁撴瀯浣擄細NET_VCA_FACESNAP_MATCH_ALARM


# 璁惧鍙傛暟缁撴瀯浣?V30
class NET_DVR_DEVICEINFO_V30(Structure):
    _fields_ = [
        ("sSerialNumber", C_BYTE * 48),  # 搴忓垪鍙?
        ("byAlarmInPortNum", C_BYTE),  # 妯℃嫙鎶ヨ杈撳叆涓暟
        ("byAlarmOutPortNum", C_BYTE),  # 妯℃嫙鎶ヨ杈撳嚭涓暟
        ("byDiskNum", C_BYTE),  # 纭洏涓暟
        ("byDVRType", C_BYTE),  # 璁惧绫诲瀷
        ("byChanNum", C_BYTE),  # 璁惧妯℃嫙閫氶亾涓暟锛屾暟瀛楋紙IP锛夐€氶亾鏈€澶т釜鏁颁负byIPChanNum + byHighDChanNum*256
        ("byStartChan", C_BYTE),  # 妯℃嫙閫氶亾鐨勮捣濮嬮€氶亾鍙凤紝浠?寮€濮嬨€傛暟瀛楅€氶亾鐨勮捣濮嬮€氶亾鍙疯涓嬮潰鍙傛暟byStartDChan
        ("byAudioChanNum", C_BYTE),  # 璁惧璇煶瀵硅閫氶亾鏁?
        ("byIPChanNum", C_BYTE),  # 璁惧鏈€澶ф暟瀛楅€氶亾涓暟锛屼綆8浣嶏紝楂?浣嶈byHighDChanNum
        ("byZeroChanNum", C_BYTE),  # 闆堕€氶亾缂栫爜涓暟
        ("byMainProto", C_BYTE),  # 涓荤爜娴佷紶杈撳崗璁被鍨嬶細0- private锛?- rtsp锛?- 鍚屾椂鏀寔绉佹湁鍗忚鍜宺tsp鍗忚鍙栨祦锛堥粯璁ら噰鐢ㄧ鏈夊崗璁彇娴侊級
        ("bySubProto", C_BYTE),  # 瀛愮爜娴佷紶杈撳崗璁被鍨嬶細0- private锛?- rtsp锛?- 鍚屾椂鏀寔绉佹湁鍗忚鍜宺tsp鍗忚鍙栨祦锛堥粯璁ら噰鐢ㄧ鏈夊崗璁彇娴侊級
        ("bySupport", C_BYTE),  # 鑳藉姏锛屼綅涓庣粨鏋滀负0琛ㄧず涓嶆敮鎸侊紝1琛ㄧず鏀寔
        # bySupport & 0x1锛岃〃绀烘槸鍚︽敮鎸佹櫤鑳芥悳绱?
        # bySupport & 0x2锛岃〃绀烘槸鍚︽敮鎸佸浠?
        # bySupport & 0x4锛岃〃绀烘槸鍚︽敮鎸佸帇缂╁弬鏁拌兘鍔涜幏鍙?
        # bySupport & 0x8, 琛ㄧず鏄惁鏀寔鍙岀綉鍗?
        # bySupport & 0x10, 琛ㄧず鏀寔杩滅▼SADP
        # bySupport & 0x20, 琛ㄧず鏀寔Raid鍗″姛鑳?
        # bySupport & 0x40, 琛ㄧず鏀寔IPSAN鐩綍鏌ユ壘
        # bySupport & 0x80, 琛ㄧず鏀寔rtp over rtsp
        ("bySupport1", C_BYTE),  # 鑳藉姏闆嗘墿鍏咃紝浣嶄笌缁撴灉涓?琛ㄧず涓嶆敮鎸侊紝1琛ㄧず鏀寔
        # bySupport1 & 0x1, 琛ㄧず鏄惁鏀寔snmp v30
        # bySupport1 & 0x2, 琛ㄧず鏄惁鏀寔鍖哄垎鍥炴斁鍜屼笅杞?
        # bySupport1 & 0x4, 琛ㄧず鏄惁鏀寔甯冮槻浼樺厛绾?
        # bySupport1 & 0x8, 琛ㄧず鏅鸿兘璁惧鏄惁鏀寔甯冮槻鏃堕棿娈垫墿灞?
        # bySupport1 & 0x10,琛ㄧず鏄惁鏀寔澶氱鐩樻暟锛堣秴杩?3涓級
        # bySupport1 & 0x20,琛ㄧず鏄惁鏀寔rtsp over http
        # bySupport1 & 0x80,琛ㄧず鏄惁鏀寔杞︾墝鏂版姤璀︿俊鎭紝涓旇繕琛ㄧず鏄惁鏀寔NET_DVR_IPPARACFG_V40閰嶇疆
        ("bySupport2", C_BYTE),  # 鑳藉姏闆嗘墿鍏咃紝浣嶄笌缁撴灉涓?琛ㄧず涓嶆敮鎸侊紝1琛ㄧず鏀寔
        # bySupport2 & 0x1, 琛ㄧず瑙ｇ爜鍣ㄦ槸鍚︽敮鎸侀€氳繃URL鍙栨祦瑙ｇ爜
        # bySupport2 & 0x2, 琛ㄧず鏄惁鏀寔FTPV40
        # bySupport2 & 0x4, 琛ㄧず鏄惁鏀寔ANR(鏂綉褰曞儚)
        # bySupport2 & 0x20, 琛ㄧず鏄惁鏀寔鍗曠嫭鑾峰彇璁惧鐘舵€佸瓙椤?
        # bySupport2 & 0x40, 琛ㄧず鏄惁鏄爜娴佸姞瀵嗚澶?
        ("wDevType", C_WORD),  # 璁惧鍨嬪彿锛岃瑙佷笅鏂囧垪琛?
        ("bySupport3", C_BYTE),  # 鑳藉姏闆嗘墿灞曪紝浣嶄笌缁撴灉锛?- 涓嶆敮鎸侊紝1- 鏀寔
        # bySupport3 & 0x1, 琛ㄧず鏄惁鏀寔澶氱爜娴?
        # bySupport3 & 0x4, 琛ㄧず鏄惁鏀寔鎸夌粍閰嶇疆锛屽叿浣撳寘鍚€氶亾鍥惧儚鍙傛暟銆佹姤璀﹁緭鍏ュ弬鏁般€両P鎶ヨ杈撳叆/杈撳嚭鎺ュ叆鍙傛暟銆佺敤鎴峰弬鏁般€佽澶囧伐浣滅姸鎬併€丣PEG鎶撳浘銆佸畾鏃跺拰鏃堕棿鎶撳浘銆佺‖鐩樼洏缁勭鐞嗙瓑
        # bySupport3 & 0x20, 琛ㄧず鏄惁鏀寔閫氳繃DDNS鍩熷悕瑙ｆ瀽鍙栨祦
        ("byMultiStreamProto", C_BYTE),  # 鏄惁鏀寔澶氱爜娴侊紝鎸変綅琛ㄧず锛屼綅涓庣粨鏋滐細0-涓嶆敮鎸侊紝1-鏀寔
        # byMultiStreamProto & 0x1, 琛ㄧず鏄惁鏀寔鐮佹祦3
        # byMultiStreamProto & 0x2, 琛ㄧず鏄惁鏀寔鐮佹祦4
        # byMultiStreamProto & 0x40,琛ㄧず鏄惁鏀寔涓荤爜娴?
        # byMultiStreamProto & 0x80,琛ㄧず鏄惁鏀寔瀛愮爜娴?
        ("byStartDChan", C_BYTE),  # 璧峰鏁板瓧閫氶亾鍙凤紝0琛ㄧず鏃犳暟瀛楅€氶亾锛屾瘮濡侱VR鎴朓PC
        ("byStartDTalkChan", C_BYTE),  # 璧峰鏁板瓧瀵硅閫氶亾鍙凤紝鍖哄埆浜庢ā鎷熷璁查€氶亾鍙凤紝0琛ㄧず鏃犳暟瀛楀璁查€氶亾
        ("byHighDChanNum", C_BYTE),  # 鏁板瓧閫氶亾涓暟锛岄珮8浣?
        ("bySupport4", C_BYTE),  # 鑳藉姏闆嗘墿灞曪紝鎸変綅琛ㄧず锛屼綅涓庣粨鏋滐細0- 涓嶆敮鎸侊紝1- 鏀寔
        # bySupport4 & 0x01, 琛ㄧず鏄惁鎵€鏈夌爜娴佺被鍨嬪悓鏃舵敮鎸丷TSP鍜岀鏈夊崗璁?
        # bySupport4 & 0x10, 琛ㄧず鏄惁鏀寔鍩熷悕鏂瑰紡鎸傝浇缃戠粶纭洏
        ("byLanguageType", C_BYTE),  # 鏀寔璇鑳藉姏锛屾寜浣嶈〃绀猴紝浣嶄笌缁撴灉锛?- 涓嶆敮鎸侊紝1- 鏀寔
        # byLanguageType ==0锛岃〃绀鸿€佽澶囷紝涓嶆敮鎸佽瀛楁
        # byLanguageType & 0x1锛岃〃绀烘槸鍚︽敮鎸佷腑鏂?
        # byLanguageType & 0x2锛岃〃绀烘槸鍚︽敮鎸佽嫳鏂?
        ("byVoiceInChanNum", C_BYTE),  # 闊抽杈撳叆閫氶亾鏁?
        ("byStartVoiceInChanNo", C_BYTE),  # 闊抽杈撳叆璧峰閫氶亾鍙凤紝0琛ㄧず鏃犳晥
        ("bySupport5", C_BYTE),  # 鎸変綅琛ㄧず,0-涓嶆敮鎸?1-鏀寔,bit0-鏀寔澶氱爜娴?
        ("bySupport6", C_BYTE),  # 鎸変綅琛ㄧず,0-涓嶆敮鎸?1-鏀寔
        # bySupport6 & 0x1  琛ㄧず璁惧鏄惁鏀寔鍘嬬缉
        # bySupport6 & 0x2  琛ㄧず鏄惁鏀寔娴両D鏂瑰紡閰嶇疆娴佹潵婧愭墿灞曞懡浠わ紝DVR_SET_STREAM_SRC_INFO_V40
        # bySupport6 & 0x4  琛ㄧず鏄惁鏀寔浜嬩欢鎼滅储V40鎺ュ彛
        # bySupport6 & 0x8  琛ㄧず鏄惁鏀寔鎵╁睍鏅鸿兘渚︽祴閰嶇疆鍛戒护
        # bySupport6 & 0x40 琛ㄧず鍥剧墖鏌ヨ缁撴灉V40鎵╁睍
        ("byMirrorChanNum", C_BYTE),  # 闀滃儚閫氶亾涓暟锛屽綍鎾富鏈轰腑鐢ㄤ簬琛ㄧず瀵兼挱閫氶亾
        ("wStartMirrorChanNo", C_WORD),  # 璧峰闀滃儚閫氶亾鍙?
        ("bySupport7", C_BYTE),  # 鑳藉姏,鎸変綅琛ㄧず,0-涓嶆敮鎸?1-鏀寔
        # bySupport7 & 0x1  琛ㄧず璁惧鏄惁鏀寔NET_VCA_RULECFG_V42鎵╁睍
        # bySupport7 & 0x2  琛ㄧず璁惧鏄惁鏀寔IPC HVT 妯″紡鎵╁睍
        # bySupport7 & 0x04 琛ㄧず璁惧鏄惁鏀寔杩斿洖閿佸畾鏃堕棿
        # bySupport7 & 0x08 琛ㄧず璁剧疆浜戝彴PTZ浣嶇疆鏃讹紝鏄惁鏀寔甯﹂€氶亾鍙?
        # bySupport7 & 0x10 琛ㄧず璁惧鏄惁鏀寔鍙岀郴缁熷崌绾у浠?
        # bySupport7 & 0x20 琛ㄧず璁惧鏄惁鏀寔OSD瀛楃鍙犲姞V50
        # bySupport7 & 0x40 琛ㄧず璁惧鏄惁鏀寔涓讳粠锛堜粠鎽勫儚鏈猴級
        # bySupport7 & 0x80 琛ㄧず璁惧鏄惁鏀寔鎶ユ枃鍔犲瘑
        ("byRes2", C_BYTE)]  # 淇濈暀锛岀疆涓?


LPNET_DVR_DEVICEINFO_V30 = POINTER(NET_DVR_DEVICEINFO_V30)


# 璁惧鍙傛暟缁撴瀯浣?V40
class NET_DVR_DEVICEINFO_V40(Structure):
    _fields_ = [
        ('struDeviceV30', NET_DVR_DEVICEINFO_V30),  # 璁惧淇℃伅
        ('bySupportLock', C_BYTE),  # 璁惧鏀寔閿佸畾鍔熻兘锛岃瀛楁鐢盨DK鏍规嵁璁惧杩斿洖鍊兼潵璧嬪€肩殑銆俠ySupportLock涓?鏃讹紝dwSurplusLockTime鍜宐yRetryLoginTime鏈夋晥
        ('byRetryLoginTime', C_BYTE),  # 鍓╀綑鍙皾璇曠櫥闄嗙殑娆℃暟锛岀敤鎴峰悕锛屽瘑鐮侀敊璇椂锛屾鍙傛暟鏈夋晥
        ('byPasswordLevel', C_BYTE),  # admin瀵嗙爜瀹夊叏绛夌骇
        ('byProxyType', C_BYTE),  # 浠ｇ悊绫诲瀷锛?-涓嶄娇鐢ㄤ唬鐞? 1-浣跨敤socks5浠ｇ悊, 2-浣跨敤EHome浠ｇ悊
        ('dwSurplusLockTime', C_DWORD),  # 鍓╀綑鏃堕棿锛屽崟浣嶇锛岀敤鎴烽攣瀹氭椂锛屾鍙傛暟鏈夋晥
        ('byCharEncodeType', C_BYTE),  # 瀛楃缂栫爜绫诲瀷
        ('bySupportDev5', C_BYTE),  # 鏀寔v50鐗堟湰鐨勮澶囧弬鏁拌幏鍙栵紝璁惧鍚嶇О鍜岃澶囩被鍨嬪悕绉伴暱搴︽墿灞曚负64瀛楄妭
        ('bySupport', C_BYTE),  # 鑳藉姏闆嗘墿灞曪紝浣嶄笌缁撴灉锛?- 涓嶆敮鎸侊紝1- 鏀寔
        ('byLoginMode', C_BYTE),  # 鐧诲綍妯″紡:0- Private鐧诲綍锛?- ISAPI鐧诲綍
        ('dwOEMCode', C_DWORD),  # OEM Code
        ('iResidualValidity', C_LONG),  # 璇ョ敤鎴峰瘑鐮佸墿浣欐湁鏁堝ぉ鏁帮紝鍗曚綅锛氬ぉ锛岃繑鍥炶礋鍊硷紝琛ㄧず瀵嗙爜宸茬粡瓒呮湡浣跨敤锛屼緥濡傗€?3琛ㄧず瀵嗙爜宸茬粡瓒呮湡浣跨敤3澶┾€?
        ('byResidualValidity', C_BYTE),  # iResidualValidity瀛楁鏄惁鏈夋晥锛?-鏃犳晥锛?-鏈夋晥
        ('bySingleStartDTalkChan', C_BYTE),  # 鐙珛闊宠建鎺ュ叆鐨勮澶囷紝璧峰鎺ュ叆閫氶亾鍙凤紝0-涓轰繚鐣欏瓧鑺傦紝鏃犲疄闄呭惈涔夛紝闊宠建閫氶亾鍙蜂笉鑳戒粠0寮€濮?
        ('bySingleDTalkChanNums', C_BYTE),  # 鐙珛闊宠建鎺ュ叆鐨勮澶囩殑閫氶亾鎬绘暟锛?-琛ㄧず涓嶆敮鎸?
        ('byPassWordResetLevel', C_BYTE),  # 0-鏃犳晥锛?
        # 1- 绠＄悊鍛樺垱寤轰竴涓潪绠＄悊鍛樼敤鎴蜂负鍏惰缃瘑鐮侊紝璇ラ潪绠＄悊鍛樼敤鎴锋纭櫥褰曡澶囧悗瑕佹彁绀衡€滆淇敼鍒濆鐧诲綍瀵嗙爜鈥濓紝鏈慨鏀圭殑鎯呭喌涓嬶紝鐢ㄦ埛姣忔鐧诲叆閮戒細杩涜鎻愰啋锛?
        # 2- 褰撻潪绠＄悊鍛樼敤鎴风殑瀵嗙爜琚鐞嗗憳淇敼锛岃闈炵鐞嗗憳鐢ㄦ埛鍐嶆姝ｇ‘鐧诲綍璁惧鍚庯紝闇€瑕佹彁绀衡€滆閲嶆柊璁剧疆鐧诲綍瀵嗙爜鈥濓紝鏈慨鏀圭殑鎯呭喌涓嬶紝鐢ㄦ埛姣忔鐧诲叆閮戒細杩涜鎻愰啋銆?
        ('bySupportStreamEncrypt', C_BYTE),  # 鑳藉姏闆嗘墿灞曪紝浣嶄笌缁撴灉锛?- 涓嶆敮鎸侊紝1- 鏀寔
        # bySupportStreamEncrypt & 0x1 琛ㄧず鏄惁鏀寔RTP/TLS鍙栨祦
        # bySupportStreamEncrypt & 0x2 琛ㄧず鏄惁鏀寔SRTP/UDP鍙栨祦
        # bySupportStreamEncrypt & 0x4 琛ㄧず鏄惁鏀寔SRTP/MULTICAST鍙栨祦
        ('byMarketType', C_BYTE),  # 0-鏃犳晥锛堟湭鐭ョ被鍨嬶級,1-缁忛攢鍨嬶紝2-琛屼笟鍨?
        ('byRes2', C_BYTE * 238)  # 淇濈暀锛岀疆涓?
    ]


LPNET_DVR_DEVICEINFO_V40 = POINTER(NET_DVR_DEVICEINFO_V40)

# 寮傛鐧诲綍鍥炶皟鍑芥暟
fLoginResultCallBack = fun_ctype(None, C_LONG, C_DWORD, LPNET_DVR_DEVICEINFO_V30, c_void_p)


# NET_DVR_Login_V40()鍙傛暟
class NET_DVR_USER_LOGIN_INFO(Structure):
    _fields_ = [
        ("sDeviceAddress", c_char * 129),  # 璁惧鍦板潃锛孖P 鎴栬€呮櫘閫氬煙鍚?
        ("byUseTransport", C_BYTE),  # 鏄惁鍚敤鑳藉姏闆嗛€忎紶锛?- 涓嶅惎鐢ㄩ€忎紶锛岄粯璁わ紱1- 鍚敤閫忎紶
        ("wPort", C_WORD),  # 璁惧绔彛鍙凤紝渚嬪锛?000
        ("sUserName", c_char * 64),  # 鐧诲綍鐢ㄦ埛鍚嶏紝渚嬪锛歛dmin
        ("sPassword", c_char * 64),  # 鐧诲綍瀵嗙爜锛屼緥濡傦細12345
        ("cbLoginResult", fLoginResultCallBack),  # 鐧诲綍鐘舵€佸洖璋冨嚱鏁帮紝bUseAsynLogin 涓?鏃舵湁鏁?
        ("pUser", C_LPVOID),  # 鐢ㄦ埛鏁版嵁
        ("bUseAsynLogin", C_DWORD),  # 鏄惁寮傛鐧诲綍锛?- 鍚︼紝1- 鏄?
        ("byProxyType", C_BYTE),  # 0:涓嶄娇鐢ㄤ唬鐞嗭紝1锛氫娇鐢ㄦ爣鍑嗕唬鐞嗭紝2锛氫娇鐢‥Home浠ｇ悊
        ("byUseUTCTime", C_BYTE),
        # 0-涓嶈繘琛岃浆鎹紝榛樿,1-鎺ュ彛涓婅緭鍏ヨ緭鍑哄叏閮ㄤ娇鐢║TC鏃堕棿,SDK瀹屾垚UTC鏃堕棿涓庤澶囨椂鍖虹殑杞崲,2-鎺ュ彛涓婅緭鍏ヨ緭鍑哄叏閮ㄤ娇鐢ㄥ钩鍙版湰鍦版椂闂达紝SDK瀹屾垚骞冲彴鏈湴鏃堕棿涓庤澶囨椂鍖虹殑杞崲
        ("byLoginMode", C_BYTE),  # 0-Private 1-ISAPI 2-鑷€傚簲
        ("byHttps", C_BYTE),  # 0-涓嶉€傜敤tls锛?-浣跨敤tls 2-鑷€傚簲
        ("iProxyID", C_DWORD),  # 浠ｇ悊鏈嶅姟鍣ㄥ簭鍙凤紝娣诲姞浠ｇ悊鏈嶅姟鍣ㄤ俊鎭椂锛岀浉瀵瑰簲鐨勬湇鍔″櫒鏁扮粍涓嬭〃鍊?
        ("byVerifyMode", C_BYTE),  # 璁よ瘉鏂瑰紡锛?-涓嶈璇侊紝1-鍙屽悜璁よ瘉锛?-鍗曞悜璁よ瘉锛涜璇佷粎鍦ㄤ娇鐢═LS鐨勬椂鍊欑敓鏁?
        ("byRes2", C_BYTE * 119)]


LPNET_DVR_USER_LOGIN_INFO = POINTER(NET_DVR_USER_LOGIN_INFO)


# 缁勪欢搴撳姞杞借矾寰勪俊鎭?
class NET_DVR_LOCAL_SDK_PATH(Structure):
    _fields_ = [
        ('sPath', c_char * 256),  # 缁勪欢搴撳湴鍧€
        ('byRes', C_BYTE * 128),
    ]


LPNET_DVR_LOCAL_SDK_PATH = POINTER(NET_DVR_LOCAL_SDK_PATH)


# 鎶ヨ璁惧淇℃伅缁撴瀯浣?
class NET_DVR_ALARMER(Structure):
    _fields_ = [
        ("byUserIDValid", C_BYTE),  # UserID鏄惁鏈夋晥 0-鏃犳晥锛?-鏈夋晥
        ("bySerialValid", C_BYTE),  # 搴忓垪鍙锋槸鍚︽湁鏁?0-鏃犳晥锛?-鏈夋晥
        ("byVersionValid", C_BYTE),  # 鐗堟湰鍙锋槸鍚︽湁鏁?0-鏃犳晥锛?-鏈夋晥
        ("byDeviceNameValid", C_BYTE),  # 璁惧鍚嶅瓧鏄惁鏈夋晥 0-鏃犳晥锛?-鏈夋晥
        ("byMacAddrValid", C_BYTE),  # MAC鍦板潃鏄惁鏈夋晥 0-鏃犳晥锛?-鏈夋晥
        ("byLinkPortValid", C_BYTE),  # login绔彛鏄惁鏈夋晥 0-鏃犳晥锛?-鏈夋晥
        ("byDeviceIPValid", C_BYTE),  # 璁惧IP鏄惁鏈夋晥 0-鏃犳晥锛?-鏈夋晥
        ("bySocketIPValid", C_BYTE),  # socket ip鏄惁鏈夋晥 0-鏃犳晥锛?-鏈夋晥
        ("lUserID", C_LONG),  # NET_DVR_Login()杩斿洖鍊? 甯冮槻鏃舵湁鏁?
        ("sSerialNumber", C_BYTE * 48),  # 搴忓垪鍙?
        ("dwDeviceVersion", C_DWORD),  # 鐗堟湰淇℃伅 楂?6浣嶈〃绀轰富鐗堟湰锛屼綆16浣嶈〃绀烘鐗堟湰
        ("sDeviceName", C_BYTE * 32),  # 璁惧鍚嶅瓧
        ("byMacAddr", C_BYTE * 6),  # MAC鍦板潃
        ("wLinkPort", C_WORD),  # link port
        ("sDeviceIP", C_BYTE * 128),  # IP鍦板潃
        ("sSocketIP", C_BYTE * 128),  # 鎶ヨ涓诲姩涓婁紶鏃剁殑socket IP鍦板潃
        ("byIpProtocol", C_BYTE),  # Ip鍗忚 0-IPV4, 1-IPV6
        ("byRes2", C_BYTE * 11)]


LPNET_DVR_ALARMER = POINTER(NET_DVR_ALARMER)


# 鎶ヨ甯冮槻鍙傛暟缁撴瀯浣?
class NET_DVR_SETUPALARM_PARAM(Structure):
    _fields_ = [
        ("dwSize", C_DWORD),  # 缁撴瀯浣撳ぇ灏?
        ("byLevel", C_BYTE),  # 甯冮槻浼樺厛绾э細0- 涓€绛夌骇锛堥珮锛夛紝1- 浜岀瓑绾э紙涓級锛?- 涓夌瓑绾э紙浣庯級
        ("byAlarmInfoType", C_BYTE),
        # 涓婁紶鎶ヨ淇℃伅绫诲瀷锛堟姄鎷嶆満鏀寔锛夛紝0-鑰佹姤璀︿俊鎭紙NET_DVR_PLATE_RESULT锛夛紝1-鏂版姤璀︿俊鎭?NET_ITS_PLATE_RESULT)2012-9-28
        ("byRetAlarmTypeV40", C_BYTE),
        # 0- 杩斿洖NET_DVR_ALARMINFO_V30鎴朜ET_DVR_ALARMINFO,
        # 1- 璁惧鏀寔NET_DVR_ALARMINFO_V40鍒欒繑鍥濶ET_DVR_ALARMINFO_V40锛屼笉鏀寔鍒欒繑鍥濶ET_DVR_ALARMINFO_V30鎴朜ET_DVR_ALARMINFO
        ("byRetDevInfoVersion", C_BYTE),  # CVR涓婁紶鎶ヨ淇℃伅鍥炶皟缁撴瀯浣撶増鏈彿 0-COMM_ALARM_DEVICE锛?1-COMM_ALARM_DEVICE_V40
        ("byRetVQDAlarmType", C_BYTE),  # VQD鎶ヨ涓婁紶绫诲瀷锛?-涓婁紶鎶ユ姤璀ET_DVR_VQD_DIAGNOSE_INFO锛?-涓婁紶鎶ヨNET_DVR_VQD_ALARM
        ("byFaceAlarmDetection", C_BYTE),
        ("bySupport", C_BYTE),
        ("byBrokenNetHttp", C_BYTE),
        ("wTaskNo", C_WORD),
        # 浠诲姟澶勭悊鍙?鍜?(涓婁紶鏁版嵁NET_DVR_VEHICLE_RECOG_RESULT涓殑瀛楁dwTaskNo瀵瑰簲 鍚屾椂 涓嬪彂浠诲姟缁撴瀯 NET_DVR_VEHICLE_RECOG_COND涓殑瀛楁dwTaskNo瀵瑰簲)
        ("byDeployType", C_BYTE),  # 甯冮槻绫诲瀷锛?-瀹㈡埛绔竷闃诧紝1-瀹炴椂甯冮槻
        ("byRes1", C_BYTE * 3),
        ("byAlarmTypeURL", C_BYTE),
        # bit0-琛ㄧず浜鸿劯鎶撴媿鎶ヨ涓婁紶
        # 0-琛ㄧず浜岃繘鍒朵紶杈擄紝1-琛ㄧずURL浼犺緭锛堣澶囨敮鎸佺殑鎯呭喌涓嬶紝璁惧鏀寔鑳藉姏鏍规嵁鍏蜂綋鎶ヨ鑳藉姏闆嗗垽鏂?鍚屾椂璁惧闇€瑕佹敮鎸乁RL鐨勭浉鍏虫湇鍔★紝褰撳墠鏄€濅簯瀛樺偍鈥滐級
        ("byCustomCtrl", C_BYTE)]  # Bit0- 琛ㄧず鏀寔鍓┚椹朵汉鑴稿瓙鍥句笂浼? 0-涓嶄笂浼?1-涓婁紶


LPNET_DVR_SETUPALARM_PARAM = POINTER(NET_DVR_SETUPALARM_PARAM)


# 涓婁紶鐨勬姤璀︿俊鎭粨鏋勪綋銆?
class NET_DVR_ALARMINFO_V30(Structure):
    _fields_ = [
        ("dwAlarmType", c_uint32),  # 鎶ヨ绫诲瀷
        ("dwAlarmInputNumber", c_uint32),  # 鎶ヨ杈撳叆绔彛锛屽綋鎶ヨ绫诲瀷涓?銆?3鏃舵湁鏁?
        ("byAlarmOutputNumber", c_byte * 96),
        # 瑙﹀彂鐨勬姤璀﹁緭鍑虹鍙ｏ紝鍊间负1琛ㄧず璇ユ姤璀︾鍙ｈ緭鍑猴紝濡俠yAlarmOutputNumber[0]=1琛ㄧず瑙﹀彂绗?涓姤璀﹁緭鍑哄彛杈撳嚭锛宐yAlarmOutputNumber[1]=1琛ㄧず瑙﹀彂绗?涓姤璀﹁緭鍑哄彛锛屼緷娆＄被鎺?
        ("byAlarmRelateChannel", c_byte * 64),  # 瑙﹀彂鐨勫綍鍍忛€氶亾锛屽€间负1琛ㄧず璇ラ€氶亾褰曞儚锛屽byAlarmRelateChannel[0]=1琛ㄧず瑙﹀彂绗?涓€氶亾褰曞儚
        ("byChannel", c_byte * 64),  # 鍙戠敓鎶ヨ鐨勯€氶亾銆傚綋鎶ヨ绫诲瀷涓?銆?銆?銆?銆?0銆?1銆?3銆?5銆?6鏃舵湁鏁堬紝濡俠yChannel[0]=1琛ㄧず绗?涓€氶亾鎶ヨ
        ("byDiskNumber", c_byte * 33)]  # 鍙戠敓鎶ヨ鐨勭‖鐩樸€傚綋鎶ヨ绫诲瀷涓?锛?锛?鏃舵湁鏁堬紝byDiskNumber[0]=1琛ㄧず1鍙风‖鐩樺紓甯?


LPNET_DVR_ALARMINFO_V30 = POINTER(NET_DVR_ALARMINFO_V30)


# 鏃堕棿鍙傛暟缁撴瀯浣?
class NET_DVR_TIME_EX(Structure):
    _fields_ = [
        ("dwYear", c_ushort),
        ("dwMonth", c_ubyte),
        ("dwDay", c_ubyte),
        ("dwHour", c_ubyte),
        ("dwMinute", c_ubyte),
        ("dwSecond", c_ubyte),
        ("byRes", c_ubyte)
    ]


LPNET_DVR_TIME_EX = POINTER(NET_DVR_TIME_EX)


# 闃插尯鍙傛暟缁撴瀯浣撱€?
class NET_DVR_ALARMIN_SETUP(Structure):
    _fields_ = [
        ("byAssiciateAlarmIn", C_BYTE * 512),  # 鎶ヨ绫诲瀷
        ("byRes", C_BYTE * 100)
    ]


LPNET_DVR_ALARMIN_SETUP = POINTER(NET_DVR_ALARMIN_SETUP)


# CID鎶ヨ淇℃伅缁撴瀯浣撱€?
class NET_DVR_CID_ALARM(Structure):
    _fields_ = [
        ("dwAlarmType", C_DWORD),  # 鎶ヨ绫诲瀷
        ("sCIDCode", C_BYTE * 4),  # CID浜嬩欢鍙凤紝鍙傜収NET_DVR_ALARMHOST_CID_ALL_MINOR_TYPE
        ("sCIDDescribe", C_BYTE * 32),  # CID浜嬩欢鍚?
        ("struTriggerTime", NET_DVR_TIME_EX),  # 瑙﹀彂鎶ヨ鐨勬椂闂寸偣
        ("struUploadTime", NET_DVR_TIME_EX),  # 涓婁紶鎶ヨ鐨勬椂闂寸偣
        ("sCenterAccount", C_BYTE * 6),  # 涓績甯愬彿锛宐yCenterType涓?鎴?鏃舵湁鏁?
        ("byReportType", C_BYTE),  # 鎶ュ憡绫诲瀷锛屽叿浣撳畾涔夊弬鑰僋ET_DVR_ALARMHOST_REPORT_TYPE
        ("byUserType", C_BYTE),  # 鐢ㄦ埛绫诲瀷锛?-缃戠粶鐢ㄦ埛锛?-閿洏鐢ㄦ埛
        ("sUserName", C_BYTE * 32),  # 缃戠粶鐢ㄦ埛鐢ㄦ埛鍚?
        ("wKeyUserNo", C_WORD),  # 閿洏鐢ㄦ埛鍙凤紝0xFFFF琛ㄧず鏃犳晥
        ("byKeypadNo", C_BYTE),  # 閿洏鍙凤紝0xFF琛ㄧず鏃犳晥
        ("bySubSysNo", C_BYTE),  # 瀛愮郴缁熷彿锛?xFF琛ㄧず鏃犳晥
        ("wDefenceNo", C_WORD),  # 闃插尯鍙凤紝0xFFFF琛ㄧず鏃犳晥
        ("byVideoChanNo", C_BYTE),  # 瑙嗛閫氶亾鍙凤紝0xFF琛ㄧず鏃犳晥
        ("byDiskNo", C_BYTE),  # 纭洏鍙凤紝0xFF琛ㄧず鏃犳晥
        ("wModuleAddr", C_WORD),  # 妯″潡鍦板潃锛?xFFFF琛ㄧず鏃犳晥
        ("byCenterType", C_BYTE),  # 涓績璐﹀彿绫诲瀷锛?- 鏃犳晥锛?- 涓績璐﹀彿(闀垮害6)锛?- 鎵╁睍鐨勪腑蹇冭处鍙?闀垮害32)
        ("byRes1", C_BYTE),  # 淇濈暀
        ("sCenterAccountV40", C_BYTE * 32),  # 涓績璐﹀彿鎵╁睍锛宐yCenterType涓?鏃舵湁鏁?
        ("byRes2", C_BYTE * 28)  # 淇濈暀
    ]


LPNET_DVR_CID_ALARM = POINTER(NET_DVR_CID_ALARM)


# 鏃堕棿鍙傛暟缁撴瀯浣?
class NET_DVR_TIME(Structure):
    _fields_ = [
        ("dwYear", C_DWORD),  # 骞?
        ("dwMonth", C_DWORD),  # 鏈?
        ("dwDay", C_DWORD),  # 鏃?
        ("dwHour", C_DWORD),  # 鏃?
        ("dwMinute", C_DWORD),  # 鍒?
        ("dwSecond", C_DWORD)]  # 绉?


LPNET_DVR_TIME = POINTER(NET_DVR_TIME)


# IP鍦板潃缁撴瀯浣?
class NET_DVR_IPADDR(Structure):
    _fields_ = [
        ("sIpV4", c_char * 16),  # 璁惧IPv4鍦板潃
        ("sIpV6", C_BYTE * 128)]  # 璁惧IPv6鍦板潃


LPNET_DVR_IPADDR = POINTER(NET_DVR_IPADDR)


# 闂ㄧ涓绘満浜嬩欢淇℃伅
class NET_DVR_ACS_EVENT_INFO(Structure):
    _fields_ = [
        ("dwSize", C_DWORD),  # 缁撴瀯浣撳ぇ灏?
        ("byCardNo", C_BYTE * 32),  # 鍗″彿
        ("byCardType", C_BYTE),  # 鍗＄被鍨嬶細1- 鏅€氬崱锛?- 闈炴巿鏉冨悕鍗曞崱锛?- 宸℃洿鍗★紝5- 鑳佽揩鍗★紝6- 瓒呯骇鍗★紝7- 鏉ュ鍗★紝8- 瑙ｉ櫎鍗★紝涓?琛ㄧず鏃犳晥
        ("byAllowListNo", C_BYTE),  # 鎺堟潈鍚嶅崟鍗曞彿锛屽彇鍊艰寖鍥达細1~8锛?琛ㄧず鏃犳晥
        ("byReportChannel", C_BYTE),  # 鎶ュ憡涓婁紶閫氶亾锛?- 甯冮槻涓婁紶锛?- 涓績缁?涓婁紶锛?- 涓績缁?涓婁紶锛?琛ㄧず鏃犳晥
        ("byCardReaderKind", C_BYTE),  # 璇诲崱鍣ㄧ被鍨嬶細0- 鏃犳晥锛?- IC璇诲崱鍣紝2- 韬唤璇佽鍗″櫒锛?- 浜岀淮鐮佽鍗″櫒锛?- 鎸囩汗澶?
        ("dwCardReaderNo", C_DWORD),  # 璇诲崱鍣ㄧ紪鍙凤紝涓?琛ㄧず鏃犳晥
        ("dwDoorNo", C_DWORD),  # 闂ㄧ紪鍙凤紙鎴栬€呮鎺х殑妤煎眰缂栧彿锛夛紝涓?琛ㄧず鏃犳晥锛堝綋鎺ョ殑璁惧涓轰汉鍛橀€氶亾璁惧鏃讹紝闂?涓鸿繘鏂瑰悜锛岄棬2涓哄嚭鏂瑰悜锛?
        ("dwVerifyNo", C_DWORD),  # 澶氶噸鍗¤璇佸簭鍙凤紝涓?琛ㄧず鏃犳晥
        ("dwAlarmInNo", C_DWORD),  # 鎶ヨ杈撳叆鍙凤紝涓?琛ㄧず鏃犳晥
        ("dwAlarmOutNo", C_DWORD),  # 鎶ヨ杈撳嚭鍙凤紝涓?琛ㄧず鏃犳晥
        ("dwCaseSensorNo", C_DWORD),  # 浜嬩欢瑙﹀彂鍣ㄧ紪鍙?
        ("dwRs485No", C_DWORD),  # RS485閫氶亾鍙凤紝涓?琛ㄧず鏃犳晥
        ("dwMultiCardGroupNo", C_DWORD),  # 缇ょ粍缂栧彿
        ("wAccessChannel", C_WORD),  # 浜哄憳閫氶亾鍙?
        ("byDeviceNo", C_BYTE),  # 璁惧缂栧彿锛屼负0琛ㄧず鏃犳晥
        ("byDistractControlNo", C_BYTE),  # 鍒嗘帶鍣ㄧ紪鍙凤紝涓?琛ㄧず鏃犳晥
        ("dwEmployeeNo", C_DWORD),  # 宸ュ彿锛屼负0鏃犳晥
        ("wLocalControllerID", C_WORD),  # 灏卞湴鎺у埗鍣ㄧ紪鍙凤紝0-闂ㄧ涓绘満锛?-255浠ｈ〃灏卞湴鎺у埗鍣?
        ("byInternetAccess", C_BYTE),  # 缃戝彛ID锛氾紙1-涓婅缃戝彛1,2-涓婅缃戝彛2,3-涓嬭缃戝彛1锛?
        ("byType", C_BYTE),
        # 闃插尯绫诲瀷锛?:鍗虫椂闃插尯,1-24灏忔椂闃插尯,2-寤舵椂闃插尯,3-鍐呴儴闃插尯,4-閽ュ寵闃插尯,5-鐏闃插尯,6-鍛ㄧ晫闃插尯,7-24灏忔椂鏃犲０闃插尯,
        # 8-24灏忔椂杈呭姪闃插尯,9-24灏忔椂闇囧姩闃插尯,10-闂ㄧ绱ф€ュ紑闂ㄩ槻鍖?11-闂ㄧ绱ф€ュ叧闂ㄩ槻鍖猴紝0xff-鏃?
        ("byMACAddr", C_BYTE * 6),  # 鐗╃悊鍦板潃锛屼负0鏃犳晥
        ("bySwipeCardType", C_BYTE),  # 鍒峰崱绫诲瀷锛?-鏃犳晥锛?-浜岀淮鐮?
        ("byMask", C_BYTE),  # 鏄惁甯﹀彛缃╋細0-淇濈暀锛?-鏈煡锛?-涓嶆埓鍙ｇ僵锛?-鎴村彛缃?
        ("dwSerialNo", C_DWORD),  # 浜嬩欢娴佹按鍙凤紝涓?鏃犳晥
        ("byChannelControllerID", C_BYTE),  # 閫氶亾鎺у埗鍣↖D锛屼负0鏃犳晥锛?-涓婚€氶亾鎺у埗鍣紝2-浠庨€氶亾鎺у埗鍣?
        ("byChannelControllerLampID", C_BYTE),  # 閫氶亾鎺у埗鍣ㄧ伅鏉縄D锛屼负0鏃犳晥锛堟湁鏁堣寖鍥?-255锛?
        ("byChannelControllerIRAdaptorID", C_BYTE),  # 閫氶亾鎺у埗鍣ㄧ孩澶栬浆鎺ユ澘ID锛屼负0鏃犳晥锛堟湁鏁堣寖鍥?-255锛?
        ("byChannelControllerIREmitterID", C_BYTE),  # 閫氶亾鎺у埗鍣ㄧ孩澶栧灏処D锛屼负0鏃犳晥锛堟湁鏁堣寖鍥?-255锛?
        ("byHelmet", C_BYTE),  # 鍙€夛紝鏄惁鎴村畨鍏ㄥ附锛?-淇濈暀锛?-鏈煡锛?-涓嶆埓瀹夊叏, 3-鎴村畨鍏ㄥ附
        ("byRes", C_BYTE * 3)]  # 淇濈暀锛岀疆涓?


LPNET_DVR_ACS_EVENT_INFO = POINTER(NET_DVR_ACS_EVENT_INFO)


class NET_DVR_ACS_EVENT_INFO_EXTEND(Structure):
    _fields_ = [
        ("dwFrontSerialNo", C_DWORD),  # 浜嬩欢娴佹按鍙凤紝涓?鏃犳晥
        ("byUserType", C_BYTE),  # 浜哄憳绫诲瀷锛?-鏃犳晥锛?-鏅€氫汉锛堜富浜猴級锛?-鏉ュ锛堣瀹級锛?-闈炴巿鏉冨悕鍗曚汉锛?-绠＄悊鍛?
        ("byCurrentVerifyMode", C_BYTE),  # 璇诲崱鍣ㄥ綋鍓嶉獙璇佹柟寮?
        ("byCurrentEvent", C_BYTE),  # 鏄惁涓哄疄鏃朵簨浠讹細0-鏃犳晥锛?-鏄紙瀹炴椂浜嬩欢锛夛紝2-鍚︼紙绂荤嚎浜嬩欢锛?
        ("byPurePwdVerifyEnable", C_BYTE),  # 璁惧鏄惁鏀寔绾瘑鐮佽璇侊細0-涓嶆敮鎸侊紝1-鏀寔
        ("byEmployeeNo", C_BYTE * 32),
        # 宸ュ彿锛堜汉鍛業D锛夛紙瀵逛簬璁惧鏉ヨ锛屽鏋滀娇鐢ㄤ簡宸ュ彿锛堜汉鍛業D锛夊瓧娈碉紝byEmployeeNo涓€瀹氳浼犻€掞紝濡傛灉byEmployeeNo鍙浆鎹负dwEmployeeNo锛岄偅涔堣瀛楁涔熻浼犻€掞紱瀵逛簬涓婂眰骞冲彴鎴栧鎴风鏉ヨ锛屼紭鍏堣В鏋恇yEmployeeNo瀛楁锛屽璇ュ瓧娈典负绌猴紝鍐嶈€冭檻瑙ｆ瀽dwEmployeeNo瀛楁锛?
        ("byAttendanceStatus", C_BYTE),  # 鑰冨嫟鐘舵€侊細0-鏈畾涔?1-涓婄彮锛?-涓嬬彮锛?-寮€濮嬩紤鎭紝4-缁撴潫浼戞伅锛?-寮€濮嬪姞鐝紝6-缁撴潫鍔犵彮
        ("byStatusValue", C_BYTE),  # 鑰冨嫟鐘舵€佸€?
        ("byRes2", C_BYTE * 2),  # 淇濈暀锛岀疆涓?
        ("byUUID", C_BYTE * 36),  # UUID锛堣瀛楁浠呭湪瀵规帴钀ょ煶骞冲彴杩囩▼涓墠浼氫娇鐢級
        ("byDeviceName", C_BYTE * 64),  # 璁惧搴忓垪鍙?
        ("byRes", C_BYTE * 24),  # 淇濈暀锛岀疆涓?
    ]


LPNET_DVR_ACS_EVENT_INFO_EXTEND = POINTER(NET_DVR_ACS_EVENT_INFO_EXTEND)


# 闂ㄧ涓绘満鎶ヨ淇℃伅缁撴瀯浣?
class NET_DVR_ACS_ALARM_INFO(Structure):
    _fields_ = [
        ("dwSize", C_DWORD),  # 缁撴瀯浣撳ぇ灏?
        ("dwMajor", C_DWORD),  # 鎶ヨ涓荤被鍨嬶紝鍏蜂綋瀹氫箟瑙佲€淩emarks鈥濊鏄?
        ("dwMinor", C_DWORD),  # 鎶ヨ娆＄被鍨嬶紝娆＄被鍨嬪惈涔夋牴鎹富绫诲瀷涓嶅悓鑰屼笉鍚岋紝鍏蜂綋瀹氫箟瑙佲€淩emarks鈥濊鏄?
        ("struTime", NET_DVR_TIME),  # 鎶ヨ鏃堕棿
        ("sNetUser", C_BYTE * 16),  # 缃戠粶鎿嶄綔鐨勭敤鎴峰悕
        ("struRemoteHostAddr", NET_DVR_IPADDR),  # 杩滅▼涓绘満鍦板潃
        ("struAcsEventInfo", NET_DVR_ACS_EVENT_INFO),  # 鎶ヨ淇℃伅璇︾粏鍙傛暟
        ("dwPicDataLen", C_DWORD),  # 鍥剧墖鏁版嵁澶у皬锛屼笉涓?鏄〃绀哄悗闈㈠甫鏁版嵁
        # ("pPicData", c_char_p),  # 鍥剧墖鏁版嵁缂撳啿鍖?
        ("pPicData", POINTER(C_BYTE)),  # 鍥剧墖鏁版嵁缂撳啿鍖?
        ("wInductiveEventType", C_WORD),  # 褰掔撼浜嬩欢绫诲瀷锛?-鏃犳晥锛屽鎴风鍒ゆ柇璇ュ€间负闈?鍊煎悗锛屾姤璀︾被鍨嬮€氳繃褰掔撼浜嬩欢绫诲瀷鍖哄垎锛屽惁鍒欓€氳繃鍘熸湁鎶ヨ涓绘绫诲瀷锛坉wMajor銆乨wMinor锛夊尯鍒?
        ("byPicTransType", C_BYTE),  # 鍥剧墖鏁版嵁浼犺緭鏂瑰紡: 0-浜岃繘鍒讹紱1-url
        ("byRes1", C_BYTE),  # 淇濈暀锛岀疆涓?
        ("dwIOTChannelNo", C_DWORD),  # IOT閫氶亾鍙?
        ("pAcsEventInfoExtend", c_void_p),  # byAcsEventInfoExtend涓?鏃讹紝琛ㄧず鎸囧悜涓€涓狽ET_DVR_ACS_EVENT_INFO_EXTEND缁撴瀯浣?
        ("byAcsEventInfoExtend", C_BYTE),  # pAcsEventInfoExtend鏄惁鏈夋晥锛?-鏃犳晥锛?-鏈夋晥
        ("byTimeType", C_BYTE),  # 鏃堕棿绫诲瀷锛?-璁惧鏈湴鏃堕棿锛?-UTC鏃堕棿锛坰truTime鐨勬椂闂达級
        ("byRes2", C_BYTE),  # 淇濈暀锛岀疆涓?
        ("byAcsEventInfoExtendV20", C_BYTE),  # pAcsEventInfoExtendV20鏄惁鏈夋晥锛?-鏃犳晥锛?-鏈夋晥
        ("pAcsEventInfoExtendV20", c_void_p),  # byAcsEventInfoExtendV20涓?鏃讹紝琛ㄧず鎸囧悜涓€涓狽ET_DVR_ACS_EVENT_INFO_EXTEND_V20缁撴瀯浣?
        ("byRes", C_BYTE * 4)  # 淇濈暀锛岀疆涓?
    ]


LPNET_DVR_ACS_ALARM_INFO = POINTER(NET_DVR_ACS_ALARM_INFO)


# 鐐瑰潗鏍囧弬鏁扮粨鏋勪綋
class NET_VCA_POINT(Structure):
    _fields_ = [
        ("fX", c_float),
        ("fY", c_float)
    ]


# 韬唤璇佸埛鍗′俊鎭墿灞曞弬鏁?
class NET_DVR_ID_CARD_INFO_EXTEND(Structure):
    _fields_ = [
        ("byRemoteCheck", C_BYTE),
        ("byThermometryUnit", C_BYTE),
        ("byIsAbnomalTemperature", C_BYTE),
        ("byRes2", C_BYTE),
        ("fCurrTemperature", c_float),
        ("struRegionCoordinates", NET_VCA_POINT),
        ("dwQRCodeInfoLen", C_DWORD),
        ("dwVisibleLightDataLen", C_DWORD),
        ("dwThermalDataLen", C_DWORD),
        ("pQRCodeInfo", c_char_p),
        ("pVisibleLightData", c_char_p),
        ("pThermalData", c_char_p),
        ("wXCoordinate", C_WORD),
        ("wYCoordinate", C_WORD),
        ("wWidth", C_WORD),
        ("wHeight", C_WORD),
        ("byHealthCode", C_BYTE),
        ("byNADCode", C_BYTE),
        ("byTravelCode", C_BYTE),
        ("byVaccineStatus", C_BYTE),
        ("byRes", C_BYTE * 1012)
    ]


# 鏃ユ湡淇℃伅缁撴瀯浣?
class NET_DVR_DATE(Structure):
    _fields_ = [
        ('wYear', C_WORD),
        ('byMonth', C_BYTE),
        ('byDay', C_BYTE)
    ]


# 韬唤璇佷俊鎭粨鏋勪綋
class NET_DVR_ID_CARD_INFO(Structure):
    _fields_ = [
        ("dwSize", C_DWORD),
        ("byName", C_BYTE * 128),
        ("struBirth", NET_DVR_DATE),
        ("byAddr", C_BYTE * 280),
        ("byIDNum", C_BYTE * 32),
        ("byIssuingAuthority", C_BYTE * 128),
        ("struStartDate", NET_DVR_DATE),
        ("struEndDate", NET_DVR_DATE),
        ("byTermOfValidity", C_BYTE),
        ("bySex", C_BYTE),
        ("byNation", C_BYTE),
        ("byRes", C_BYTE * 101)
    ]


# 鏃堕棿鍙傛暟缁撴瀯浣?
class NET_DVR_TIME(Structure):
    _fields_ = [
        ("dwYear", C_DWORD),
        ("dwMonth", C_DWORD),
        ("dwDay", C_DWORD),
        ("dwHour", C_DWORD),
        ("dwMinute", C_DWORD),
        ("dwSecond", C_DWORD)
    ]


# 鏃堕棿鍙傛暟缁撴瀯浣?
class NET_DVR_TIME_V30(Structure):
    _fields_ = [
        ('wYear', C_WORD),
        ('byMonth', C_BYTE),
        ('byDay', C_BYTE),
        ('byHour', C_BYTE),
        ('byMinute', C_BYTE),
        ('bySecond', C_BYTE),
        ('byISO8601', C_BYTE),
        ('wMilliSec', C_WORD),
        ('cTimeDifferenceH', c_byte),
        ('cTimeDifferenceM', c_byte),
    ]


# 韬唤璇佸埛鍗′俊鎭笂浼犵粨鏋勪綋
class NET_DVR_ID_CARD_INFO_ALARM(Structure):
    _fields_ = [
        ("dwSize", C_DWORD),  # 缁撴瀯闀垮害
        ("struIDCardCfg", NET_DVR_ID_CARD_INFO),  # 韬唤璇佷俊鎭?
        ("dwMajor", C_DWORD),  # 鎶ヨ涓荤被鍨嬶紝鍙傝€冨畯瀹氫箟
        ("dwMinor", C_DWORD),  # 鎶ヨ娆＄被鍨嬶紝鍙傝€冨畯瀹氫箟
        ("struSwipeTime", NET_DVR_TIME_V30),  # 鍒峰崱鏃堕棿
        ("byNetUser", C_BYTE * 16),  # 缃戠粶鎿嶄綔鐨勭敤鎴峰悕
        ("struRemoteHostAddr", NET_DVR_IPADDR),  # 杩滅▼涓绘満鍦板潃
        ("dwCardReaderNo", C_DWORD),  # 璇诲崱鍣ㄧ紪鍙凤紝涓?鏃犳晥
        ("dwDoorNo", C_DWORD),  # 闂ㄧ紪鍙凤紝涓?鏃犳晥
        ("dwPicDataLen", C_DWORD),  # 鍥剧墖鏁版嵁澶у皬锛屼笉涓?鏄〃绀哄悗闈㈠甫鏁版嵁
        ("pPicData", c_void_p),  # 韬唤璇佸浘鐗囨暟鎹紦鍐插尯锛宒wPicDataLen涓嶄负0鏃剁紦鍐插尯閲岄潰瀛樻斁韬唤璇佸ご鍍忕殑鍥剧墖鏁版嵁
        ("byCardType", C_BYTE),  # 鍗＄被鍨嬶紝1-鏅€氬崱锛?-闈炴巿鏉冨悕鍗曞崱锛?-宸℃洿鍗★紝5-鑳佽揩鍗★紝6-瓒呯骇鍗★紝7-鏉ュ鍗★紝8-瑙ｉ櫎鍗★紝涓?鏃犳晥
        ("byDeviceNo", C_BYTE),  # 璁惧缂栧彿锛屼负0鏃舵棤鏁堬紙鏈夋晥鑼冨洿1-255锛?
        ("byMask", C_BYTE),  # 鏄惁甯﹀彛缃╋細0-淇濈暀锛?-鏈煡锛?-涓嶆埓鍙ｇ僵锛?-鎴村彛缃?
        ("byRes2", C_BYTE),  # 淇濈暀锛岀疆涓?
        ("dwFingerPrintDataLen", C_DWORD),  # 鎸囩汗鏁版嵁澶у皬锛屼笉涓?鏄〃绀哄悗闈㈠甫鏁版嵁
        ("pFingerPrintData", c_void_p),  # 鎸囩汗鏁版嵁缂撳啿鍖猴紝dwFingerPrintDataLen涓嶄负0鏃剁紦鍐插尯閲岄潰瀛樻斁鎸囩汗鏁版嵁
        ("dwCapturePicDataLen", C_DWORD),  # 鎶撴媿鍥剧墖鏁版嵁澶у皬锛屼笉涓?鏄〃绀哄悗闈㈠甫鏁版嵁
        ("pCapturePicData", c_void_p),  # 鎶撴媿鍥剧墖鏁版嵁缂撳啿鍖猴紝dwCapturePicDataLen涓嶄负0鏃剁紦鍐插尯閲岄潰瀛樻斁璁惧涓婃憚鍍忔満鎶撴媿涓婁紶鐨勫浘鐗囨暟鎹?
        ("dwCertificatePicDataLen", C_DWORD),  # 璇佷欢鎶撴媿鍥剧墖鏁版嵁澶у皬锛屼笉涓?鏄〃绀哄悗闈㈠甫鏁版嵁
        ("pCertificatePicData", c_void_p),  # 璇佷欢鎶撴媿鍥剧墖鏁版嵁缂撳啿鍖猴紝dwCertificatePicDataLen涓嶄负0鏃剁紦鍐插尯閲岄潰瀛樻斁璁惧涓婃憚鍍忔満鎶撴媿涓婁紶鐨勮瘉浠舵姄鎷嶅浘鐗囨暟鎹?
        ("byCardReaderKind", C_BYTE),  # 璇诲崱鍣ㄥ睘浜庡摢涓€绫伙細0-鏃犳晥锛?-IC璇诲崱鍣紝2-韬唤璇佽鍗″櫒锛?-浜岀淮鐮佽鍗″櫒锛?-鎸囩汗澶?
        ("byRes3", C_BYTE * 2),  # 淇濈暀锛岀疆涓?
        ("byIDCardInfoExtend", C_BYTE),  # pIDCardInfoExtend鏄惁鏈夋晥锛?-鏃犳晥锛?-鏈夋晥
        ("pIDCardInfoExtend", POINTER(NET_DVR_ID_CARD_INFO_EXTEND)),  # 韬唤璇佸埛鍗℃墿灞曚簨浠朵俊鎭?
        ("byRes", C_BYTE * 172)  # 韬唤璇佸埛鍗℃墿灞曚簨浠朵俊鎭?
    ]


LPNET_DVR_ID_CARD_INFO_ALARM = POINTER(NET_DVR_ID_CARD_INFO_ALARM)


class NET_DVR_ALARM_ISAPI_PICDATA(Structure):
    _fields_ = [
        ("dwPicLen", C_DWORD),  # 鍥剧墖鏁版嵁闀垮害
        ("byPicType", C_BYTE),  # 鍥剧墖鏍煎紡: 1- jpg
        ("byRes", C_BYTE * 3),  #
        ("szFilename", c_char * 256),  # 鍥剧墖鍚嶇О
        ("pPicData", POINTER(C_BYTE)),  # 鍥剧墖鏁版嵁
    ]


LPNET_DVR_ALARM_ISAPI_PICDATA = POINTER(NET_DVR_ALARM_ISAPI_PICDATA)


class NET_DVR_ALARM_ISAPI_INFO(Structure):
    _fields_ = [
        ("pAlarmData", c_char_p),  # 鎶ヨ鏁版嵁
        ("dwAlarmDataLen", C_DWORD),  # 鎶ヨ鏁版嵁闀垮害
        ("byDataType", C_BYTE),  # 0-invalid,1-xml,2-json
        ("byPicturesNumber", C_BYTE),  # 鍥剧墖鏁伴噺
        ("byRes[2]", C_BYTE * 2),  # 淇濈暀瀛楄妭
        ("pPicPackData", c_void_p),  # 鍥剧墖鍙橀暱閮ㄥ垎
        ("byRes1[32]", C_BYTE * 32),  # 淇濈暀瀛楄妭
    ]


LPNET_DVR_ALARM_ISAPI_INFO = POINTER(NET_DVR_ALARM_ISAPI_INFO)


class NET_DVR_LOCAL_GENERAL_CFG(Structure):
    _fields_ = [
        ("byExceptionCbDirectly", C_BYTE),  # 0-閫氳繃绾跨▼姹犲紓甯稿洖璋冿紝1-鐩存帴寮傚父鍥炶皟缁欎笂灞?
        ("byNotSplitRecordFile", C_BYTE),  # 鍥炴斁鍜岄瑙堜腑淇濆瓨鍒版湰鍦板綍鍍忔枃浠朵笉鍒囩墖 0-榛樿鍒囩墖锛?-涓嶅垏鐗?
        ("byResumeUpgradeEnable", C_BYTE),  # 鏂綉缁紶鍗囩骇浣胯兘锛?-鍏抽棴锛堥粯璁わ級锛?-寮€鍚?
        ("byAlarmJsonPictureSeparate", C_BYTE),  # 鎺у埗JSON閫忎紶鎶ヨ鏁版嵁鍜屽浘鐗囨槸鍚﹀垎绂伙紝0-涓嶅垎绂伙紝1-鍒嗙锛堝垎绂诲悗璧癈OMM_ISAPI_ALARM鍥炶皟杩斿洖锛?
        ("byRes", C_BYTE * 4),  # 淇濈暀
        ("i64FileSize", C_UINT64),  # 鍗曚綅锛欱yte
        ("dwResumeUpgradeTimeout", C_DWORD),  # 鏂綉缁紶閲嶈繛瓒呮椂鏃堕棿锛屽崟浣嶆绉?
        ("byAlarmReconnectMode", C_BYTE),  # 0-鐙珛绾跨▼閲嶈繛锛堥粯璁わ級 1-绾跨▼姹犻噸杩?
        ("byStdXmlBufferSize", C_BYTE),  # 璁剧疆ISAPI閫忎紶鎺ユ敹缂撳啿鍖哄ぇ灏忥紝1-1M 鍏朵粬-榛樿
        ("byMultiplexing", C_BYTE),  # 0-鏅€氶摼鎺ワ紙闈濼LS閾炬帴锛夊叧闂璺鐢紝1-鏅€氶摼鎺ワ紙闈濼LS閾炬帴锛夊紑鍚璺鐢?
        ("byFastUpgrade", C_BYTE),  # 0-姝ｅ父鍗囩骇锛?-蹇€熷崌绾?
        ("byRes1", C_BYTE * 232),  # 棰勭暀
    ]


# 鍖哄煙妗嗗弬鏁扮粨鏋勪綋銆?
class NET_VCA_RECT(Structure):
    _fields_ = [
        ("fX", c_float),  # 杈圭晫妗嗗乏涓婅鐐圭殑X杞村潗鏍?
        ("fY", c_float),  # 杈圭晫妗嗗乏涓婅鐐圭殑Y杞村潗鏍?
        ("fWidth", c_float),  # 杈圭晫妗嗙殑瀹藉害
        ("fHeight", c_float)  # 杈圭晫妗嗙殑楂樺害
    ]


# 鎶ヨ鐩爣淇℃伅缁撴瀯浣撱€?
class NET_VCA_TARGET_INFO(Structure):
    _field_ = [
        ('dwID', C_DWORD),  # 鐩爣ID
        ('struRect', NET_VCA_RECT),  # 鐩爣杈圭晫妗?
        ('byRes', C_BYTE * 4)
    ]


# 鍓嶇璁惧淇℃伅缁撴瀯浣撱€?
class NET_VCA_DEV_INFO(Structure):
    _fields_ = [
        ('struDevIP', NET_DVR_IPADDR),  # 鎶ヨ閫氶亾瀵瑰簲璁惧鐨処P鍦板潃
        ('wPort', C_WORD),  # 鎶ヨ閫氶亾瀵瑰簲璁惧鐨勭鍙ｅ彿
        ('byChannel', C_BYTE),  # 鎶ヨ閫氶亾瀵瑰簲璁惧鐨勯€氶亾鍙凤紝鍙傛暟鍊煎嵆琛ㄧず閫氶亾鍙枫€傛瘮濡傦紝byChannel=1锛岃〃绀洪€氶亾1
        ('byIvmsChannel', C_BYTE)  # SDK鎺ュ叆璁惧鐨勯€氶亾鍙?
    ]


# 浜轰綋灞炴€у弬鏁扮粨鏋勪綋銆?
class NET_VCA_HUMAN_FEATURE(Structure):
    _fields_ = [
        ("byAgeGroup", C_BYTE),  # 骞撮緞娈碉紝0xffffffff琛ㄧず鍏ㄩ儴锛堜笉鍏虫敞骞撮緞娈碉級锛岃瑙佹灇涓剧被鍨嬶細HUMAN_AGE_GROUP_ENUM
        ("bySex", C_BYTE),  # 鎬у埆锛?- 鐢凤紝2- 濂?
        ("byEyeGlass", C_BYTE),  # 鏄惁鎴寸溂闀滐細1- 涓嶆埓锛?- 鎴?
        ("byAge", C_BYTE),  # 骞撮緞
        ("byAgeDeviation", C_BYTE),  # 骞撮緞璇樊鍊硷紝濡俠yAge涓?5銆乥yAgeDeviation涓?锛岃〃绀哄疄闄呬汉鑴稿浘鐗囧勾榫勭殑涓?4~16涔嬮棿
        ("byRes0", C_BYTE),  # 淇濈暀
        ("byMask", C_BYTE),  # 鏄惁鎴村彛缃╋細0-琛ㄧず鈥滄湭鐭モ€濓紙绠楁硶涓嶆敮鎸侊級锛?- 涓嶆埓鍙ｇ僵锛?-鎴村彛缃╋紱0xff-绠楁硶鏀寔锛屼絾鏄病鏈夎瘑鍒嚭鏉?
        ("bySmile", C_BYTE),  # 鏄惁寰瑧锛?-琛ㄧず鈥滄湭鐭モ€濓紙绠楁硶涓嶆敮鎸侊級锛?- 涓嶅井绗戯紱2- 寰瑧锛?xff-绠楁硶鏀寔锛屼絾鏄病鏈夎瘑鍒嚭鏉?
        ("byFaceExpression", C_BYTE),  # 淇濈暀
        ("byRes1", C_BYTE),  # 淇濈暀
        ("byRes2", C_BYTE),  # 淇濈暀
        ("byHat", C_BYTE),  # 甯藉瓙锛?- 涓嶆敮鎸侊紱1- 涓嶆埓甯藉瓙锛?- 鎴村附瀛愶紱0xff- 鏈煡,绠楁硶鏀寔鏈鍑?
        ("byRes", C_BYTE * 4)  # 淇濈暀
    ]


# 浜鸿劯鎶撴媿缁撴灉缁撴瀯浣撱€?
class NET_VCA_FACESNAP_RESULT(Structure):
    _fields_ = [
        ("dwSize", C_DWORD),  # 缁撴瀯浣撳ぇ灏?
        ("dwRelativeTime", C_DWORD),  # 鐩稿鏃舵爣
        ("dwAbsTime", C_DWORD),  # 缁濆鏃舵爣
        ("dwFacePicID", C_DWORD),  # 浜鸿劯鍥綢D
        ("dwFaceScore", C_DWORD),  # 浜鸿劯璇勫垎锛岃寖鍥达細0~100
        ("struTargetInfo", NET_VCA_TARGET_INFO),  # 鎶ヨ鐩爣淇℃伅
        ("struRect", NET_VCA_RECT),  # 浜鸿劯瀛愬浘鍖哄煙
        ("struDevInfo", NET_VCA_DEV_INFO),  # 鍓嶇璁惧淇℃伅
        ("dwFacePicLen", C_DWORD),  # 浜鸿劯瀛愬浘鐨勯暱搴︼紝涓?琛ㄧず娌℃湁鍥剧墖锛屽ぇ浜?琛ㄧず鏈夊浘鐗?
        ("dwBackgroundPicLen", C_DWORD),  # 鑳屾櫙鍥剧殑闀垮害锛屼负0琛ㄧず娌℃湁鍥剧墖锛屽ぇ浜?琛ㄧず鏈夊浘鐗?淇濈暀)
        ("bySmart", C_BYTE),  # 0- iDS璁惧杩斿洖锛堥粯璁ゅ€硷級锛?- SMART璁惧杩斿洖
        ("byAlarmEndMark", C_BYTE),  # 鎶ヨ缁撴潫鏍囪锛?- 淇濈暀锛?- 缁撴潫鏍囪锛堣瀛楁缁撳悎浜鸿劯ID瀛楁浣跨敤锛岃〃绀鸿ID瀵瑰簲鐨勪笅鎶ヨ缁撴潫锛岀敤浜庡垽鏂姤璀︾粨鏉燂紝鎻愬彇璇嗗埆鍥剧墖鏁版嵁涓紝娓呮櫚搴︽渶楂樼殑鍥剧墖锛?
        ("byRepeatTimes", C_BYTE),  # 閲嶅鎶ヨ娆℃暟锛?-鏃犳剰涔?
        ("byUploadEventDataType", C_BYTE),  # 浜鸿劯鍥剧墖鏁版嵁闀夸紶鏂瑰紡锛?-浜岃繘鍒舵暟鎹紝1-URL
        ("struFeature", NET_VCA_HUMAN_FEATURE),  # 浜轰綋灞炴€?
        ("fStayDuration", c_float),  # 鍋滅暀鐢婚潰涓椂闂达紙鍗曚綅锛氱锛?
        ("sStorageIP", c_char * 16),  # 瀛樺偍鏈嶅姟IP鍦板潃
        ("wStoragePort", C_WORD),  # 瀛樺偍鏈嶅姟绔彛鍙?
        ("wDevInfoIvmsChannelEx", C_WORD),
        # 涓嶯ET_VCA_DEV_INFO閲岀殑byIvmsChannel鍚箟鐩稿悓锛岃兘琛ㄧず鏇村ぇ鐨勫€笺€傝€佸鎴风鐢╞yIvmsChannel鑳界户缁吋瀹癸紝浣嗘槸鏈€澶у埌255銆傛柊瀹㈡埛绔増鏈浣跨敤wDevInfoIvmsChannelEx
        ("byFacePicQuality", C_BYTE),  # 浜鸿劯瀛愬浘鍥剧墖璐ㄩ噺璇勪及绛夌骇锛?-浣庣瓑璐ㄩ噺锛?-涓瓑璐ㄩ噺锛?-楂樼瓑璐ㄩ噺锛?
        ("byUIDLen", C_BYTE),  # 涓婁紶鎶ヨ鐨勬爣璇嗛暱搴?
        ("byLivenessDetectionStatus", C_BYTE),  # 娲讳綋妫€娴嬬姸鎬? 0-淇濈暀锛?-鏈煡(妫€娴嬪け璐?锛?-闈炵湡浜轰汉鑴?
        ("byAddInfo", C_BYTE),  # 闄勫姞淇℃伅鏍囪瘑浣嶏細0-鏃犻檮鍔犱俊鎭紝1-鏈夐檮鍔犱俊鎭?
        ("pUIDBuffer", POINTER(C_BYTE)),  # 鏍囪瘑鎸囬拡锛宐yUIDLen涓?鏃舵湁鏁堬紝閫氳繃byUIDLen鍜宲UIDBuffer鐨勫唴瀹瑰垽鏂槸鍚︽槸鍚屼竴娆℃姄鎷嶇粨鏋?
        ("pAddInfoBuffer", POINTER(C_BYTE)),
        # 闄勫姞淇℃伅鎸囬拡锛宐yAddInfo涓?鏃舵湁鏁堬紝鎸囧悜NET_VCA_FACESNAP_ADDINFO缁撴瀯浣擄紝鎸囬拡鎸囧悜鍐呭瓨澶у皬涓哄浐瀹氬ぇ灏忓嵆NET_VCA_FACESNAP_ADDINFO缁撴瀯浣撶殑澶у皬
        ("byTimeDiffFlag", C_BYTE),  # 鏃跺樊瀛楁鏄惁鏈夋晥锛?-鏃跺樊鏃犳晥锛?-鏃跺樊鏈夋晥
        ("cTimeDifferenceH", c_char),  # 涓嶶TC鐨勬椂宸紙灏忔椂锛夛紝-12 ... +14锛?琛ㄧず涓滃尯,锛宐yTimeDiffFlag涓?鏃舵湁鏁?
        ("cTimeDifferenceM", c_char),  # 涓嶶TC鐨勬椂宸紙鍒嗛挓锛夛紝-30, 30, 45锛?琛ㄧず涓滃尯锛宐yTimeDiffFlag涓?鏃舵湁鏁?
        ("byBrokenNetHttp", C_BYTE),  # 鏂綉缁紶鏍囧織浣嶏細0-闈為噸浼犳暟鎹紝1-閲嶄紶鏁版嵁
        ("pBuffer1", POINTER(C_BYTE)),  # 浜鸿劯瀛愬浘鐨勫浘鐗囨暟鎹?
        ("pBuffer2", POINTER(C_BYTE))  # 鑳屾櫙鍥剧殑鍥剧墖鏁版嵁
    ]


LPNET_VCA_FACESNAP_RESULT = POINTER(NET_VCA_FACESNAP_RESULT)


# 绫嶈疮鍙傛暟缁撴瀯浣?
class NET_DVR_AREAINFOCFG(Structure):
    _fields_ = [
        ("wNationalityID", C_WORD),  # 鍥界睄
        ("wProvinceID", C_WORD),  # 鐪侊紝dwCode涓?鏃跺彇鍊艰瑙佹灇涓剧被鍨嬶細PROVINCE_CITY_IDX
        ("wCityID", C_WORD),  # 甯?
        ("wCountyID", C_WORD),  # 鍘?
        ("dwCode", C_DWORD),
        # 鍥藉鍜屽湴鍖烘爣鍑嗙殑鐪佷唤銆佸煄甯傘€佸幙绾т唬鐮侊紝涓?琛ㄧず璁惧涓嶆敮鎸侊紝涓嶄负0鏃秝NationalityID銆亀ProvinceID銆亀CityID銆亀CountyID鍙栧€艰瑙佸叏鍥藉悇鐪佷唤鍩庡競鍒楄〃
    ]


# 浜哄憳淇℃伅缁撴瀯浣?
class NET_VCA_HUMAN_ATTRIBUTE(Structure):
    _fields_ = [
        ('bySex', C_BYTE),  # 鎬у埆锛?- 鐢凤紝1- 濂筹紝0xff- 鏈煡
        ('byCertificateType', C_BYTE),  # 璇佷欢绫诲瀷锛?- 韬唤璇侊紝1- 璀﹀畼璇侊紝3- 鎶ょ収锛?- 鍏朵粬锛?xff- 鏈煡
        ('byBirthDate', C_BYTE * 10),  # 鍑虹敓骞存湀锛屽锛?01106
        ('byName', C_BYTE * 32),  # 濮撳悕
        ('struNativePlace', NET_DVR_AREAINFOCFG),  # 绫嶈疮
        ('byCertificateNumber', C_BYTE * 32),  # 璇佷欢鍙?
        ('dwPersonInfoExtendLen', C_DWORD),  # 浜哄憳鏍囩淇℃伅鎵╁睍闀垮害
        ('pPersonInfoExtend', POINTER(C_BYTE)),
        # 浜哄憳鏍囩淇℃伅鎵╁睍淇℃伅锛屽搴擷ML鏁版嵁缁撴瀯锛歅ersonInfoExtendList锛岃鏍囩淇℃伅鍙互閫氳繃鎺ュ彛(NET_DVR_STDXMLConfig)瀵煎叆锛岃澶囩涓嶅仛澶勭悊锛岀洿鎺ュ湪姣斿涓婁紶鐨勬椂鍊欓€忎紶鎼哄甫璇ユ暟鎹俊鎭?
        ('byAgeGroup', C_BYTE),  # 骞撮緞娈碉紝璇﹁鏋氫妇绫诲瀷锛欻UMAN_AGE_GROUP_ENUM
        ('byRes2', C_BYTE * 3),  # 淇濈暀
        ('pThermalData', POINTER(C_BYTE)),  # 鐑垚鍍忓浘鐗囨寚閽?
    ]


# 榛戝悕鍗曚汉鍛樹俊鎭粨鏋勪綋
class NET_VCA_BLOCKLIST_INFO(Structure):
    _fields_ = [
        ('dwSize', C_DWORD),  # 缁撴瀯浣撳ぇ灏?
        ('dwRegisterID', C_DWORD),  # 鍚嶅崟娉ㄥ唽ID鍙凤紙鍙锛?
        ('dwGroupNo', C_DWORD),  # 鍒嗙粍鍙?
        ('byType', C_BYTE),  # 闈炴巿鏉冨悕鍗曟爣蹇楋細0- 鍏ㄩ儴锛?- 鎺堟潈鍚嶅崟(闄岀敓浜烘姤璀?锛?- 闈炴巿鏉冨悕鍗?浜鸿劯姣斿鎶ヨ)
        ('byLevel', C_BYTE),  # 闈炴巿鏉冨悕鍗曠瓑绾э細0- 鍏ㄩ儴锛?- 浣庯紝2- 涓紝3- 楂?
        ('byRes1', C_BYTE * 2),  # 淇濈暀
        ('struAttribute', NET_VCA_HUMAN_ATTRIBUTE),  # 浜哄憳淇℃伅
        ('byRemark', C_BYTE * 32),  # 澶囨敞淇℃伅
        ('dwFDDescriptionLen', C_DWORD),  # 浜鸿劯搴撴弿杩版暟鎹暱搴?
        ('pFDDescriptionBuffer', POINTER(C_BYTE)),  # 浜鸿劯搴撴弿杩版暟鎹寚閽堬紝瀵瑰簲XML鏁版嵁缁撴瀯锛欶DDescription
        ('dwFCAdditionInfoLen', C_DWORD),  # 鎶撴媿搴撻檮鍔犱俊鎭暱搴?
        ('pFCAdditionInfoBuffer', POINTER(C_BYTE)),  # 鎶撴媿搴撻檮鍔犱俊鎭暟鎹寚閽堬紝瀵瑰簲XML鏁版嵁缁撴瀯锛欶CAdditionInfo
        ('dwThermalDataLen', C_DWORD),  # 鐑垚鍍忓浘鐗囬暱搴︼紝瀵瑰簲struAttribute瀛楁涓殑pThermalData鐑垚鍍忓浘鐗囨暟鎹暱搴︼紝浠呬汉鑴告瘮瀵逛簨浠朵笂鎶ユ敮鎸?
    ]


# 瀹氫箟 锛堜汉鑴稿姣旓級浜鸿劯鎶撴媿淇℃伅缁撴瀯浣撱€?
class NET_VCA_FACESNAP_INFO_ALARM(Structure):
    _fields_ = [
        ('dwRelativeTime', C_DWORD),  # 鐩稿鏃舵爣
        ('dwAbsTime', C_DWORD),  # 缁濆鏃舵爣
        ('dwSnapFacePicID', C_DWORD),  # 鎶撴媿浜鸿劯鍥綢D
        ('dwSnapFacePicLen', C_DWORD),  # 鎶撴媿浜鸿劯瀛愬浘鐨勯暱搴︼紝涓?琛ㄧず娌℃湁鍥剧墖锛屽ぇ浜?琛ㄧず鏈夊浘鐗?
        ('struDevInfo', NET_VCA_DEV_INFO),  # 鍓嶇璁惧淇℃伅
        ('byFaceScore', C_BYTE),  # 浜鸿劯璇勫垎锛屾寚浜鸿劯瀛愬浘鐨勮川閲忕殑璇勫垎锛屽彇鍊艰寖鍥达細0~100
        ('bySex', C_BYTE),  # 鎬у埆锛?- 鏈煡锛?- 鐢凤紝2- 濂?
        ('byGlasses', C_BYTE),  # 鏄惁甯︾溂闀滐細0- 鏈煡锛?- 鏄紝2- 鍚?
        ('byAge', C_BYTE),  # 骞撮緞
        ('byAgeDeviation', C_BYTE),  # 骞撮緞璇樊鍊硷紝濡俠yAge涓?5涓攂yAgeDeviation涓?锛屽垯琛ㄧず瀹為檯浜鸿劯鍥剧墖骞撮緞鐨勪负14~16涔嬮棿
        ('byAgeGroup', C_BYTE),  # 骞撮緞娈碉紝璇﹁鏋氫妇绫诲瀷锛欻UMAN_AGE_GROUP_ENUM
        ('byFacePicQuality', C_BYTE),
        # 鑴稿瓙鍥惧浘鐗囪川閲忚瘎浼扮瓑绾э細0-浣庣瓑璐ㄩ噺锛?-涓瓑璐ㄩ噺锛?-楂樼瓑璐ㄩ噺锛岃璐ㄩ噺璇勪及绠楁硶浠呴拡瀵逛汉鑴稿瓙鍥惧崟寮犲浘鐗囷紝鍏蜂綋鏄€氳繃濮挎€併€佹竻鏅板害銆侀伄鎸℃儏鍐点€佸厜鐓ф儏鍐电瓑鍙奖鍝嶄汉鑴告姄鎷嶆€ц兘鐨勫洜绱犵患鍚堣瘎浼扮殑缁撴灉
        ('byRes', C_BYTE),  # 淇濈暀
        ('dwUIDLen', C_DWORD),  # 涓婁紶鎶ヨ鐨勬爣璇嗛暱搴?
        ('pUIDBuffer', POINTER(C_BYTE)),  # 缂撳啿鍖烘寚閽堬紝瀛樻斁涓婁紶鎶ヨ鐨勬爣璇嗕俊鎭紝淇℃伅鐩稿悓琛ㄧず鍚屼竴娆℃姤璀︿笂浼犵殑缁撴灉
        ('fStayDuration', c_float),  # 鍋滅暀鐢婚潰涓椂闂?鍗曚綅锛氱)
        ('pBuffer1', POINTER(C_BYTE)),  # 鎶撴媿浜鸿劯瀛愬浘鐨勫浘鐗囨暟鎹?
    ]


# 闈炴巿鏉冨悕鍗曟姤璀︿俊鎭粨鏋勪綋銆?
class NET_VCA_BLOCKLIST_INFO_ALARM(Structure):
    _fields_ = [
        ('struBlockListInfo', NET_VCA_BLOCKLIST_INFO),  # 闈炴巿鏉冨悕鍗曞熀鏈俊鎭?
        ('dwBlockListPicLen', C_DWORD),  # 闈炴巿鏉冨悕鍗曚汉鑴稿瓙鍥剧殑闀垮害锛屼负0琛ㄧず娌℃湁鍥剧墖锛屽ぇ浜?琛ㄧず鏈夊浘鐗?
        ('dwFDIDLen', C_DWORD),  # 浜鸿劯搴揑D闀垮害
        ('pFDID', POINTER(C_BYTE)),  # 浜鸿劯搴揑D鏁版嵁缂撳啿鍖烘寚閽?
        ('dwPIDLen', C_DWORD),  # 浜鸿劯搴撳浘鐗嘔D闀垮害
        ('pPID', POINTER(C_BYTE)),  # 浜鸿劯搴撳浘鐗嘔D鎸囬拡
        ('wThresholdValue', C_WORD),  # 浜鸿劯搴撻槇鍊硷紝鍙栧€艰寖鍥达細[0,100]
        ('byRes', C_BYTE * 2),  # 淇濈暀
        ('pBuffer1', POINTER(C_BYTE)),  # 闈炴巿鏉冨悕鍗曚汉鑴稿瓙鍥剧殑鍥剧墖鏁版嵁
    ]  # 浜鸿劯姣斿鎶ヨ淇℃伅


# 浜鸿劯瀵规瘮鍙傛暟缁撴瀯浣?
class NET_VCA_FACESNAP_MATCH_ALARM(Structure):
    _fields_ = [
        ('dwSize', C_DWORD),  # 缁撴瀯浣撳ぇ灏?
        ('fSimilarity', c_float),  # 鐩镐技搴︼紝鍙栧€艰寖鍥达細[0.001,1]
        ('struSnapInfo', NET_VCA_FACESNAP_INFO_ALARM),  # 浜鸿劯鎶撴媿涓婁紶淇℃伅
        ('struBlockListInfo', NET_VCA_BLOCKLIST_INFO_ALARM),  # 浜鸿劯姣斿鎶ヨ淇℃伅
        ('sStorageIP', c_char * 16),  # 瀛樺偍鏈嶅姟IP鍦板潃
        ('wStoragePort', C_WORD),  # 瀛樺偍鏈嶅姟绔彛鍙?
        ('byMatchPicNum', C_BYTE),  # 鍖归厤鍥剧墖鐨勬暟閲忥紝0鏄繚鐣欏€硷紙涓嶆敮鎸佽瀛楁鐨勮澶囷紝璇ュ€奸粯璁や负0锛涙敮鎸佽瀛楁鐨勮澶囷紝璇ュ€间负0鏃惰〃绀哄悗缁病鏈夊尮閰嶇殑鍥剧墖淇℃伅锛?
        ('byPicTransType', C_BYTE),  # 鍥剧墖鏁版嵁浼犺緭鏂瑰紡: 0- 浜岃繘鍒讹紝1- URL璺緞(HTTP鍗忚鐨勫浘鐗嘦RL)
        ('dwSnapPicLen', C_DWORD),  # 璁惧璇嗗埆鎶撴媿鍥剧墖闀垮害
        ('pSnapPicBuffer', POINTER(C_BYTE)),  # 璁惧璇嗗埆鎶撴媿鍥剧墖鎸囬拡
        ('struRegion', NET_VCA_RECT),  # 璁惧璇嗗埆鎶撴媿鍥剧墖涓汉鑴稿瓙鍥惧潗鏍囷紝鍙互鏍规嵁璇ュ潗鏍囦粠鎶撴媿鍥剧墖涓婃姞鍙栦汉鑴稿皬鍥剧墖
        ('dwModelDataLen', C_DWORD),  # 寤烘ā鏁版嵁闀垮害
        ('pModelDataBuffer', POINTER(C_BYTE)),  # 寤烘ā鏁版嵁鎸囬拡
        ('byModelingStatus', C_BYTE),  # 寤烘ā鐘舵€?
        ('byLivenessDetectionStatus', C_BYTE),  # 娲讳綋妫€娴嬬姸鎬侊細0-淇濈暀锛?-鏈煡锛堟娴嬪け璐ワ級锛?-闈炵湡浜轰汉鑴革紝3-鐪熶汉浜鸿劯锛?-鏈紑鍚椿浣撴娴?
        ('cTimeDifferenceH', c_char),  # 涓嶶TC鐨勬椂宸紙灏忔椂锛夛紝-12 ... +14锛?琛ㄧず涓滃尯锛?xff鏃犳晥
        ('cTimeDifferenceM', c_char),  # 涓嶶TC鐨勬椂宸紙鍒嗛挓锛夛紝-30, 30, 45锛?琛ㄧず涓滃尯锛?xff鏃犳晥
        ('byMask', C_BYTE),  # 鎶撴媿鍥炬槸鍚︽埓鍙ｇ僵锛?-淇濈暀锛?-鏈煡锛?-涓嶆埓鍙ｇ僵锛?-鎴村彛缃?
        ('bySmile', C_BYTE),  # 鎶撴媿鍥炬槸鍚﹀井绗戯紝0-淇濈暀锛?-鏈煡锛?-涓嶅井绗戯紝3-寰瑧
        ('byContrastStatus', C_BYTE),  # 姣斿缁撴灉锛?-淇濈暀锛?-姣斿鎴愬姛锛?-姣斿澶辫触
        ('byBrokenNetHttp', C_BYTE),  # 鏂綉缁紶鏍囧織浣嶏細0- 涓嶆槸閲嶄紶鏁版嵁锛?- 閲嶄紶鏁版嵁
    ]


LPNET_DVR_LOCAL_GENERAL_CFG = POINTER(NET_DVR_LOCAL_GENERAL_CFG)


# 浠ュお缃戦厤缃粨鏋勪綋銆?
class NET_DVR_ETHERNET(Structure):
    _fields_ = [
        ('sDVRIP', c_char * 16),  # 璁惧IP鍦板潃
        ('sDVRIPMask', c_char * 16),  # 璁惧IP鍦板潃鎺╃爜
        ('dwNetInterface', C_DWORD),  # 缃戠粶鎺ュ彛锛?-10MBase-T锛?-10MBase-T鍏ㄥ弻宸ワ紱3-100MBase-TX锛?-100M鍏ㄥ弻宸ワ紱5-10M/100M鑷€傚簲
        ('wDVRPort', C_WORD),  # 璁惧绔彛鍙?
        ('byMACAddr', C_BYTE * 6)  # 璁惧鐗╃悊鍦板潃
    ]


# 缃戠粶閰嶇疆缁撴瀯浣撱€?
class NET_DVR_NETCFG(Structure):
    _fields_ = [
        ('dwSize', C_DWORD),  # 缁撴瀯浣撳ぇ灏?
        ('struEtherNet', NET_DVR_ETHERNET * 2),  # 浠ュお缃戝彛
        ('sManageHostIP', c_char * 16),  # 杩滅▼绠＄悊涓绘満鍦板潃
        ('wManageHostPort', C_WORD),  # 杩滅▼绠＄悊涓绘満绔彛鍙?
        ('sIPServerIP', c_char * 16),  # IPServer鏈嶅姟鍣ㄥ湴鍧€
        ('sMultiCastIP', c_char * 16),  # 澶氭挱缁勫湴鍧€
        ('sGatewayIP', c_char * 16),  # 缃戝叧鍦板潃
        ('sNFSIP', c_char * 16),  # NFS涓绘満IP鍦板潃
        ('sNFSDirectory', C_BYTE * 128),  # NFS鐩綍
        ('dwPPPOE', C_DWORD),  # 0-涓嶅惎鐢?1-鍚敤
        ('sPPPoEUser', C_BYTE * 32),  # PPPoE鐢ㄦ埛鍚?
        ('sPPPoEPassword', c_char * 16),  # PPPoE瀵嗙爜
        ('sPPPoEIP', c_char * 16),  # PPPoE IP鍦板潃(鍙)
        ('wHttpPort', C_WORD)  # HTTP绔彛鍙?
    ]


LPNET_DVR_NETCFG = POINTER(NET_DVR_NETCFG)


# 浠ュお缃戦厤缃粨鏋勪綋銆?
class NET_DVR_ETHERNET_V30(Structure):
    _fields_ = [
        ('struDVRIP', NET_DVR_IPADDR),  # 璁惧IP鍦板潃
        ('struDVRIPMask', NET_DVR_IPADDR),  # 璁惧IP鍦板潃鎺╃爜
        ('dwNetInterface', C_DWORD),
        # 缃戠粶鎺ュ彛锛?-10MBase-T锛?-10MBase-T鍏ㄥ弻宸ワ紱3-100MBase-TX锛?-100M鍏ㄥ弻宸ワ紱5-10M/100M/1000M鑷€傚簲锛?-1000M鍏ㄥ弻宸?
        ('wDVRPort', C_WORD),  # 璁惧绔彛鍙?
        ('wMTU', C_WORD),  # MTU璁剧疆锛岄粯璁?500
        ('byMACAddr', C_BYTE * 6),  # 璁惧鐗╃悊鍦板潃
        ('byEthernetPortNo', C_BYTE),  # 缃戝彛鍙凤紝0-鏃犳晥锛?-缃戝彛0锛?-缃戝彛1浠ユ绫绘帹锛屽彧璇?
        ('byRes', C_BYTE * 1),
    ]


# PPPoE閰嶇疆缁撴瀯浣撱€?
class NET_DVR_PPPOECFG(Structure):
    _fields_ = [
        ('dwPPPOE', C_DWORD),  # 鏄惁鍚敤PPPoE锛?-涓嶅惎鐢紝1-鍚敤
        ('sPPPoEUser', C_BYTE * 32),  # PPPoE鐢ㄦ埛鍚?
        ('sPPPoEPassword', c_char * 16),  # PPPoE瀵嗙爜
        ('struPPPoEIP', NET_DVR_IPADDR),  # PPPoE IP鍦板潃
    ]


# 缃戠粶閰嶇疆缁撴瀯浣撱€?
class NET_DVR_NETCFG_V50(Structure):
    _fields_ = [
        ('dwSize', C_DWORD),  # 缁撴瀯浣撳ぇ灏?
        ('struEtherNet', NET_DVR_ETHERNET_V30 * 2),  # 浠ュお缃戝彛
        ('struRes1', NET_DVR_IPADDR * 2),  #
        ('struAlarmHostIpAddr', NET_DVR_IPADDR),  #
        ('byRes2', C_BYTE * 4),  #
        ('wAlarmHostIpPort', C_WORD),  # 鎶ヨ涓绘満绔彛鍙?
        ('byUseDhcp', C_BYTE),  # 鏄惁鍚敤DHCP 0xff-鏃犳晥 0-涓嶅惎鐢?1-鍚敤
        ('byIPv6Mode', C_BYTE),  # IPv6鍒嗛厤鏂瑰紡锛?-璺敱鍏憡锛?-鎵嬪姩璁剧疆锛?-鍚敤DHCP鍒嗛厤
        ('struDnsServer1IpAddr', NET_DVR_IPADDR),  # 鍩熷悕鏈嶅姟鍣?鐨処P鍦板潃
        ('struDnsServer2IpAddr', NET_DVR_IPADDR),  # 鍩熷悕鏈嶅姟鍣?鐨処P鍦板潃
        ('byIpResolver', C_BYTE * 64),  # IP瑙ｆ瀽鏈嶅姟鍣ㄥ煙鍚嶆垨IP鍦板潃
        ('wIpResolverPort', C_WORD),  # IP瑙ｆ瀽鏈嶅姟鍣ㄧ鍙ｅ彿
        ('wHttpPortNo', C_WORD),  # HTTP绔彛鍙?
        ('struMulticastIpAddr', NET_DVR_IPADDR),  # 澶氭挱缁勫湴鍧€
        ('struGatewayIpAddr', NET_DVR_IPADDR),  # 缃戝叧鍦板潃
        ('struPPPoE', NET_DVR_PPPOECFG),  #
        ('byEnablePrivateMulticastDiscovery', C_BYTE),  # 绉佹湁澶氭挱鎼滅储锛?~榛樿锛?~鍚敤锛?-绂佺敤
        ('byEnableOnvifMulticastDiscovery', C_BYTE),  # Onvif澶氭挱鎼滅储锛?~榛樿锛?~鍚敤锛?-绂佺敤
        ('wAlarmHost2IpPort', C_WORD),  # 鎶ヨ涓绘満2绔彛鍙?
        ('struAlarmHost2IpAddr', NET_DVR_IPADDR),  # 鎶ヨ涓绘満2 IP鍦板潃
        ('byEnableDNS', C_BYTE),  # DNS浣胯兘, 0-鍏抽棴锛?-鎵撳紑
        ('byRes', C_BYTE * 599),  # DNS浣胯兘, 0-鍏抽棴锛?-鎵撳紑
    ]


# 瀹氫箟棰勮鍙傛暟缁撴瀯浣?
class NET_DVR_PREVIEWINFO(Structure):
    _fields_ = [
        ('lChannel', C_LONG),  # 閫氶亾鍙?
        ('dwStreamType', C_DWORD),  # 鐮佹祦绫诲瀷锛?-涓荤爜娴侊紝1-瀛愮爜娴侊紝2-鐮佹祦3锛?-鐮佹祦4, 4-鐮佹祦5,5-鐮佹祦6,7-鐮佹祦7,8-鐮佹祦8,9-鐮佹祦9,10-鐮佹祦10
        ('dwLinkMode', C_DWORD),
        # 0锛歍CP鏂瑰紡,1锛歎DP鏂瑰紡,2锛氬鎾柟寮?3 - RTP鏂瑰紡锛?-RTP/RTSP,5-RSTP/HTTP ,6- HRUDP锛堝彲闈犱紶杈擄級 ,7-RTSP/HTTPS
        ('hPlayWnd', C_HWND),  # 鎾斁绐楀彛鐨勫彞鏌?涓篘ULL琛ㄧず涓嶆挱鏀惧浘璞?
        ('bBlocked', C_BOOL),  # 0-闈為樆濉炲彇娴? 1-闃诲鍙栨祦, 濡傛灉闃诲SDK鍐呴儴connect澶辫触灏嗕細鏈?s鐨勮秴鏃舵墠鑳藉杩斿洖,涓嶉€傚悎浜庤疆璇㈠彇娴佹搷浣?
        ('bPassbackRecord', C_BOOL),  # 0-涓嶅惎鐢ㄥ綍鍍忓洖浼?1鍚敤褰曞儚鍥炰紶
        ('byPreviewMode', C_BYTE),  # 棰勮妯″紡锛?-姝ｅ父棰勮锛?-寤惰繜棰勮
        ('byStreamID', C_BYTE * 32),  # 娴両D锛宭Channel涓?xffffffff鏃跺惎鐢ㄦ鍙傛暟
        ('byProtoType', C_BYTE),  # 搴旂敤灞傚彇娴佸崗璁紝0-绉佹湁鍗忚锛?-RTSP鍗忚,
        # 2-SRTP鐮佹祦鍔犲瘑锛堝搴旀缁撴瀯浣撲腑dwLinkMode 瀛楁锛屾敮鎸佸涓嬫柟寮? 涓?锛岃〃绀簎dp浼犺緭鏂瑰紡锛屼俊浠よ蛋TLS鍔犲瘑锛岀爜娴佽蛋SRTP鍔犲瘑锛屼负2锛岃〃绀哄鎾紶杈撴柟寮忥紝淇′护璧癟LS鍔犲瘑锛岀爜娴佽蛋SRTP鍔犲瘑锛?
        ('byRes1', C_BYTE),
        ('byVideoCodingType', C_BYTE),  # 鐮佹祦鏁版嵁缂栬В鐮佺被鍨?0-閫氱敤缂栫爜鏁版嵁 1-鐑垚鍍忔帰娴嬪櫒浜х敓鐨勫師濮嬫暟鎹?
        ('dwDisplayBufNum', C_DWORD),  # 鎾斁搴撴挱鏀剧紦鍐插尯鏈€澶х紦鍐插抚鏁帮紝鑼冨洿1-50锛岀疆0鏃堕粯璁や负1
        ('byNPQMode', C_BYTE),  # NPQ鏄洿杩炴ā寮忥紝杩樻槸杩囨祦濯掍綋锛?-鐩磋繛 1-杩囨祦濯掍綋
        ('byRecvMetaData', C_BYTE),  # 鏄惁鎺ユ敹metadata鏁版嵁
        # 璁惧鏄惁鏀寔璇ュ姛鑳介€氳繃GET /ISAPI/System/capabilities 涓璂eviceCap.SysCap.isSupportMetadata鏄惁瀛樺湪涓斾负true
        ('byDataType', C_BYTE),  # 鏁版嵁绫诲瀷锛?-鐮佹祦鏁版嵁锛?-闊抽鏁版嵁
        ('byRes', C_BYTE * 213),
    ]


LPNET_DVR_PREVIEWINFO = POINTER(NET_DVR_PREVIEWINFO)

# 鎶ヨ淇℃伅鍥炶皟鍑芥暟
MSGCallBack_V31 = fun_ctype(c_bool, C_LONG, LPNET_DVR_ALARMER, c_void_p, C_DWORD, c_void_p)

# 鐮佹祦鍥炶皟鍑芥暟
REALDATACALLBACK = fun_ctype(None, C_LONG, C_DWORD, POINTER(C_BYTE), C_DWORD, c_void_p)
