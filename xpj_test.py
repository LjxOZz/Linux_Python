import requests
import time
import hashlib

# 开发者配置（替换为自己的信息）
USER = "1911342262@qq.com"  # 替换为实际用户邮箱
USER_KEY = "eebc89e280ba47c5a12d6dc750348811"  # 替换为实际用户密钥
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
<IMG></IMG>
<CB>**#8 美团**
<L><N>--------------------------------
<CB>--在线支付--
<HB>芯烨云小票
<L><N>下单时间:2019年09月06日15时35分
订单编号:5842160392535156
**************商品**************
<C><HB>---1号口袋---
<L><N>红焖猪手砂锅饭            x1 19
牛肉                      x1 8
--------------------------------
配送费:￥4
--------------------------------
<B>小计:￥31
折扣:￥4
<L><N>********************************
<B>订单总价:￥27

<N>香洲花园 5栋6单元1404号
肖(女士):135-4444-6666
订单备注：[用餐人数]1人;
少放辣椒
<C><HB>**#8 完**
<L><N>二维码打印测试
<L><QRCODE s=6 e=L l=center>https://www.xpyun.net/open/index.html</QRCODE>
<R><N>条形码打印测试
<R><BARCODE t=CODE128 w=2 h=100 p=2>5842160392535156</BARCODE>
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
