from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest
from bleak.backends.device import BLEDevice
from bleak.exc import BleakError

from gardena_bluetooth.client import DEFAULT_DELAY, CachedConnection, Client
from gardena_bluetooth.const import AquaContourContours
from gardena_bluetooth.exceptions import CharacteristicNoAccess, CommunicationFailure
from gardena_bluetooth.parse import ContourPoint, ProductType


@pytest.fixture(autouse=True)
def establish_connection():
    """Patch establish_connection for every test - a real BLE connection must
    never be attempted. Configure `.return_value` or `.side_effect` as
    needed; left unconfigured, an attempt raises instead of hanging or
    reaching out over Bluetooth.
    """
    with patch(
        "gardena_bluetooth.client.establish_connection",
        AsyncMock(side_effect=AssertionError("should not connect")),
    ) as mock:
        yield mock


@pytest.mark.asyncio
async def test_establish_connection_failure_raises_communication_failure(
    establish_connection,
):
    device = BLEDevice(
        address="AA:BB:CC:DD:EE:FF",
        name="Gardena",
        details=None,
    )

    cached_connection = CachedConnection(DEFAULT_DELAY, lambda: device)
    client = Client(cached_connection)

    establish_connection.side_effect = BleakError("connection failed")

    with pytest.raises(
        CommunicationFailure,
        match="Communcation failed with device: connection failed",
    ):
        await client.read_char_raw("00000000-0000-0000-0000-000000000000")

    assert cached_connection._client is None


@pytest.mark.asyncio
async def test_read_char_returns_none_for_ignored_characteristic_without_io(
    establish_connection,
):
    device = BLEDevice(address="AA:BB:CC:DD:EE:FF", name="Gardena", details=None)
    cached_connection = CachedConnection(DEFAULT_DELAY, lambda: device)
    client = Client(cached_connection, ProductType.AQUA_CONTOURS)
    char = AquaContourContours.contour_receive

    assert await client.read_char(char) is None
    establish_connection.assert_not_called()


@pytest.mark.asyncio
async def test_write_char_noops_for_ignored_characteristic_without_io(
    establish_connection,
):
    device = BLEDevice(address="AA:BB:CC:DD:EE:FF", name="Gardena", details=None)
    cached_connection = CachedConnection(DEFAULT_DELAY, lambda: device)
    client = Client(cached_connection, ProductType.AQUA_CONTOURS)
    char = AquaContourContours.contour_receive

    assert await client.write_char(char, None) is None
    establish_connection.assert_not_called()


@pytest.mark.asyncio
async def test_subscribe_char_raises_for_ignored_characteristic(establish_connection):
    device = BLEDevice(address="AA:BB:CC:DD:EE:FF", name="Gardena", details=None)
    cached_connection = CachedConnection(DEFAULT_DELAY, lambda: device)
    client = Client(cached_connection, ProductType.AQUA_CONTOURS)
    char = AquaContourContours.contour_receive

    with pytest.raises(CharacteristicNoAccess):
        await client.subscribe_char(char, lambda _value: None)
    establish_connection.assert_not_called()


@pytest.mark.asyncio
async def test_subscribe_char_raw_raises_when_characteristic_not_notifiable(
    establish_connection,
):
    device = BLEDevice(address="AA:BB:CC:DD:EE:FF", name="Gardena", details=None)
    cached_connection = CachedConnection(DEFAULT_DELAY, lambda: device)
    client = Client(cached_connection)

    fake_characteristic = MagicMock()
    fake_characteristic.properties = ["read"]
    fake_client = MagicMock()
    fake_client.is_connected = True
    fake_client.services.get_characteristic.return_value = fake_characteristic
    establish_connection.side_effect = None
    establish_connection.return_value = fake_client

    with pytest.raises(CharacteristicNoAccess):
        await client.subscribe_char_raw("uuid", lambda *_: None)


def _fake_segmented_client(write_gatt_char, *, notify_uuid, write_uuid):
    notify_callback = None

    async def _start_notify(_characteristic, callback):
        nonlocal notify_callback
        notify_callback = callback

    fake_notify_characteristic = MagicMock(name="notify_characteristic")
    fake_notify_characteristic.properties = ["read", "notify"]
    fake_write_characteristic = MagicMock(name="write_characteristic")
    fake_write_characteristic.properties = ["write"]

    def _get_characteristic(uuid):
        if uuid == notify_uuid:
            return fake_notify_characteristic
        if uuid == write_uuid:
            return fake_write_characteristic
        raise AssertionError(f"Unexpected characteristic lookup for {uuid}")

    fake_client = MagicMock()
    fake_client.is_connected = True
    fake_client.services.get_characteristic.side_effect = _get_characteristic
    fake_client.start_notify = AsyncMock(side_effect=_start_notify)
    fake_client.stop_notify = AsyncMock()
    fake_client.write_gatt_char = AsyncMock(side_effect=write_gatt_char)

    def _notify(data: bytes):
        notify_callback(fake_notify_characteristic, data)

    return fake_client, fake_notify_characteristic, fake_write_characteristic, _notify


