from typing import List

from bleak import discover

from enterble.ble.device import Device


class DeviceScanner(object):

    @classmethod
    async def discover(cls, name: str = None, model_nbr_uuid: str = None, timeout: int = 5) -> List[Device]:
        if model_nbr_uuid is None:
            if timeout == -1:
                while True:
                    devices = await discover()
                    if len(devices) > 0:
                        return [Device(device) for device in devices if name is None or device.name == name]
            return [Device(device) for device in await discover(timeout=timeout) if name is None or device.name == name]

        model_nbr_uuid = model_nbr_uuid.lower()
        if timeout == -1:
            _devices = await discover()
            devices = []
            for device in _devices:
                if model_nbr_uuid in device.metadata['uuids'] and (name is None or device.name == name):
                    devices.append(Device(device))
            if len(devices) > 0:
                return devices

        _devices = await discover(timeout=timeout)
        devices = []
        for device in _devices:
            if model_nbr_uuid in device.metadata['uuids'] and (name is None or device.name == name):
                devices.append(Device(device))
        return devices

    @classmethod
    async def get_device(cls, name: str, model_nbr_uuid: str, device_identify: str, timeout: int = 5) -> Device:
        devices = await cls.discover(name, model_nbr_uuid, timeout)
        for device in devices:
            if device.identify.upper() == device_identify.upper():
                return device
        return None
