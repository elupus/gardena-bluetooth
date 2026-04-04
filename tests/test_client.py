from bleak.backends.device import BLEDevice
from bleak.exc import BleakError
from unittest.mock import patch

import pytest

from gardena_bluetooth.client import CachedConnection, Client, DEFAULT_DELAY
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
