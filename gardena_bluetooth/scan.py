import asyncio
import contextlib
import logging
from contextlib import suppress

from bleak import BleakScanner, BaseBleakScanner, AdvertisementData, BLEDevice

from .parse import ManufacturerData
from .const import ScanService

LOGGER = logging.getLogger(__name__)

DEFAULT_MANUFACTURER_DATA_PRODUCT_TYPE_FIELDS = {"group", "model", "variant"}
DEFAULT_MANUFACTURER_DATA_TIMEOUT = 5.0


@contextlib.asynccontextmanager
async def advertisement_queue(backend: type[BaseBleakScanner] | None = None):
    """
    Context manager for BleakScanner

    Some implementations do not support async context management protocol,
    this include older versions of bleak, as well as the wrapper used in
    home assistant (see https://github.com/Bluetooth-Devices/habluetooth/issues/386).

    We can't use the async iterator of the scanner, since some
    implementations (like the one in home assistant) does not
    support it. See https://github.com/Bluetooth-Devices/habluetooth/issues/380
    """

    queue = asyncio.Queue[tuple[BLEDevice, AdvertisementData]]()

    def _callback(device, advertisement):
        queue.put_nowait((device, advertisement))

    scanner = BleakScanner(
        backend=backend, service_uuids=[ScanService], detection_callback=_callback
    )

    await scanner.start()
    try:
        yield queue
    finally:
        await scanner.stop()


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
        async with advertisement_queue(backend) as queue, asyncio.timeout(timeout):
            while True:
                device, advertisement = await queue.get()
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
