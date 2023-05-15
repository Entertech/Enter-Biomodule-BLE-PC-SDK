from math import exp
import struct
from typing import Optional, Callable

from bleak.backends.client import BaseBleakClient

from enterble.collector.collector import Collector


# Flowtime 采集器 适配器
class FlowtimeCollector(Collector):

    # 通知特征表
    NOTIFY_UUID = {
        # 电量特征
        'SOC': '00002A19-0000-1000-8000-00805F9B34FB',
        # 穿戴状态特征
        'WEAR': '0000ff32-1212-abcd-1523-785feabcd123',
        # EEG 特征
        'EEG': '0000ff31-1212-abcd-1523-785feabcd123',
        # HR 特征
        'HR': '0000ff51-1212-abcd-1523-785feabcd123'
    }

    # 数据写入设备特征
    DOWN_CODE_UUID = '0000ff21-1212-abcd-1523-785feabcd123'

    # 数据写入设备特征码
    class DownCode(object):

        # 开始 EEG 采集
        START_EEG = 0x01
        # 停止 EEG 采集
        STOP_EEG = 0x02
        # 开始 HR 采集
        START_HR = 0x03
        # 停止 HR 采集
        STOP_HR = 0x04
        # 开始 全部 采集
        START_ALL = 0x05
        # 停止 全部 采集
        STOP_ALL = 0x06

        LIGHT_FLASHING = 0x07

    def __init__(
        self,
        model_nbr_uuid: str,
        device_identify: str,
        device_disconnected_callback: Optional[Callable[["BaseBleakClient"], None]],
        soc_data_callback: callable,
        wear_status_callback: callable,
        eeg_data_callback: callable,
        hr_data_callback: callable,
        name: str = None,
    ) -> None:
        """采集器初始化

        Args:
            name (str): 设备名称(不知道设备名, 可以不指定)
            model_nbr_uuid (str): 设备广播 UUID
            device_identify (str): 设备标识
            device_disconnected_callback (Optional[Callable[["BaseBleakClient"], None]]): 设备断开回调
            soc_data_callback (callable): 电量数据回调
            wear_status_callback (callable): 穿戴状态回调
            eeg_data_callback (callable): EEG 数据回调
            hr_data_callback (callable): HR 数据回调
        """
        self.device_disconnected_callback = device_disconnected_callback
        self.soc_data_callback = soc_data_callback
        self.wear_status_callback = wear_status_callback
        self.eeg_data_callback = eeg_data_callback
        self.hr_data_callback = hr_data_callback

        notify_callback_table = {
            self.NOTIFY_UUID['SOC']: self._soc_notify_callback,
            self.NOTIFY_UUID['WEAR']: self._wear_notify_callback,
            self.NOTIFY_UUID['EEG']: self._eeg_notify_callback,
            self.NOTIFY_UUID['HR']: self._hr_notify_callback,
        }
        after_notify_callback_table = {
            self.DOWN_CODE_UUID: struct.pack('>B', self.DownCode.START_ALL),
        }
        super().__init__(
            name=name,
            model_nbr_uuid=model_nbr_uuid,
            device_identify=device_identify,
            device_disconnected_callback=device_disconnected_callback,
            notify_callback_table=notify_callback_table,
            before_notify_callback_table=None,
            after_notify_callback_table=after_notify_callback_table,
            soc_cal_call=self.soc_cal,
        )

    async def soc_cal(self, data):
        """电量计算

        Args:
            data (int): 电量数据
        """
        voltage = float(data) / 100.0 + 3.1
        a1: float = 99.84
        b1: float = 4.244
        c1: float = 0.3781
        a2: float = 21.38
        b2: float = 3.953
        c2: float = 0.1685
        a3: float = 15.21
        b3: float = 3.813
        c3: float = 0.09208

        a1_q = a1 * exp(-pow((voltage - b1) / c1, 2))
        a2_q = a2 * exp(-pow((voltage - b2) / c2, 2))
        a3_q = a3 * exp(-pow((voltage - b3) / c3, 2))

        q = a1_q + a2_q + a3_q
        q = q * 1.13 - 5
        return max(min(q, 100), 0)

    async def _soc_notify_callback(self, sender: int, data: bytearray):
        """电量通知回调

        Args:
            sender (int): 发送者
            data (bytearray): 数据
        """
        soc_data = struct.unpack('>B', data)[0]
        soc_percentage = await self.soc_cal(soc_data)
        await self.device.soc.update_soc(soc_percentage)
        await self.soc_data_callback(soc_percentage)

    async def _wear_notify_callback(self, sender: int, data: bytearray):
        """穿戴状态通知回调

        Args:
            sender (int): 发送者
            data (bytearray): 数据
        """
        status = struct.unpack('>B', data)[0] == 0
        await self.wear_status_callback(status)

    async def _eeg_notify_callback(self, sender: int, data: bytearray):
        """EEG 通知回调

        Args:
            sender (int): 发送者
            data (bytearray): 数据
        """
        eeg_data = struct.unpack('>20B', data)
        await self.eeg_data_callback(eeg_data)

    async def _hr_notify_callback(self, sender: int, data: bytearray):
        """HR 通知回调

        Args:
            sender (int): 发送者
            data (bytearray): 数据
        """
        hr_data = struct.unpack('>B', data)[0]
        await self.hr_data_callback(hr_data)
