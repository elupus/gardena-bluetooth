from unittest.mock import AsyncMock, patch

import pytest
from bleak.backends.device import BLEDevice
from bleak.exc import BleakError

from gardena_bluetooth.client import DEFAULT_DELAY, CachedConnection, Client
from gardena_bluetooth.const import Valve1, Valve2
from gardena_bluetooth.exceptions import CommunicationFailure


@pytest.mark.asyncio
async def test_establish_connection_failure_raises_communication_failure():
    device = BLEDevice(
        address="AA:BB:CC:DD:EE:FF",
        name="Gardena",
        details=None,
    )

    cached_connection = CachedConnection(DEFAULT_DELAY, lambda: device)
    client = Client(cached_connection)

    with patch(
        "gardena_bluetooth.client.establish_connection",
        side_effect=BleakError("connection failed"),
    ):
        with pytest.raises(
            CommunicationFailure,
            match="Communcation failed with device: connection failed",
        ):
            await client.read_char_raw("00000000-0000-0000-0000-000000000000")

    assert cached_connection._client is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("service", "expected_uuid"),
    [
        (Valve1, "98bda020-0b0e-421a-84e5-ddbf75dc6de4"),
        (Valve2, "98bda120-0b0e-421a-84e5-ddbf75dc6de4"),
    ],
)
async def test_start_watering_writes_lwm2m_execute_payload(service, expected_uuid):
    """start_watering must encode {0:'18', 1:str(duration)} on the right char."""
    device = BLEDevice(address="AA:BB:CC:DD:EE:FF", name="Gardena", details=None)
    client = Client(CachedConnection(DEFAULT_DELAY, lambda: device))
    client._unique_id = {service.start_watering.unique_id}

    with patch.object(client, "write_char_raw", new=AsyncMock()) as mock_write:
        await client.start_watering(service, 30)

    mock_write.assert_awaited_once_with(expected_uuid, b"0='18',1='30'", None)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("service", "expected_uuid"),
    [
        (Valve1, "98bda021-0b0e-421a-84e5-ddbf75dc6de4"),
        (Valve2, "98bda121-0b0e-421a-84e5-ddbf75dc6de4"),
    ],
)
async def test_stop_watering_writes_command_source_only(service, expected_uuid):
    """stop_watering must encode {0:'18'} on the right char."""
    device = BLEDevice(address="AA:BB:CC:DD:EE:FF", name="Gardena", details=None)
    client = Client(CachedConnection(DEFAULT_DELAY, lambda: device))
    client._unique_id = {service.stop_watering.unique_id}

    with patch.object(client, "write_char_raw", new=AsyncMock()) as mock_write:
        await client.stop_watering(service)

    mock_write.assert_awaited_once_with(expected_uuid, b"0='18'", None)
