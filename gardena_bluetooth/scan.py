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
async def advertisement_queue(
    backend: type[BaseBleakScanner] | None = None,
    *,
    filter_service_uuid: bool = True,
):
    """
    Context manager for BleakScanner

    Some implementations do not support async context management protocol,
    this include older versions of bleak, as well as the wrapper used in
    home assistant (see https://github.com/Bluetooth-Devices/habluetooth/issues/386).

    We can't use the async iterator of the scanner, since some
    implementations (like the one in home assistant) does not
    support it. See https://github.com/Bluetooth-Devices/habluetooth/issues/380

    With ``filter_service_uuid=False`` the OS-level service UUID filter is
    dropped: some devices (e.g. the G-1903x Smart Water Control family) only
    expose the scan service in passive scans, while active scans carry just
    manufacturer data.
    """

    queue = asyncio.Queue[tuple[BLEDevice, AdvertisementData]]()

    def _callback(device, advertisement):
        queue.put_nowait((device, advertisement))

    if filter_service_uuid:
        scanner = BleakScanner(
            backend=backend, service_uuids=[ScanService], detection_callback=_callback
        )
    else:
        scanner = BleakScanner(backend=backend, detection_callback=_callback)

    await scanner.start()
    try:
        yield queue
    finally:
        await scanner.stop()


async def async_scan_devices(
    backend: type[BaseBleakScanner] | None = None,
    *,
    filter_service_uuid: bool = True,
) -> AsyncGenerator[ScanResult]:
    devices: dict[str, ScanResult] = {}
    """Async iterator that accumulate manufacturer data of devices."""

    async with advertisement_queue(
        backend, filter_service_uuid=filter_service_uuid
    ) as queue:
        while True:
            device, advertisement = await queue.get()
            if filter_service_uuid:
                if ScanService not in advertisement.service_uuids:
                    continue
            elif (
                ScanService not in advertisement.service_uuids
                and ManufacturerData.company not in advertisement.manufacturer_data
            ):
                # Accept either the scan-service-uuid or manufacturer data.
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
    filter_service_uuid: bool = False,
) -> dict[str, ScanResult]:
    """Wait for enough packets of manufacturer data to get select fields, or timeout.

    The addresses are explicitly requested, so the service UUID filter is
    relaxed by default: devices that only carry manufacturer data in active
    scans (G-1903x family) are still matched.
    """
    devices: dict[str, ScanResult] = {}
    done: set[str] = set()

    if not addresses:
        return devices

    try:
        async with asyncio.timeout(timeout):
            async for result in async_scan_devices(
                backend, filter_service_uuid=filter_service_uuid
            ):
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
    filter_service_uuid: bool = False,
) -> dict[str, ManufacturerData]:
    devices = await async_get_devices(
        addresses,
        fields=fields,
        timeout=timeout,
        backend=backend,
        filter_service_uuid=filter_service_uuid,
    )
    return {
        address: scan_result.manufacturer_data
        for address, scan_result in devices.items()
    }
