from typing import Dict, Optional, Callable
import asyncio
import logging

from bleak.backends.client import BaseBleakClient
from enterble.ble.device import Device
from enterble.ble.scanner import DeviceScanner


logger = logging.getLogger(__name__)


# 数据采集器
class Collector(object):

    def __init__(
        self,
        name: str,
        model_nbr_uuid: str,
        device_identify: str,
        device_disconnected_callback: Optional[Callable[["BaseBleakClient"], None]],
        notify_callback_table: Dict[str, callable],
        before_notify_callback_table: Dict[str, bytes] = None,
        after_notify_callback_table: Dict[str, bytes] = None,
        soc_cal_call: callable = None,
    ) -> None:
        """初始化数据采集器

        Args:
            name (str): 设备名称
            model_nbr_uuid (str): 设备广播 UUID
            device_identify (str): 设备标识
            device_disconnected_callback (Optional[Callable[["BaseBleakClient"], None]]): 设备断开回调
            notify_callback_table (Dict[str, callable]): 通知回调表
            before_notify_callback_table (Dict[str, bytes], optional): 启动通知前执行的操作及回调. Defaults to None.
            after_notify_callback_table (Dict[str, bytes], optional): 启动通知后执行的操作及回调. Defaults to None.
            soc_cal_call (callable, optional): 电量自定义计算回调. Defaults to None.
        """
        self._stop: bool = False
        self.name: str = name
        self.model_nbr_uuid: str = model_nbr_uuid
        self.device_identify: str = device_identify
        self.device_disconnected_callback: Optional[Callable[["BaseBleakClient"], None]] = device_disconnected_callback
        self.notify_callback: Dict[str, callable] = notify_callback_table
        self.before_notify_callback: Dict[str, bytes] = before_notify_callback_table
        self.after_notify_callback: Dict[str, bytes] = after_notify_callback_table
        self.device_soc_cal_callback: callable = soc_cal_call
        self.device: Device = None

    async def start(self):
        """启动采集器"""

        # 扫描设备
        found = False
        while not found:
            logger.info('Scanning for %s...', self.name)
            self.device = await DeviceScanner.get_device(
                name=self.name, model_nbr_uuid=self.model_nbr_uuid, device_identify=self.device_identify
            )
            if self.device:
                found = True
                logger.info('Found %s', self.device)
            else:
                logger.info('%s not found, retrying...', self.name)

        # 电量回调
        await self.device.set_soc_cal_call(self.device_soc_cal_callback)

        # 设备连接回调
        if self.device_disconnected_callback:
            await self.device.set_disconnected_callback(self.device_disconnected)

        # 启动通知前
        if self.before_notify_callback:
            for char_specifier, data in self.before_notify_callback.items():
                await self.device.write_gatt_char(char_specifier, data)
                logger.info('Write down code before notify: %s: %s', char_specifier, data)

        # 启动通知
        for char_specifier, callback in self.notify_callback.items():
            await self.device.start_notify(char_specifier, callback)
            logger.info('Start notify: %s', char_specifier)

        # 启动通知后
        if self.after_notify_callback:
            for char_specifier, data in self.after_notify_callback.items():
                await self.device.write_gatt_char(char_specifier, data)
                logger.info('Write down code after notify: %s: %s', char_specifier, data)

        # 获取设备基础信息
        await self.device.get_soc()
        logger.info(f'{self.name} initialized')
        logger.info('Device name: {}'.format(await self.get_name()))
        logger.info('Device model: {}'.format(await self.get_model()))
        logger.info('Device connect params: {}'.format(await self.get_connect_params()))
        logger.info('Device soc: {}%'.format(await self.get_soc()))
        logger.info('Device MAC address: {}'.format(await self.get_mac_address()))
        logger.info('Device serial number: {}'.format(await self.get_serial_number()))
        logger.info('Device firmware version: {}'.format(await self.get_firmware_version()))
        logger.info('Device hardware version: {}'.format(await self.get_hardware_version()))
        logger.info('Device manufacturer: {}'.format(await self.get_manufacturer()))

    def device_disconnected(self, device: Optional[Callable[["BaseBleakClient"], None]]) -> None:
        """设备断开回调"""
        if self.device_disconnected_callback:
            asyncio.ensure_future(self.device_disconnected_callback(device))

    async def wait_for_stop(self):
        """设备运行、停止、异常等状态监听"""
        logger.info('Device running...')
        while not self._stop:
            await asyncio.sleep(1)

        for char_specifier in self.notify_callback.keys():
            await self.device.stop_notify(char_specifier)
        await self.device.disconnect()
        logger.info('Device stopped')

    async def get_name(self):
        """获取设备名称"""
        return await self.device.get_name()

    async def set_name(self, name: str, response: bool = True):
        """设置设备名称"""
        await self.device.set_name(name, response)

    async def get_model(self):
        """获取设备类型"""
        return await self.device.get_model()

    async def get_connect_params(self):
        """获取设备连接参数"""
        return await self.device.get_connect_params()

    async def get_soc(self):
        """获取电量"""
        return await self.device.get_soc()

    async def get_mac_address(self):
        """获取 MAC 地址"""
        return await self.device.get_mac_address()

    async def get_serial_number(self):
        """获取序列号"""
        return await self.device.get_serial_number()

    async def get_firmware_version(self):
        """获取固件版本"""
        return await self.device.get_firmware_version()

    async def get_hardware_version(self):
        """获取硬件版本"""
        return await self.device.get_hardware_version()

    async def get_manufacturer(self):
        """获取设备厂商"""
        return await self.device.get_manufacturer()

    async def stop(self):
        """停止采集器"""
        logger.info('Stopping...')
        self._stop = True
