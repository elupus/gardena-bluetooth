import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from bleak import AdvertisementData
from bleak.backends.device import BLEDevice

from gardena_bluetooth.const import ScanService
from gardena_bluetooth.parse import ManufacturerData
from gardena_bluetooth.scan import async_scan_devices

WATER_CONTROL_MANUFACTURER_DATA = bytes.fromhex("8e60c20b3401001d04")


def _advertisement(
    address: str,
    *,
    service_uuids: list[str] | None = None,
    manufacturer_data: dict[int, bytes] | None = None,
) -> tuple[BLEDevice, AdvertisementData]:
    device = BLEDevice(address=address, name="Gardena", details=None)
    advertisement = AdvertisementData(
        local_name="Gardena",
        manufacturer_data=manufacturer_data or {},
        service_data={},
        service_uuids=service_uuids or [],
        tx_power=None,
        rssi=-60,
        platform_data=(),
    )
    return device, advertisement


def _mock_scanner(advertisements):
    def _factory(*args, detection_callback, **kwargs):
        scanner = MagicMock()

        async def _start():
            for device, advertisement in advertisements:
                detection_callback(device, advertisement)

        scanner.start = AsyncMock(side_effect=_start)
        scanner.stop = AsyncMock()
        return scanner

    return _factory


async def _first_address() -> str | None:
    generator = async_scan_devices()
    try:
        async with asyncio.timeout(0.1):
            async for result in generator:
                return result.ble_device.address
    except TimeoutError:
        return None
    finally:
        await generator.aclose()
    return None


async def test_scan_accepts_manufacturer_data_advertisement():
    advertisements = [
        _advertisement(
            "00:00:00:00:00:01",
            manufacturer_data={
                ManufacturerData.company: WATER_CONTROL_MANUFACTURER_DATA
            },
        )
    ]
    with patch(
        "gardena_bluetooth.scan.BleakScanner", new=_mock_scanner(advertisements)
    ):
        assert await _first_address() == "00:00:00:00:00:01"


async def test_scan_skips_advertisement_without_manufacturer_data():
    advertisements = [_advertisement("00:00:00:00:00:02", service_uuids=[ScanService])]
    with patch(
        "gardena_bluetooth.scan.BleakScanner", new=_mock_scanner(advertisements)
    ):
        assert await _first_address() is None
