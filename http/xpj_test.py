import requests
import time
import hashlib

# 开发者配置（替换为自己的信息）
USER = "1911342262@qq.com"  # 替换为实际用户邮箱
USER_KEY = "xxx"  # 替换为实际用户密钥
'''
接口地址:
'''
ADD_PRINTER_URL = "https://open.xpyun.net/api/openapi/xprinter/addPrinters"
XP_PRINT_URL = "https://open.xpyun.net/api/openapi/xprinter/print"


# xp_print 参数
VOICE_MODE_CANCEL = 0
VOICE_MODE_MUTE = 1
VOICE_MODE_PLAY = 2

XP_PRINT_DATA = '''
<C>
<BOLD>
<B2>美团</B2>
<B>漱玉平民大药房</B>
</BOLD>
<C>
<BR>
<L>
<B><BOLD>商品详情:</BOLD></B>
<N>
货号: xxxxxx    <BOLD>货位: FXXXX</BOLD>
品名: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
生产单位: xxxxxxxxxxxxxxxxxxxxxxx有限公司
规格: 50ml
<BOLD>数量: x   批号: XXXXXXXXX</BOLD>
<BOLD>--------------------------------</BOLD>
货号: xxxxxx    <BOLD>货位: FXXXX</BOLD>
品名: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
生产单位: xxxxxxxxxxxxxxxxxxxxxxx有限公司
规格: 5mg
<BOLD>数量: x   批号: XXXXXXXXX</BOLD>
<BOLD>--------------------------------</BOLD>
</N>
<B><BOLD>发票提取码:</BOLD></B>
<N>
2819xxxxxxxxxxxx
发票提取码是获取发票的唯一凭证请妥善保管
<BOLD>--------------------------------</BOLD>
温馨提醒:如需发票请扫描下方二维码
<QRCODE s=12 e=L l=center>这是一个二维码</QRCODE>
-- 以上部分请放入打包袋内 --
</N>
</L>
'''

def get_common_params() -> dict:
    """构造请求公共参数"""
    timestamp = str(int(time.time()))  # 10位UNIX时间戳
    
    raw_str = USER + USER_KEY + timestamp
    sha1 = hashlib.sha1(raw_str.encode("utf-8"))

    sign = sha1.hexdigest().lower()
    return {
        "user": USER,
        "timestamp": timestamp,
        "sign": sign,
        "debug": "0"
    }

def add_printer(printers: list) -> dict:
    """
    批量添加打印机
    :param printers: 打印机列表，每个元素为包含"sn"和"name"的字典
    :return: 接口返回结果

    调用示例
    printer_list = [
        {"sn": "36R0T38XWN71149", "name": "Selftest"}
    ]
    batch_add_result = batch_add_printer(printer_list)
    print("批量添加打印机结果：", batch_add_result)
    
    """
    url = f"{ADD_PRINTER_URL}"
    params = get_common_params()
    # 添加批量打印机私有参数（items列表）
    params.update({
        "items": printers
    })
    # 发送POST请求
    response = requests.post(url, json=params, headers={"Content-Type": "application/json;charset=UTF-8"})
    return response.json()

def xp_print(data: list, content: str) -> dict:
    
    url = f"{XP_PRINT_URL}"
    params = get_common_params()

    params.update(data)
    params["content"] = content
    # print("打印参数：", params)

    # 发送POST请求
    response = requests.post(url, json=params, headers={"Content-Type": "application/json;charset=UTF-8"})
    return response.json()
    
if __name__ == "__main__":


    xp_print_data = {
        "sn": "36R0T38XWN71149",
        "voice": VOICE_MODE_MUTE,
    }

    result = xp_print(data=xp_print_data, content=XP_PRINT_DATA)
    print("r:", result)
