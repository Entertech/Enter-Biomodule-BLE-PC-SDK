from typing import Dict
import asyncio
import logging

from enterble.ble.device import Device
from enterble.ble.scanner import DeviceScanner


logger = logging.getLogger(__name__)


class Collector(object):

    def __init__(
        self,
        name: str,
        model_nbr_uuid: str,
        device_identify: str,
        notify_callback_table: Dict[str, callable],
        before_notify_callback_table: Dict[str, bytes] = None,
        after_notify_callback_table: Dict[str, bytes] = None,
        soc_cal_call: callable = None,
    ) -> None:
        self._stop: bool = False
        self.name: str = name
        self.model_nbr_uuid: str = model_nbr_uuid
        self.device_identify: str = device_identify
        self.notify_callback: Dict[str, callable] = notify_callback_table
        self.before_notify_callback: Dict[str, bytes] = before_notify_callback_table
        self.after_notify_callback: Dict[str, bytes] = after_notify_callback_table
        self.device_soc_cal_callback: callable = soc_cal_call
        self.device: Device = None

    async def start(self):
        found = False
        while not found:
            logger.info('Scanning for %s...', self.name)
            self.device = await DeviceScanner.get_device(
                self.name, self.model_nbr_uuid, self.device_identify
            )
            if self.device:
                await self.device.set_soc_cal_call(self.device_soc_cal_callback)
                found = True
                logger.info('Found %s', self.device)
            else:
                logger.info('%s not found, retrying...', self.name)

        if self.before_notify_callback:
            for char_specifier, data in self.before_notify_callback.items():
                await self.device.write_gatt_char(char_specifier, data)
                logger.info('Write down code before notify: %s: %s', char_specifier, data)

        for char_specifier, callback in self.notify_callback.items():
            await self.device.start_notify(char_specifier, callback)
            logger.info('Start notify: %s', char_specifier)

        if self.after_notify_callback:
            for char_specifier, data in self.after_notify_callback.items():
                await self.device.write_gatt_char(char_specifier, data)
                logger.info('Write down code after notify: %s: %s', char_specifier, data)

        await self.device.get_soc()
        logger.info(f'{self.name} initialized')
        logger.info('Device name: {}'.format(await self.get_name()))
        logger.info('Device model: {}'.format(await self.get_model()))
        logger.info('Device connect params: {}'.format(await self.get_connect_params()))
        logger.info('Device soc: {}%%'.format(await self.get_soc()))
        logger.info('Device MAC address: {}'.format(await self.get_mac_address()))
        logger.info('Device serial number: {}'.format(await self.get_serial_number()))
        logger.info('Device firmware version: {}'.format(await self.get_firmware_version()))
        logger.info('Device hardware version: {}'.format(await self.get_hardware_version()))
        logger.info('Device manufacturer: {}'.format(await self.get_manufacturer()))

    async def wait_for_stop(self):
        logger.info('Device running...')
        while not self._stop:
            await asyncio.sleep(1)

        for char_specifier in self.notify_callback.keys():
            await self.device.stop_notify(char_specifier)
        self.device.disconnect()
        logger.info('Device stopped')

    async def get_name(self):
        return await self.device.get_name()

    async def set_name(self, name: str, response: bool = True):
        await self.device.set_name(name, response)

    async def get_model(self):
        return await self.device.get_model()

    async def get_connect_params(self):
        return await self.device.get_connect_params()

    async def get_soc(self):
        return await self.device.get_soc()

    async def get_mac_address(self):
        return await self.device.get_mac_address()

    async def get_serial_number(self):
        return await self.device.get_serial_number()

    async def get_firmware_version(self):
        return await self.device.get_firmware_version()

    async def get_hardware_version(self):
        return await self.device.get_hardware_version()

    async def get_manufacturer(self):
        return await self.device.get_manufacturer()

    async def stop(self):
        logger.info('Stopping...')
        self._stop = True
