import asyncio
import logging
from contextlib import suppress

from bleak import BleakScanner, BaseBleakScanner

from .parse import ManufacturerData
from .const import ScanService

LOGGER = logging.getLogger(__name__)

DEFAULT_MANUFACTURER_DATA_PRODUCT_TYPE_FIELDS = {"group", "model", "variant"}
DEFAULT_MANUFACTURER_DATA_TIMEOUT = 5.0


async def async_get_manufacturer_data(
    addresses: set[str],
    *,
    fields: set[str] = DEFAULT_MANUFACTURER_DATA_PRODUCT_TYPE_FIELDS,
    timeout: float = DEFAULT_MANUFACTURER_DATA_TIMEOUT,
    backend: type[BaseBleakScanner] | None = None,
):
    """Wait for enough packets of manufacturer data to get select fields, or timeout."""
    data = {address: ManufacturerData() for address in addresses}
    done: set[str] = set()

    if not addresses:
        return data

    with suppress(TimeoutError):
        async with asyncio.timeout(timeout), BleakScanner(
            backend=backend, service_uuids=[ScanService]
        ) as scanner:
            async for device, advertisement in scanner.advertisement_data():
                if device.address not in addresses:
                    continue
                mfg_data = data[device.address]
                mfg_data.update(
                    advertisement.manufacturer_data.get(ManufacturerData.company, b"")
                )

                if any(getattr(mfg_data, field, None) is None for field in fields):
                    continue

                done.add(device.address)
                if done == data.keys():
                    break

    LOGGER.debug("Manufacturer data %s, incomplete %s", data, data.keys() - done)
    return data
