import logging
import time
import ctypes

from typing import List

from socketcan import SocketCAN

#第三代升降电机
#位置  inc(0 -> 4571136) == mm(0 -> 465) --->  (1mm == 9830.4inc)
#速度  1mm/s = 9.0009rpm  -> (1m/s = 1000mm/s = 9000.9rpm)

class KincoObject:
    ''' ---------------------- ControlWord --------------------- '''
    CONTROL_WORD = [0x40, 0x60, 0x00]
    ''' ---------------------- Status Word --------------------- '''
    STATUS_WORD = [0x41, 0x60, 0x00]
    ''' ----------------------- Work Mode ---------------------- '''
    WORK_MODE = [0x60, 0x60, 0x00]
    ''' ------------------------- Basic ------------------------ '''
    POS_ACTUAL = [0x63, 0x60, 0x00]         # 实际位置
    POS_TARGET = [0x7A, 0x60, 0x00]         # 目标位置
    SPEED_ACTUAL = [0x6C, 0x60, 0x00]       # 实际速度
    SPEED_TARGET = [0xFF, 0x60, 0x00]       # 目标速度
    CURRENT_ACTUAL = [0x78, 0x60, 0x00]     # 实际电流
    CURRENT_TARGET = [0xF6, 0x60, 0x08]     # 目标电流
    ''' ------------------------- Limit ------------------------ '''
    CURRENT_LIMIT = [0x60, 0x73, 0x00]      # 目标电流限制
    POS_SOFT_LIMIT = [0x60, 0x7D, 0x01]     # 软限位正设置
    NEG_SOFT_LIMIT = [0x60, 0x7D, 0x02]     # 软限位负设置
    SPEED_LIMIT = [0x60, 0x80, 0x00]        # 最大速度限制
    ''' ------------------------- Error ------------------------ '''
    ERROR_CODE1 = [0x01, 0x26, 0x00]
    ERROR_CODE2 = [0x02, 0x26, 0x00]

class KincoCanController:
    def __init__(self, channel, id, bitrate):
        self.kinco_motor = SocketCAN(channel=channel, bitrate=bitrate, is_fd=False)

        self.node_id = id
        self.master_cob_id = 0x600 + self.node_id 
        self.slave_cob_id = 0x580 + self.node_id
        
    def __kinco_send_receive(self, send_data, timeout=0.1):

        self.kinco_motor.send_msg(can_id = self.master_cob_id, 
                                  data = send_data,
                                  is_extended_id=False
                                )
        return_data = self.kinco_motor.recv_msg(timeout)
        return return_data
    
    # ------------------------- Service Data Object ------------------------
    def __sdo_read(self, Data1_3: list[int]) -> list:
        Data0 = [0x40]
        Data4_7 = [0x00, 0x00, 0x00, 0x00]
        rev_data = self.__kinco_send_receive(send_data = Data0 + Data1_3 + Data4_7)
        logging.debug(f"__sdo_read rev_data:{rev_data}")
        
        dec_list = [int(b, 16) for b in rev_data]
        if not dec_list:
            logging.error("获取伺服数据失败:__sdo_read返回空")
            return None
        logging.debug(f"__sdo_read dec_data:{dec_list}")

        if   dec_list[0] == 0x4F: 
            Data = dec_list[4]
        elif dec_list[0] == 0x4B: 
            Data = dec_list[4] + dec_list[5]*256
        elif dec_list[0] == 0x43: 
            Data = dec_list[4] + dec_list[5]*256 + dec_list[6]*65536 + dec_list[7]*16777216
        elif dec_list[0] == 0x80:
            err_code = dec_list[4] + dec_list[5]*256 + dec_list[6]*65536 + dec_list[7]*16777216
            logging.error(f"communication err = {err_code}")
        else:
            logging.error("Accept errors")
            return -1
        return Data

    def __sdo_write(self, write_len, Data1_3, Data4_7):
        if   write_len == 1: Data0 = [0x2F]
        elif write_len == 2: Data0 = [0x2B]
        elif write_len == 4: Data0 = [0x23]
        else:
            logging.error(f"Write_len err={write_len}")
            return -1
        
        recv_data = self.__kinco_send_receive(send_data = Data0 + Data1_3 + Data4_7)
        # 这里要判断发送是否成功
        logging.debug(f"recv_data:{recv_data}")

    def __set_position_mode(self):
        sdo_data = [0x01, 0x00, 0x00, 0x00]
        return self.__sdo_write(write_len=1, Data1_3=KincoObject.WORK_MODE, Data4_7=sdo_data)
    
    def __set_control_word(self, Num):
        sdo_data = [Num, 0x00, 0x00, 0x00]
        return self.__sdo_write(write_len=2, Data1_3=KincoObject.CONTROL_WORD, Data4_7=sdo_data)
    # ------------------------- 暴露 ------------------------
    def reset_error(self):
        '''复位错误'''
        self.__set_control_word(0x86)

    def quick_stop(self):
        '''快速停止'''
        self.__set_control_word(0x0B)

    def start_move(self):
        '''开始以绝对位置模式运动'''
        self.__set_control_word(0x2F)
        self.__set_position_mode()
        self.__set_control_word(0x3F)
    
    def set_target_position(self, pos):
        '''pos: 单位inc'''
        pos_int = round(pos)
        pos_bytes = pos_int.to_bytes(4, byteorder="little", signed=True)
        sdo_data = list(pos_bytes)
        Data1 = [0x7A, 0x60, 0x00]
        return self.__sdo_write(write_len=4, Data1_3=Data1, Data4_7=sdo_data)
    
    def set_trapezoid_speed(self, speed):
        '''speed: 单位rpm'''
        pos_speed = (speed * 512 * 65536) / 1875
        speed_int = round(pos_speed)
        speed_bytes = speed_int.to_bytes(4, byteorder="little", signed=True)
        sdo_data = list(speed_bytes)
        Data1 = [0x81, 0x60, 0x00]
        return self.__sdo_write(write_len=4, Data1_3=Data1, Data4_7=sdo_data)

    def get_now_position(self):
        '''return: 单位:inc'''
        INC_uint32 = self.__sdo_read(KincoObject.POS_ACTUAL)
        INC_int32 = ctypes.c_int32(INC_uint32).value
        logging.debug(f"DEC_int32={INC_int32}")
        return INC_int32
    
    def get_now_speed(self):
        '''return: 单位:rpm''' 
        DEC_uint32 = self.__sdo_read(KincoObject.SPEED_ACTUAL)
        DEC_int32 = ctypes.c_int32(DEC_uint32).value
        logging.debug(f"DEC_int32={DEC_int32}")
        RPM = DEC_int32 * 0.00005588  # DEC=[(RPM*512*编码器分辨率)/1875]
        return RPM

    def get_err_code(self):
        '''参考手册编写错误一一对应提醒,如果是0x00 ,0x00就是没有错误'''
        err_code1 = self.__sdo_read(KincoObject.ERROR_CODE1)
        err_code2 = self.__sdo_read(KincoObject.ERROR_CODE2)
        logging.debug(f"Err_Code1={err_code1}")
        logging.debug(f"Err_Code1={err_code2}")
        return ((err_code2 << 16) | err_code1)
    
    def Open(self):
        self.kinco_motor.connect()

    def Close(self):
        self.kinco_motor.disconnect()
    
    def set_pos_speed(self, pos, speed):
        '''
        set_pos_speed函数: 以绝对位置模式控制
        pos:   范围:[0 465],单位:mm(升降柱上升下降的长度)
        speed: 范围:[0 333],单位:mm/s(升降柱上升下降的速度)
        '''
        self.__set_control_word(0x2F)
        self.__set_position_mode()
        self.set_target_position(pos*9830.4)
        self.set_trapezoid_speed(speed) 
        self.__set_control_word(0x3F)


