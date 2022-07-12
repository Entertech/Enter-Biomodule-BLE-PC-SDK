import struct
import logging
import time

from bleak.backends.device import BLEDevice
from bleak.backends.service import BleakGATTServiceCollection
from bleak import BleakClient, BleakError


logger = logging.getLogger(__name__)


class SOC(object):
    def __init__(self, soc_cal_call: callable):
        self.soc_cal_call = soc_cal_call
        self.source_soc = None
        self.update_time = None
        self.soc_percentage = None

    async def set_soc(self, source_data):
        if self.soc_cal_call:
            self.soc_percentage = await self.soc_cal_call(source_data)
        else:
            self.soc_percentage = source_data
        self.source_soc = source_data
        self.update_time = time.time()

    async def update_soc(self, soc_percentage):
        self.soc_percentage = soc_percentage
        self.update_time = time.time()

    def __str__(self) -> str:
        return 'SOC: remain > %s | time > %s' % (self.soc_percentage, self.update_time)


class Device(object):

    def __init__(self, device: BLEDevice, soc_cal_call: callable = None) -> None:
        self.device: BLEDevice = device
        self.soc_col_call: callable = soc_cal_call
        self.soc: SOC = SOC(soc_cal_call)
        self._client: BleakClient = None
        self.connected: bool = False
        logger.info(f'Device initialized: {self}')

    async def set_soc_cal_call(self, callback: callable):
        self.soc.soc_cal_call = callback

    @property
    def identify(self):
        return self.device.address

    def __str__(self) -> str:
        return f'{self.device}'

    async def connect(self) -> None:
        logger.info(f'Connecting to {self}')
        self._client = BleakClient(self.identify)
        await self._client.connect()
        self.connected = True
        logger.info(f'Connected to {self}')

    async def disconnect(self) -> None:
        logger.info(f'Disconnecting from {self}')
        if self._client:
            await self._client.disconnect()
        self.connected = False
        logger.info(f'Disconnected from {self}')

    async def client(self) -> BleakClient:
        if self._client and self.connected:
            return self._client
        await self.connect()
        return self._client

    async def get_services(self) -> BleakGATTServiceCollection:
        return await (await self.client()).get_services()

    async def get_name(self) -> str:
        name = await self.read_gatt_char('00002A00-0000-1000-8000-00805F9B34FB')
        if name is None:
            return None
        name = struct.unpack('>{}s'.format(len(name)), name)
        return name[0].decode('utf-8')

    async def set_name(self, name: str, response: bool = True) -> None:
        name = struct.pack('>s', name.encode('utf-8'))
        await self.write_gatt_char('00002A00-0000-1000-8000-00805F9B34FB', name, response)

    async def get_model(self) -> str:
        model = await self.read_gatt_char('00002A01-0000-1000-8000-00805F9B34FB')
        if model is None:
            return None
        model = struct.unpack('>{}s'.format(len(model)), model)
        return model[0].decode('utf-8')

    async def get_connect_params(self) -> str:
        params = await self.read_gatt_char('00002A04-0000-1000-8000-00805F9B34FB')
        if params is None:
            return None
        params = struct.unpack('>{}s'.format(len(params)), params)
        return params[0].decode('utf-8')

    async def get_soc(self) -> SOC:
        soc = await self.read_gatt_char('00002A19-0000-1000-8000-00805F9B34FB')
        if soc is None:
            return None
        soc = struct.unpack('>B', soc)
        await self.soc.set_soc(soc[0])
        return self.soc

    async def get_mac_address(self) -> str:
        MAC = await (await self.client()).read_gatt_char('00002A24-0000-1000-8000-00805F9B34FB')
        if MAC is None:
            return None
        MAC = [bytes([b]).hex() for b in struct.unpack('>6B', MAC)]
        MAC.reverse()
        return ':'.join(MAC)

    async def get_serial_number(self) -> str:
        serial = await self.read_gatt_char('00002A25-0000-1000-8000-00805F9B34FB')
        if serial is None:
            return None
        serial = struct.unpack('>{}s'.format(len(serial)), serial)
        try:
            return serial[0].decode('utf-8')
        except UnicodeDecodeError:
            return None

    async def get_firmware_version(self) -> str:
        version = await self.read_gatt_char('00002A26-0000-1000-8000-00805F9B34FB')
        if version is None:
            return None
        version = struct.unpack('>{}s'.format(len(version)), version)
        return version[0].decode('utf-8')

    async def get_hardware_version(self) -> str:
        version = await self.read_gatt_char('00002A27-0000-1000-8000-00805F9B34FB')
        if version is None:
            return None
        version = struct.unpack('>{}s'.format(len(version)), version)
        return version[0].decode('utf-8')

    async def get_manufacturer(self) -> str:
        manufacturer = await self.read_gatt_char('00002A29-0000-1000-8000-00805F9B34FB')
        if manufacturer is None:
            return None
        manufacturer = struct.unpack('>{}s'.format(len(manufacturer)), manufacturer)
        return manufacturer[0].decode('utf-8')

    async def start_notify(self, char_specifier: str, callback: callable) -> None:
        await (await self.client()).start_notify(char_specifier, callback)

    async def stop_notify(self, char_specifier: str) -> None:
        await (await self.client()).stop_notify(char_specifier)

    async def write_gatt_char(self, char_specifier: str, data: bytes, response: bool = True) -> None:
        try:
            await (await self.client()).write_gatt_char(char_specifier, data, response)
        except Exception as e:
            logger.error(f'Error writing to {self}: {e}')

    async def read_gatt_char(self, char_specifier: str) -> bytes:
        try:
            data = await (await self.client()).read_gatt_char(char_specifier)
        except BleakError as e:
            logger.error(f'Error reading {char_specifier}: {e}')
            return None
        return data