@pytest.mark.asyncio
async def test_read_raw_segmented_acks_single_final_frame(establish_connection):
    """frames_left is 1-indexed - frames_left == 1 on the first frame means
    this is a single-frame transfer, and it still gets acked."""
    device = BLEDevice(
        address="AA:BB:CC:DD:EE:FF",
        name="Gardena",
        details=None,
    )

    cached_connection = CachedConnection(DEFAULT_DELAY, lambda: device)
    client = Client(cached_connection, ProductType.AQUA_CONTOURS)
    char = AquaContourContours.contour_points_1

    async def _write_gatt_char(_characteristic, data, response=None):
        cmd = data[0] // 32
        if cmd == 3:  # QUERY
            notify(bytes([0, 1, 45, 45] + [0] * 14))  # FIRST, frames_left=1 (final)

    fake_client, fake_notify_characteristic, fake_write_characteristic, notify = (
        _fake_segmented_client(
            _write_gatt_char,
            notify_uuid=char.uuid,
            write_uuid=char.write_uuid,
        )
    )
    establish_connection.side_effect = None
    establish_connection.return_value = fake_client

    payload = await client.read_raw_segmented(char, index=0, timeout=1)

    assert char.decode(payload) == [ContourPoint(90, 450)]
    assert fake_client.write_gatt_char.await_args_list == [
        call(fake_write_characteristic, bytes([(3 << 5) | 0]), response=True),
        call(fake_write_characteristic, bytes([(2 << 5) | 0]), response=True),
    ]
    fake_client.stop_notify.assert_awaited_once_with(fake_notify_characteristic)


@pytest.mark.asyncio
async def test_read_raw_segmented_only_acks_final_frame_of_multi_frame_transfer(
    establish_connection,
):
    """Only the frame reporting frames_left == 1 is acked, not the earlier ones."""
    device = BLEDevice(
        address="AA:BB:CC:DD:EE:FF",
        name="Gardena",
        details=None,
    )

    cached_connection = CachedConnection(DEFAULT_DELAY, lambda: device)
    client = Client(cached_connection, ProductType.AQUA_CONTOURS)
    char = AquaContourContours.contour_points_1

    async def _write_gatt_char(_characteristic, data, response=None):
        cmd = data[0] // 32
        if cmd == 3:  # QUERY
            notify(bytes([0, 3, 45, 45] + [0] * 14))  # FIRST, frames_left=3
            notify(bytes([1 << 5, 2, 0, 90] + [0] * 14))  # NEXT, frames_left=2
            notify(bytes([1 << 5, 1, 1, 45] + [0] * 14))  # NEXT, frames_left=1 (final)

    fake_client, fake_notify_characteristic, fake_write_characteristic, notify = (
        _fake_segmented_client(
            _write_gatt_char,
            notify_uuid=char.uuid,
            write_uuid=char.write_uuid,
        )
    )
    establish_connection.side_effect = None
    establish_connection.return_value = fake_client

    payload = await client.read_raw_segmented(char, index=0, timeout=1)

    assert char.decode(payload) == [
        ContourPoint(90, 450),
        ContourPoint(0, 900),
        ContourPoint(2, 450),
    ]
    assert fake_client.write_gatt_char.await_args_list == [
        call(fake_write_characteristic, bytes([(3 << 5) | 0]), response=True),
        call(fake_write_characteristic, bytes([(2 << 5) | 0]), response=True),
    ]
    fake_client.stop_notify.assert_awaited_once_with(fake_notify_characteristic)


@pytest.mark.asyncio
async def test_read_char_routes_segmented_characteristic_through_segmented_protocol(
    establish_connection,
):
    device = BLEDevice(
        address="AA:BB:CC:DD:EE:FF",
        name="Gardena",
        details=None,
    )

    cached_connection = CachedConnection(DEFAULT_DELAY, lambda: device)
    client = Client(cached_connection, ProductType.AQUA_CONTOURS)
    char = AquaContourContours.contour_points_1

    async def _write_gatt_char(_characteristic, data, response=None):
        cmd = data[0] // 32
        if cmd == 3:  # QUERY
            # FIRST, index=1, frames_left=1 (final)
            notify(bytes([(0 << 5) | 1, 1, 45, 45] + [0] * 14))

    fake_client, _fake_notify_characteristic, fake_write_characteristic, notify = (
        _fake_segmented_client(
            _write_gatt_char,
            notify_uuid=char.uuid,
            write_uuid=char.write_uuid,
        )
    )
    establish_connection.side_effect = None
    establish_connection.return_value = fake_client

    points = await client.read_char(char)

    assert points == [ContourPoint(90, 450)]
    assert fake_client.write_gatt_char.await_args_list == [
        call(fake_write_characteristic, bytes([(3 << 5) | 1]), response=True),
        call(fake_write_characteristic, bytes([(2 << 5) | 1]), response=True),
    ]


@pytest.mark.asyncio
async def test_read_raw_segmented_times_out_without_final_frame(establish_connection):
    device = BLEDevice(
        address="AA:BB:CC:DD:EE:FF",
        name="Gardena",
        details=None,
    )

    cached_connection = CachedConnection(DEFAULT_DELAY, lambda: device)
    client = Client(cached_connection, ProductType.AQUA_CONTOURS)
    char = AquaContourContours.contour_points_1

    async def _write_gatt_char(_characteristic, _data, response=None):
        pass  # no notification sent, so the read never completes

    fake_client, fake_notify_characteristic, _fake_write_characteristic, _notify = (
        _fake_segmented_client(
            _write_gatt_char,
            notify_uuid=char.uuid,
            write_uuid=char.write_uuid,
        )
    )
    establish_connection.side_effect = None
    establish_connection.return_value = fake_client

    with pytest.raises(CommunicationFailure, match="Timed out"):
        await client.read_raw_segmented(char, index=0, timeout=0.01)

    fake_client.stop_notify.assert_awaited_once_with(fake_notify_characteristic)
