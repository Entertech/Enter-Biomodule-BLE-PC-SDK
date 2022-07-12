import time
import asyncio
asyncio.get_running_loop = asyncio._get_running_loop
import logging
import struct
# from loguru import logger
from bleak import BleakClient

logger = logging.getLogger(__name__)

address = "AAE31983-8A63-BBA9-3CD4-3EBECC8C315D"
#下面这个是特征
# NOTIFICATION_UUID = '0000FF31-1212-abcd-1523-785feabcd123'
NOTIFICATION_UUID = '0000FF51-1212-abcd-1523-785feabcd123'

SEND_CODE_UUID = '0000FF21-1212-abcd-1523-785feabcd123'

async def run_ble_client(address: str, queue: asyncio.Queue):
    async def callback_handler(sender, data):
        print(f"Received callback data: {data}")
        await queue.put((time.time(), data))

    async with BleakClient(address) as client:
        logger.info(f"Connected: {client.is_connected}")
        await asyncio.sleep(1.0)
        services = await client.get_services()
        await client.start_notify(NOTIFICATION_UUID, callback_handler)
        await client.write_gatt_char(SEND_CODE_UUID, bytes([5]))
        await asyncio.sleep(130.0)
        await client.stop_notify(NOTIFICATION_UUID)

        await queue.put((time.time(), None))


async def run_queue_consumer(queue: asyncio.Queue):
    while True:
        # Use await asyncio.wait_for(queue.get(), timeout=1.0) if you want a timeout for getting data.
        epoch, data = await queue.get()
        print(f"Received data: {data}")
        if data is None:
            logger.info(
                "Got message from client about disconnection. Exiting consumer loop..."
            )
            break
        else:
            logger.info(f"Received callback data via async queue at {epoch}: {data}")


async def main():
    queue = asyncio.Queue()
    client_task = run_ble_client(address, queue)
    consumer_task = run_queue_consumer(queue)
    await asyncio.gather(client_task, consumer_task)
    logger.info("Main method done.")


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
