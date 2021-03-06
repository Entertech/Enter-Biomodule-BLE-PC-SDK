import asyncio
import sys
import logging
import platform

from bleak.backends.corebluetooth.client import BleakClientCoreBluetooth

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

    async def device_disconnected(device: BleakClientCoreBluetooth):
        logger.info(f'Device disconnected: {device}')

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
        "FB:EC:25:DE:1A:92"
        if platform.system() != "Darwin"
        else "AAE31983-8A63-BBA9-3CD4-3EBECC8C315D"
        # else "7500F2E8-4606-48EF-8CAB-72E1949D15E4"
    )

    collector = FlowtimeCollector(
        name='Flowtime',
        model_nbr_uuid=model_nbr_uuid,
        device_identify=device_identify,
        device_disconnected_callback=device_disconnected,
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
    # loop.run_until_complete(get_device())
    loop.run_until_complete(data_collector())
