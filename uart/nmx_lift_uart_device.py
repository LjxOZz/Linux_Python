from typing import List

import serial
import logging

import nmxrdk

class KincoRS232Controller:
    def __init__(self, config):
        self.config = config
        self.ser = None
        self.recv_buffer = b""

    def init(self):
        logging.info(f"Open Kinco RS232 on {self.config.dev} at {self.config.baudrate}")
        self.ser = serial.Serial(
            port=self.config.dev,
            baudrate=self.config.baudrate,
            bytesize=8,
            parity="N",
            stopbits=1,
            timeout=0.5,
        )

    def _execute(self, hex_cmd):
        self.ser.write(bytes.fromhex(hex_cmd))
        return "recv"

    def set_control_word_2F(self):
        cmd = "7F2B4060002F00000087"
        return self._execute(cmd)

    def set_control_word_3F(self):
        cmd = "7F2B4060003F00000077"
        return self._execute(cmd)

    def set_control_word_4F(self):
        cmd = "7F2B4060004F00000067"
        return self._execute(cmd)

    def set_control_word_5F(self):
        cmd = "7F2B4060005F00000057"
        return self._execute(cmd)

    def set_control_word_103F(self):
        cmd = "7F2B4060003F10000067"
        return self._execute(cmd)

    def set_control_word_06(self):
        cmd = "7F2B40600006000000B0"
        return self._execute(cmd)

    def set_operation_mode_pos(self):
        cmd = "7F2F6060000100000091"
        return self._execute(cmd)

    def set_operation_mode_speed(self):
        cmd = "7F2F606000030000008F"
        return self._execute(cmd)

    def set_target_position_0(self):
        cmd = "7F237A60000000000084"
        return self._execute(cmd)

    def set_target_position_3584000(self):
        cmd = "7F237A600000b6360098"
        return self._execute(cmd)

    def set_target_position(self, pos):
        pos_bytes = pos.to_bytes(4, byteorder="little", signed=True)
        cmd = [0x7F, 0x23, 0x7A, 0x60, 0x00] + list(pos_bytes)
        cmd.append(self.calc_lrc(cmd))
        self.ser.write(bytes(cmd))

    def set_trapezoid_speed_200(self):
        cmd = "7F23816000039D3600A7"
        return self._execute(cmd)

    def set_trapezoid_speed(self, speed):
        target_speed = speed * 512 * 65536 / 1875
        speed_hex = int(target_speed) & 0xFFFFFFFF
        speed_bytes = speed_hex.to_bytes(4, byteorder="little")
        cmd = [0x7F, 0x23, 0x81, 0x60, 0x00] + list(speed_bytes)
        cmd.append(self.calc_lrc(cmd))
        self.ser.write(bytes(cmd))

    def set_target_speed_0(self):
        cmd = "7F23FF600000000000FF"
        return self._execute(cmd)

    def set_target_speed_r100(self):
        cmd = "7F23FF60007EB1E4FFED"
        return self._execute(cmd)

    def set_target_speed(self, speed):
        target_speed = int(speed * 512 * 65536 / 1875)
        speed_bytes = target_speed.to_bytes(4, byteorder="little", signed=True)
        cmd = [0x7F, 0x23, 0xFF, 0x60, 0x00] + list(speed_bytes)
        cmd.append(self.calc_lrc(cmd))
        self.ser.write(bytes(cmd))

    def read_frame(self):
        while True:
            frame = b""
            datastart = self.ser.read(1)
            if not datastart:
                break
            if datastart == b"\x7f":
                data1 = self.ser.read(1)
                data2 = self.ser.read(1)
                if not data1 or not data2:
                    break
                if data1[0] == 0x43 and data2[0] == 0x63:
                    frame += datastart + data1 + data2
                    temp = self.ser.read(7)
                    if len(temp) < 7:
                        break
                    frame += temp
                    return frame
        return b""

    def get_position(self) -> int:
        cmd = "7F40636000000000007E"

        self.ser.write(bytes.fromhex(cmd))

        frame = self.read_frame()
        response = frame.hex()
        if response[0:2] != "7f" or response[2:4] != "43" or response[4:6] != "63":
            return -1
        data = response[10:18]
        value = int.from_bytes(bytes.fromhex(data), byteorder="little", signed=True)
        lrc_recv = int(response[18:20], 16)
        lrc_calc = self.calc_lrc(
            [int(response[i : i + 2], 16) for i in range(0, 18, 2)]
        )
        if lrc_recv == lrc_calc:
            return value
        return -1

    # http://www.ip33.com/lrc.html
    def calc_lrc(self, cmd_bytes):
        total = sum(cmd_bytes)
        mod = total % 256
        lrc = (256 - mod) & 0xFF
        return lrc

class NmxLiftDevice(nmxrdk.LiftDevice):
    def __init__(self, config):
        self.config = config
        self.ctrl = None

    def init(self, config):
        # TODO 86 清除错误
        self.ctrl = KincoRS232Controller(self.config)
        self.ctrl.init()
        self.ctrl.set_operation_mode_pos()
        self.ctrl.set_trapezoid_speed(200)

    def up(self, speed: float = 30, duration: float = 0.5):
        """升降机构上升
        Args:
            speed: 速度百分比，0~100
            duration: 运动时间，单位：秒
        """
        self.ctrl.set_target_position(178400)
        self.ctrl.set_control_word_4F()
        self.ctrl.set_control_word_5F()

    def down(self, speed: float = 30, duration: float = 0.5):
        """升降机构下降
        Args:
            speed: 速度百分比，0~100
            duration: 运动时间，单位：秒
        """
        self.ctrl.set_target_position(-178400)
        self.ctrl.set_control_word_4F()
        self.ctrl.set_control_word_5F()

    def stop(self):
        """停止升降机构运动"""
        pass

    def get_height(self) -> List[float]:
        """获取升降机构当前高度
        Returns:
            float: 当前高度，单位m
        """
        h = [0.0, 0.0]
        pos = self.ctrl.get_position()
        if pos < 0:
            return [-1, -1]
        else:
            temp = pos / 3584000.0 * 500 / 1000
            return [temp/2.0, temp/2.0]

    def set_height(self, height: float):
        """设置升降机构高度
        Args:
            height: 目标高度，单位m
        """
        self.ctrl.set_target_position(int(height * 1000 * 3584000.0 / 500))
        self.ctrl.set_control_word_2F()
        self.ctrl.set_control_word_3F()
