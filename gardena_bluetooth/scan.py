import asyncio
import contextlib
import dataclasses
import logging
from collections.abc import AsyncGenerator

from bleak import AdvertisementData, BaseBleakScanner, BleakScanner, BLEDevice

from .const import ScanService
from .parse import ManufacturerData

LOGGER = logging.getLogger(__name__)

DEFAULT_MANUFACTURER_DATA_PRODUCT_TYPE_FIELDS = {"group", "model", "variant"}
DEFAULT_MANUFACTURER_DATA_TIMEOUT = 15.0


@dataclasses.dataclass
class ScanResult:
    manufacturer_data: ManufacturerData
    advertisement: AdvertisementData
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

    # NOTE: do NOT pass service_uuids=[ScanService] here. On macOS the
    # CoreBluetooth-level filter hides devices that don't advertise the scan
    # service UUID in their ad packet — the newer Smart Water Control
    # G-19033-20 advertises only manufacturer data, no service UUIDs. The
    # async iterator below filters by Gardena's manufacturer id (0x0426).
    scanner = BleakScanner(backend=backend, detection_callback=_callback)

    await scanner.start()
    try:
        yield queue
    finally:
        await scanner.stop()


async def async_scan_devices(
    backend: type[BaseBleakScanner] | None = None,
) -> AsyncGenerator[ScanResult]:
    devices: dict[str, ScanResult] = {}
    """Async iterator that accumulate manufacturer data of devices."""

    async with advertisement_queue(backend) as queue:
        while True:
            device, advertisement = await queue.get()
            # Accept either the legacy scan-service-uuid advert OR the newer
            # G-19033-20 packets that only carry manufacturer data.
            if (
                ScanService not in advertisement.service_uuids
                and ManufacturerData.company
                not in (advertisement.manufacturer_data or {})
            ):
                continue

            data = devices.get(device.address)
            if data is None:
                data = ScanResult(ManufacturerData(), advertisement, device)
                devices[device.address] = data

            data.ble_device = device
            data.advertisement = advertisement
            data.manufacturer_data.update(
                advertisement.manufacturer_data.get(ManufacturerData.company, b"")
            )
            yield data


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
        return devices

    try:
        async with asyncio.timeout(timeout):
            async for result in async_scan_devices(backend):
                if result.ble_device.address not in addresses:
                    continue

                devices[result.ble_device.address] = result
                if any(
                    getattr(result.manufacturer_data, field, None) is None
                    for field in fields
                ):
                    continue

                done.add(result.ble_device.address)
                if done == addresses:
                    break

    except TimeoutError:
        missing = addresses - devices.keys()
        if missing:
            LOGGER.debug(
                "One or more of the requested address was not found: %s", missing
            )
            raise

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