class NmxLiftCanDevice:#(nmxrdk.LiftDevice)
    def __init__(self, config):
        self.motor = KincoCanController(config.channel, config.id, config.bitrate)
        self.motor.Open()
        self.init(config)

    def init(self, config):
        # TODO 86 清除错误 (清除错误后,必须执行这个函数)
        self.motor.reset_error()

    # def up(self, speed: float = 30, duration: float = 0.5):
    #     pass

    # def down(self, speed: float = 30, duration: float = 0.5):
    #     pass

    def go(self):
        """开始升降机构运动"""
        self.motor.start_move()

    def stop(self):
        """停止升降机构运动"""
        self.motor.quick_stop()

    def get_status(self):
        speed = self.get_speed()
        height = self.get_height()
        code = self.motor.get_err_code()
        logging.info(f"speed={speed}m/s,height={height}m,err={code}")

    def get_speed(self) -> float:
        """获取升降机构当前速度
        Returns:
            float: 当前速度，单位m/s
        """
        return (self.motor.get_now_speed() / 9000.9)

    def set_speed(self, speed: float):
        """设置升降机构速度
        Args:
            speed: 速度，单位m/s
        """
        self.motor.set_trapezoid_speed(speed*9000.9)

    def get_height(self) -> List[float]:
        """获取升降机构当前高度
        Returns:
            float: 当前高度，单位m
        """
        return (self.motor.get_now_position() / 9830400)

    def set_height(self, height: float):
        """设置升降机构高度
        Args:
            height: 目标高度，单位m
        """
        self.motor.set_target_position(height*9830400)

    def Close(self):
        self.motor.Close()



class CanConfig:
    def __init__(self):
        self.channel = "can1"   # CAN 通道名
        self.id = 0x01          # CAN 帧 ID
        self.bitrate = 500000   # 波特率


if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    config = CanConfig()

    test = NmxLiftCanDevice(config)

    test.set_height(0.465)  #465mm
    test.set_speed(0.0465)  #46.5mm/s
    test.go()

    test.get_status()
    time.sleep(10)

    test.get_status()

    test.Close()

