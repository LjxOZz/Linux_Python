
import can
from typing import Optional, List, Union
'''

sudo ip link set can1 down
sudo ip link set can1 type can bitrate 500000
sudo ip link set can1 up
'''

class SocketCAN:
    """
    支持标准CAN/CAN_FD
    """
    def __init__(self, channel: str = "can0", bitrate: int = 1000000, is_fd: bool = False):
        self.channel = channel
        self.bitrate = bitrate
        self.is_fd = is_fd
        self.bus: Optional[can.Bus] = None

    def connect(self) -> bool:
        try:
            bus_config = {"interface": "socketcan","channel": self.channel,
                          "bitrate": self.bitrate,"fd": self.is_fd }
            
            if self.is_fd:
                bus_config["data_bitrate"] = 5000000

            self.bus = can.Bus(**bus_config)
            return True
        except Exception as e:
            return False

    def send_msg(self, can_id: int, data: Union[List[int], bytes], 
                 is_extended_id: bool = False, timeout: float = 0.2) -> bool:
        
        if not self.bus:
            return False
        msg = can.Message(arbitration_id=can_id, data=data, is_extended_id=is_extended_id, is_fd=self.is_fd)
        try:
            self.bus.send(msg, timeout=timeout)
            return True
        except can.CanError:
            return False
        
    def recv_msg(self, timeout: float = 0.1):
        if not self.bus:
            return False
        
        msg = self.bus.recv(timeout)
        # print("msg的所有属性", dir(msg))
        # print("msg内容      ", msg)
        if msg is None:
            print(f"[WARNING] 接收CAN消息超时(超时时间:{timeout}s)")
            return []
        
        # 转化为16进制
        hex_list = [hex(b) for b in msg.data]
        return hex_list
    
    def disconnect(self):
        if self.bus:
            self.bus.shutdown()


if __name__ == "__main__":
    # 1. 初始化发送器（标准CAN模式）
    can_sender = SocketCAN(channel="can1", bitrate=1000000, is_fd=False)
    # 2. 连接总线
    if not can_sender.connect():
        exit(1)

    try:
        can_sender.send_msg(can_id=0x601, data=[0x40, 0x60, 0x63])
        can_sender.recv_msg(can_id=0x601)

    except KeyboardInterrupt:
        print("\n用户中断程序")
    finally:
        can_sender.disconnect()
    