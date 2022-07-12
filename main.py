import asyncio
import struct
import platform
import sys
from functools import partial

asyncio.get_running_loop = asyncio._get_running_loop
import logging
from bleak import discover, BleakClient, BleakScanner

LOG_LEVEL = logging.INFO

logging.basicConfig(level=LOG_LEVEL, format='%(levelname)s - %(asctime)s - %(name)s - %(message)s')

logging.getLogger('bleak').setLevel(logging.INFO)

# logging.basicConfig(
#     level=LOG_LEVEL,
    # format=formatter
# )
# logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

logger = logging.getLogger(__name__)
# stream = logging.StreamHandler(sys.stdout)
# stream.setFormatter(formatter)
# stream.setLevel(LOG_LEVEL)
# logger.addHandler(stream)
logger.setLevel(LOG_LEVEL)
logger.info('Start...........')

# MAC_UUID = '00002A24-0000-1000-8000-00805F9B34FB'

DEVICE_UUID = '0000FF10-1212-ABCD-1523-785FEABCD123'
NOTIFY_UUID = {
    'WEAR': '0000ff32-1212-abcd-1523-785feabcd123',
    'EEG': '0000ff31-1212-abcd-1523-785feabcd123',
    'HR': '0000ff51-1212-abcd-1523-785feabcd123'
}


DOWN_CODE_UUID = '0000ff21-1212-abcd-1523-785feabcd123'

DEVICE_ADDRESS = (
    "FB:EC:25:DE:1A:92"
    if platform.system() != "Darwin"
    else "AAE31983-8A63-BBA9-3CD4-3EBECC8C315D"
)


CONNECTED = False

LOCK = asyncio.Lock()


async def main2():
    scanner = BleakScanner()
    scanner.register_detection_callback(detection_callback)
#     await scanner.start()
#     stop = False
#     while True:
#         if CONNECTED and not stop:
#             logger.info('stop')
#             await scanner.stop()
#             stop = True
#         await asyncio.sleep(0.1)
    # await asyncio.sleep(1.0)
    # await scanner.stop()
    # # 最终扫描出来的设备
    # print("--------------------")
    # for d in scanner.discovered_devices:
    #     print(d)


async def main():
    while True:
        if not CONNECTED:
            devices = await discover()
            for device in devices:
                logger.info(device)
                await detection_callback(device, None)
        await asyncio.sleep(1)


SERVICES = {}


async def wear(data):
    status = struct.unpack('>B', data)[0] == 0
    logger.info(f'Received wear data: {status}')


async def eeg(data):
    eeg_data = struct.unpack('>20B', data)
    logger.info(f'Received eeg data: {eeg_data}')


async def hr(data):
    hr_rate = struct.unpack('>B', data)[0]
    logger.info(f'Received hr data: {hr_rate}')


CALLBACK_TABLE = {
    NOTIFY_UUID['WEAR']: wear,
    NOTIFY_UUID['EEG']: eeg,
    NOTIFY_UUID['HR']: hr
}

async def callback_handler(sender, data):
    # logger.info(f"Received({SERVICES[sender]}) callback data: {data}")
    sender_uuid = SERVICES[sender]
    callback = CALLBACK_TABLE.get(sender_uuid)
    if callback:
        await callback(data)


async def detection_callback(device, advertisement_data):
        if len(device.metadata['uuids']):
            logger.info(device.metadata['uuids'])
            if device.metadata['uuids'][0].upper() != DEVICE_UUID or device.address != DEVICE_ADDRESS:
            # if device.metadata['uuids'][0].upper() != UUID.upper():
                return
            logger.info(device)
            # with await LOCK:
            
            # if CONNECTED:
            #     return
            async with BleakClient(device.address) as client:
                global CONNECTED
                CONNECTED = True
                logger.info(f"Connected to {device.address}")
                await asyncio.sleep(1)

                # code_uuid = None
                global SERVICES
                services = await client.get_services()
                for char, detail in services.characteristics.items():
                    logger.info('{} {} {}'.format(char, detail.properties, detail.uuid))
                    SERVICES[char] = detail.uuid
                    # if 'notify' in detail.properties:# and detail.uuid.upper() == NOTIFY_UUID.upper():
                        # logger.info(f'Start notify({detail.uuid})')
                        # await client.start_notify(detail, callback_handler)
                    # elif 'write' in detail.properties:
                    #     if detail.uuid == UP_CODE_UUID:
                            # code = struct.pack('>B', 5)
                            # logger.info(f'Send {code} code [{bytes([5])}]')
                            # await client.write_gatt_char(detail, bytes([5]))
                            # code_uuid = detail

                # resp = await client.read_gatt_char(MAC_UUID)
                # await asyncio.sleep(2)

                for service, _uuid in NOTIFY_UUID.items():
                    logger.info(f'Start {service} notify({_uuid})')
                    await client.start_notify(_uuid.lower(), callback_handler)

                # await asyncio.sleep(3)

                # code = struct.pack('>B', 5)
                # logger.info(f'Send {code} code [{bytes([5])}]')
                # await client.write_gatt_char(code_uuid, code)
                code = struct.pack('>b', 5)
                logger.info(f'Send {code} code')
                await client.write_gatt_char(DOWN_CODE_UUID, code, response=True)
                # await client.write_gatt_descriptor(CODE_UUID, code)

                logger.info('Waiting')
                await asyncio.sleep(130.0)

                logger.info('Stop notify')
                for service, _uuid in NOTIFY_UUID.items():
                    await client.stop_notify(_uuid)


asyncio.get_event_loop().run_until_complete(main())

