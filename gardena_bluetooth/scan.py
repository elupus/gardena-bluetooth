import asyncio
import contextlib
import logging
import dataclasses

from bleak import BleakScanner, BaseBleakScanner, AdvertisementData, BLEDevice

from .parse import ManufacturerData
from .const import ScanService

LOGGER = logging.getLogger(__name__)

DEFAULT_MANUFACTURER_DATA_PRODUCT_TYPE_FIELDS = {"group", "model", "variant"}
DEFAULT_MANUFACTURER_DATA_TIMEOUT = 15.0


@dataclasses.dataclass
class ScanResult:
    manufacturer_data: ManufacturerData
    ble_device: BLEDevice


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


async def async_get_devices(
    addresses: set[str],
    *,
    fields: set[str] = DEFAULT_MANUFACTURER_DATA_PRODUCT_TYPE_FIELDS,
    timeout: float | None = DEFAULT_MANUFACTURER_DATA_TIMEOUT,
    backend: type[BaseBleakScanner] | None = None,
) -> dict[str, ScanResult]:
    """Wait for enough packets of manufacturer data to get select fields, or timeout."""
    devices: dict[str, ScanResult] = {}
    done: set[str] = set()

    if not addresses:
        return set()

    async with advertisement_queue(backend) as queue, asyncio.timeout(timeout):
        while True:
            device, advertisement = await queue.get()
            if device.address not in addresses:
                continue

            if (result := devices.get(device.address)) is None:
                result = ScanResult(ManufacturerData(), device)
                devices[device.address] = result

            result.manufacturer_data.update(
                advertisement.manufacturer_data.get(ManufacturerData.company, b"")
            )

            if any(
                getattr(result.manufacturer_data, field, None) is None
                for field in fields
            ):
                continue

            done.add(device.address)
            if done == addresses:
                break

    LOGGER.debug("Device data %s, incomplete %s", devices, addresses - done)
    return devices


async def async_get_manufacturer_data(
    addresses: set[str],
    *,
    fields: set[str] = DEFAULT_MANUFACTURER_DATA_PRODUCT_TYPE_FIELDS,
    timeout: float = DEFAULT_MANUFACTURER_DATA_TIMEOUT,
    backend: type[BaseBleakScanner] | None = None,
) -> dict[str, ManufacturerData]:
    devices = await async_get_devices(
        addresses, fields=fields, timeout=timeout, backend=backend
    )
    return {
        address: scan_result.manufacturer_data
        for address, scan_result in devices.items()
    }
