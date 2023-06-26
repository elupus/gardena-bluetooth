from __future__ import annotations

import logging
from datetime import datetime

from bleak import BleakClient
from bleak.uuids import register_uuids
from typing import TypeVar, overload

from .const import DeviceConfiguration, ScanService
from .exceptions import CharacteristicNoAccess, CharacteristicNotFound
from .parse import Characteristic, CharacteristicType, Service

LOGGER = logging.getLogger(__name__)
DEFAULT_MISSING = object()
DEFAULT_TYPE = TypeVar("DEFAULT_TYPE")

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


@overload
async def read_char_raw(client: BleakClient, uuid: str) -> bytes:
    ...


@overload
async def read_char_raw(
    client: BleakClient, uuid: str, default: DEFAULT_TYPE
) -> bytes | DEFAULT_TYPE:
    ...


async def read_char_raw(
    client: BleakClient, uuid: str, default: DEFAULT_TYPE = DEFAULT_MISSING
) -> bytes | DEFAULT_TYPE:
    characteristic = client.services.get_characteristic(uuid)
    if characteristic is None:
        if default is not DEFAULT_MISSING:
            return default
        raise CharacteristicNotFound(f"Unable to find characteristic {uuid}")
    if "read" not in characteristic.properties:
        if default is not DEFAULT_MISSING:
            return default
        raise CharacteristicNoAccess(f"Characteristic {uuid} is not readable")
    return await client.read_gatt_char(characteristic)


@overload
async def read_char(
    client: BleakClient, char: Characteristic[CharacteristicType]
) -> CharacteristicType:
    ...


@overload
async def read_char(
    client: BleakClient,
    char: Characteristic[CharacteristicType],
    default: DEFAULT_TYPE,
) -> CharacteristicType | DEFAULT_TYPE:
    ...


async def read_char(
    client: BleakClient,
    char: Characteristic[CharacteristicType],
    default: DEFAULT_TYPE = DEFAULT_MISSING,
) -> CharacteristicType | DEFAULT_TYPE:
    """Read data to from a characteristic."""
    try:
        return char.decode(await read_char_raw(client, char.uuid))
    except CharacteristicNotFound:
        if default is not DEFAULT_MISSING:
            return default
        raise


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
    try:
        timestamp = await read_char(client, DeviceConfiguration.unix_timestamp)
    except CharacteristicNoAccess:
        LOGGER.debug("No timestamp defined for device")
        return
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
    else:
        LOGGER.debug("No need to update timestamp local time delta was %s", delta)


async def get_all_characteristics_uuid(client: BleakClient) -> set[str]:
    """Get all characteristics from device."""
    characteristics = {
        characteristic.uuid
        for service in client.services
        for characteristic in service.characteristics
    }
    LOGGER.debug("Characteristics: %s", characteristics)
    return characteristics
