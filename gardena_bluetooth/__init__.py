from __future__ import annotations

import logging
from collections.abc import Iterable
from datetime import datetime

from bleak import BleakClient
from bleak.uuids import register_uuids

from .const import DeviceConfiguration, ScanService
from .exceptions import CharacteristicNoAccess, CharacteristicNotFound
from .parse import Characteristic, CharacteristicType, Service

from typing import TypeVar

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


async def read_characteristic(
    client: BleakClient, char: Characteristic[CharacteristicType]
) -> CharacteristicType:
    """Read data to from a characteristic."""
    characteristic = client.services.get_characteristic(char.uuid)
    if characteristic is None:
        raise CharacteristicNotFound(f"Unable to find characteristic {char.uuid}")
    if "read" not in characteristic.properties:
        raise CharacteristicNoAccess(f"Characteristic {char.uuid} is not writable")
    data = await client.read_gatt_char(characteristic)
    return char.decode(data)


async def write_characteristic(
    client: BleakClient,
    char: Characteristic[CharacteristicType],
    value: CharacteristicType,
    response=True,
) -> None:
    """Write data to a characteristic."""
    characteristic = client.services.get_characteristic(char.uuid)
    if characteristic is None:
        raise CharacteristicNotFound(f"Unable to find characteristic {char.uuid}")
    if "write" not in characteristic.properties:
        raise CharacteristicNoAccess(f"Characteristic {char.uuid} is not writable")
    data = char.encode(value)
    await client.write_gatt_char(characteristic, data, response=response)


async def update_timestamp(client: BleakClient, now: datetime):
    timestamp = await read_characteristic(client, DeviceConfiguration.unix_timestamp)
    timestamp = timestamp.replace(tzinfo=now.tzinfo)
    delta = timestamp - now
    if abs(delta.total_seconds()) > 60:
        LOGGER.warning(
            "Updating time on device to match local time delta was %s", delta
        )
        await write_characteristic(
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
