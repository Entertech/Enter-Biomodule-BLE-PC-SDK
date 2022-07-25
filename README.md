# Enter BLE SDK For PC

## 简介

Enter BLE SDK For PC 是[回车科技](https://www.entertech.cn/)提供的，适配回车科技蓝牙芯片的 PC 端 SDK。本 SDK 使用 Python 语言开发，可以在 macOS、Linux、Win 下运行。

## 安装

`pip install enterble`

## 功能

1. 搜索蓝牙设备
2. 连接蓝牙设备
3. 与蓝牙设备通信
4. 回车科技 Flowtime 系列芯片数据交互适配

## 使用

查看 [examples](https://github.com/Entertech/Enter-Biomodule-BLE-PC-SDK/tree/main/examples)

Simple:

```python
import asyncio
import sys
import logging
import platform

from enterble import DeviceScanner, FlowtimeCollector


if sys.version_info < (3, 7):
    asyncio.get_running_loop = asyncio._get_running_loop


logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(asctime)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)


def bleak_log(level=logging.INFO):
    import bleak
    logging.getLogger('bleak').setLevel(level=level)


async def get_device():
    devices = await DeviceScanner.discover(
        name=None,
        model_nbr_uuid='0000ff10-1212-abcd-1523-785feabcd123',
    )
    if not devices:
        raise Exception('No device found, please try again later.')

    for device in devices:
        try:
            services = await device.get_services()
            for _id, service in services.characteristics.items():
                logger.info(f'{device} - {_id} - {service}')
            MAC = await device.get_mac_address()
            logger.info(
                f'{device} - {MAC}'
            )
        except Exception as e:
            logger.error(f'{device} - {device.identify} - {e}')


async def data_collector():

    async def soc_callback(soc):
        logger.info(f'SOC: {soc}')
        pass

    async def wear_status_callback(wear_status):
        logger.info(f'Wear status: {wear_status}')
        pass

    async def eeg_data_collector(data):
        logger.info(f'EEG: {data}')
        pass

    async def hr_data_collector(data):
        logger.info(f'HR: {data}')
        pass

    model_nbr_uuid = '0000ff10-1212-abcd-1523-785feabcd123'
    device_identify = (
        "FA:EC:25:DE:1A:92"
        if platform.system() != "Darwin"
        # else "AAE31983-8A63-BBA9-3CD4-3EBECC8C315D"
        else "D5E4362A-1690-4204-B797-3015EEDB510C"
    )

    collector = FlowtimeCollector(
        name='Flowtime',
        model_nbr_uuid=model_nbr_uuid,
        device_identify=device_identify,
        soc_data_callback=soc_callback,
        wear_status_callback=wear_status_callback,
        eeg_data_callback=eeg_data_collector,
        hr_data_callback=hr_data_collector,
    )
    await collector.start()
    await collector.wait_for_stop()


if __name__ == '__main__':
    bleak_log(logging.INFO)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(data_collector())

```
