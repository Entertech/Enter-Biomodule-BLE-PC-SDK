from math import exp
import struct

from enterble.collector.collector import Collector


class FlowtimeCollector(Collector):

    NOTIFY_UUID = {
        'SOC': '00002A19-0000-1000-8000-00805F9B34FB',
        'WEAR': '0000ff32-1212-abcd-1523-785feabcd123',
        'EEG': '0000ff31-1212-abcd-1523-785feabcd123',
        'HR': '0000ff51-1212-abcd-1523-785feabcd123'
    }

    DOWN_CODE_UUID = '0000ff21-1212-abcd-1523-785feabcd123'

    class DownCode(object):

        START_EEG = 0x01
        STOP_EEG = 0x02
        START_HR = 0x03
        STOP_HR = 0x04
        START_ALL = 0x05
        STOP_ALL = 0x06

        LIGHT_FLASHING = 0x07

    def __init__(
        self,
        name: str,
        model_nbr_uuid: str,
        device_identify: str,
        soc_data_callback: callable,
        wear_status_callback: callable,
        eeg_data_callback: callable,
        hr_data_callback: callable,
    ) -> None:
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
            notify_callback_table=notify_callback_table,
            before_notify_callback_table=None,
            after_notify_callback_table=after_notify_callback_table,
            soc_cal_call=self.soc_cal,
        )

    async def soc_cal(self, data):
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
        soc_data = struct.unpack('>B', data)[0]
        soc_percentage = await self.soc_cal(soc_data)
        self.device.soc.update_soc(soc_percentage)
        await self.soc_data_callback(soc_percentage)

    async def _wear_notify_callback(self, sender: int, data: bytearray):
        status = struct.unpack('>B', data)[0] == 0
        await self.wear_status_callback(status)

    async def _eeg_notify_callback(self, sender: int, data: bytearray):
        eeg_data = struct.unpack('>20B', data)
        await self.eeg_data_callback(eeg_data)

    async def _hr_notify_callback(self, sender: int, data: bytearray):
        hr_data = struct.unpack('>B', data)[0]
        await self.hr_data_callback(hr_data)
