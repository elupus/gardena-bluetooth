from __future__ import annotations

import logging
from datetime import datetime

from bleak import BleakClient
from bleak.uuids import register_uuids

from .const import DeviceConfiguration, ScanService
from .exceptions import CharacteristicNoAccess, CharacteristicNotFound
from .parse import Characteristic, CharacteristicType, Service

LOGGER = logging.getLogger(__name__)

register_uuids(
    {
        service.uuid: f"Gardena {service.__name__}"
        for service in Service.registry.values()
    }
)

register_uuids(
    {
        char.uuid: f"Gardena {service.__name__} {char.name}"
        for service in Service.registry.values()
        for char in service.characteristics()
    }
)

register_uuids({ScanService: "Husqvarna"})


async def read_char_raw(client: BleakClient, uuid: str):
    characteristic = client.services.get_characteristic(uuid)
    if characteristic is None:
        raise CharacteristicNotFound(f"Unable to find characteristic {uuid}")
    if "read" not in characteristic.properties:
        raise CharacteristicNoAccess(f"Characteristic {uuid} is not readable")
    return await client.read_gatt_char(characteristic)


async def read_char(
    client: BleakClient, char: Characteristic[CharacteristicType]
) -> CharacteristicType:
    """Read data to from a characteristic."""
    return char.decode(await read_char_raw(client, char.uuid))


async def write_char_raw(
    client: BleakClient, uuid: str, data: bytes, response: bool = True
):
    """Write data to a characteristic."""
    characteristic = client.services.get_characteristic(uuid)
    if characteristic is None:
        raise CharacteristicNotFound(f"Unable to find characteristic {uuid}")
    if "write" not in characteristic.properties:
        raise CharacteristicNoAccess(f"Characteristic {uuid} is not writable")
    await client.write_gatt_char(characteristic, data, response=response)


async def write_char(
    client: BleakClient,
    char: Characteristic[CharacteristicType],
    value: CharacteristicType,
    response=True,
) -> None:
    """Write data to a characteristic."""
    data = char.encode(value)
    await write_char_raw(client, char.uuid, data, response)


async def update_timestamp(client: BleakClient, now: datetime):
    timestamp = await read_char(client, DeviceConfiguration.unix_timestamp)
    timestamp = timestamp.replace(tzinfo=now.tzinfo)
    delta = timestamp - now
    if abs(delta.total_seconds()) > 60:
        LOGGER.warning(
            "Updating time on device to match local time delta was %s", delta
        )
        await write_char(
            client,
            DeviceConfiguration.unix_timestamp,
            now.replace(tzinfo=None),
            True,
        )


async def get_all_characteristics_uuid(client: BleakClient) -> set[str]:
    """Get all characteristics from device."""
    return {
        characteristic.uuid
        for service in client.services
        for characteristic in service.characteristics
    }
