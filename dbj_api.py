#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
打包机API测试脚本

注意:
    1,x86上关闭防火墙,处于同一网段下
    2,打开机器软件配置好 封包方式改为指令封包
    3,机器红外光前不能有反射物体,会导致机器一直反转

"""

import requests
import sys      # 处理命令行参数
import time

class BalerPrinter:
    """
    打包机打印机操作类
    封装打包机的所有API操作
    """

    def __init__(self, base_url="http://10.128.0.128:9000", send_data=None):
        """
        初始化打包机操作类

        Args:
            base_url: API基础地址
            self.test_data: 测试数据，如果不提供则使用默认数据
        """
        self.base_url = base_url
        self.send_data = send_data or {
            "ticket_info": {
                "order_source": "Test_Data",
                "order_no": "601827061572981635",
                "order_time": "2025-10-20 19:02:26"
            }
        }
    
    def baler_status(self):
        """查询打包机状态"""
        print("=== 查询打包机状态 ===")
        try:
            response = requests.post(
                f"{self.base_url}/api/baler_status",
                json=self.send_data,
                headers={"Content-Type": "application/json"}
            )

            print(f"状态码: {response.status_code}")
            print(f"响应: {response.text}")

            if response.status_code == 200:
                result = response.json()
                print(f"Success: {result.get('Success', False)}")
                print(f"Message: {result.get('Message', '')}")
                print(f"Data: {result.get('Data', '')}")
                return result
            else:
                print("✗ 状态查询失败")
                return None

        except Exception as e:
            print(f"✗ 请求失败: {str(e)}")
            return None

    def start_pack(self):
        """开始打包 - 等待接收返回值"""
        print("\n=== 开始打包 ===")
        
        try:
            response = requests.post(
                f"{self.base_url}/api/start_pack",
                json=self.send_data,
                headers={"Content-Type": "application/json"},
                timeout=30
            )

            print(f"状态码: {response.status_code}")
            print(f"响应: {response.text}")

            if response.status_code == 200:
                result = response.json()
                success = result.get('Success', False)

                print(f"Success: {success}")
                print(f"Message: {result.get('Message', '')}")
                print(f"Data: {result.get('Data', '')}")

            if success:
                print("✓ 开始打包成功，接收到有效返回值")
                return result
                

        except requests.exceptions.Timeout:
            print(f"start")
            
        return None

    def end_pack(self):
        """结束打包"""
        print("\n=== 结束打包 ===")
        try:
            response = requests.post(
                f"{self.base_url}/api/end_pack",
                json=self.send_data,
                headers={"Content-Type": "application/json"}
            )

            print(f"状态码: {response.status_code}")
            print(f"响应: {response.text}")

            if response.status_code == 200:
                result = response.json()
                print(f"Success: {result.get('Success', False)}")
                print(f"Message: {result.get('Message', '')}")
                print(f"Data: {result.get('Data', '')}")
                return result
            else:
                print("✗ 结束打包失败")
                return None

        except Exception as e:
            print(f"✗ 请求失败: {str(e)}")
            return None
        

if __name__ == "__main__":

    if len(sys.argv) != 2:
        print("使用方法:")
        print("  python3 dbj_api.py status  # 查询打包机状态")
        print("  python3 dbj_api.py start   # 开始打包")
        print("  python3 dbj_api.py end     # 结束打包")
        sys.exit(1)  # 参数错误，退出程序
    
    # 2. 获取指令参数
    cmd = sys.argv[1].lower()  # 转为小写，兼容大小写输入（如Start/START）
    
    printer = BalerPrinter()
    
    # 4. 根据指令执行对应方法
    if cmd == "status":
        printer.baler_status()
    elif cmd == "start":
        printer.start_pack()
    elif cmd == "end":
        printer.end_pack()
    else:
        print(f"✗ 无效指令: {cmd}")
        print("支持的指令：status / start / end")
        sys.exit(1)
    
    print("\n 操作完成 ")


'''
执行start操作时: 一定要机器完成操作后再执行end操作,否则end操作可能不执行
'''
