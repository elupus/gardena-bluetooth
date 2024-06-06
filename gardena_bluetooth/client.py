import asyncio
import logging
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from datetime import datetime
from typing import TypeVar, overload

from bleak import BleakClient
from bleak.exc import BleakError
from bleak.backends.device import BLEDevice
from bleak_retry_connector import establish_connection

from .const import DeviceConfiguration
from .exceptions import (
    CharacteristicNoAccess,
    CharacteristicNotFound,
    CommunicationFailure,
)
from .parse import Characteristic, CharacteristicType

LOGGER = logging.getLogger(__name__)
DEFAULT_MISSING = object()
DEFAULT_TYPE = TypeVar("DEFAULT_TYPE")
DEFAULT_DELAY = 1


class CallLaterJob:
    """Helper to contain a function that is to be called later."""

    def __init__(self, fun: Callable[[], Awaitable[None]]) -> None:
        """Initialize a call later job."""
        self._fun = fun
        self._cancel: asyncio.TimerHandle | asyncio.Task | None = None

    def cancel(self):
        """Cancel any pending delay call."""
        if self._cancel:
            self._cancel.cancel()
            self._cancel = None

    async def _call(self):
        await self.call_now()

    async def call_now(self):
        """Call function now."""
        self.cancel()
        await self._fun()

    def call_later(self, delay: float):
        """Call function sometime later."""
        self.cancel()

        async def _call_task():
            await self._fun()
            self._cancel = None

        def _call():
            self._cancel = asyncio.create_task(_call_task())

        self._cancel = asyncio.get_event_loop().call_later(delay, _call)


class CachedConnection:
    """Recursive and delay closed client."""

    def __init__(
        self, disconnect_delay: float, device_lookup: Callable[[], BLEDevice]
    ) -> None:
        """Initialize cached client."""

        self._client: BleakClient | None = None
        self._lock = asyncio.Lock()
        self._count = 0
        self._lookup = device_lookup
        self._disconnect_delay = disconnect_delay
        self._disconnect_job = CallLaterJob(self._disconnect)

    async def disconnect(self):
        await self._disconnect_job.call_now()

    async def _disconnect(self):
        async with self._lock:
            if client := self._client:
                LOGGER.debug("Disconnecting from %s", self._client.address)
                self._client = None
                await client.disconnect()

    async def _connect(self) -> BleakClient:
        device = self._lookup()

        LOGGER.debug("Connecting to %s", device.address)
        self._client = await establish_connection(
            BleakClient, device, "Gardena Bluetooth", use_services_cache=True
        )
        LOGGER.debug("Connected to %s", device.address)
        return self._client

    @asynccontextmanager
    async def __call__(self):
        """Retrieve a context manager for a cached client."""
        self._disconnect_job.cancel()

        try:
            async with self._lock:
                if not (client := self._client) or not client.is_connected:
                    client = await self._connect()

                self._count += 1
                try:
                    yield client
                finally:
                    self._count -= 1

                    if not self._count and self._client:
                        self._disconnect_job.call_later(self._disconnect_delay)
        except BleakError as exception:
            await self._disconnect_job.call_now()
            LOGGER.debug("Unexpected disconnection from device %s", exception)
            raise CommunicationFailure(
                f"Communcation failed with device: {exception}"
            ) from exception


class Client:
    def __init__(self, client_or_device: CachedConnection | BLEDevice) -> None:
        if isinstance(client_or_device, CachedConnection):
            self._client = client_or_device
        else:
            self._client = CachedConnection(DEFAULT_DELAY, lambda: client_or_device)

    async def disconnect(self):
        await self._client.disconnect()

    @overload
    async def read_char_raw(self, uuid: str) -> bytes: ...

    @overload
    async def read_char_raw(
        self, uuid: str, default: DEFAULT_TYPE
    ) -> bytes | DEFAULT_TYPE: ...

    async def read_char_raw(
        self, uuid: str, default: DEFAULT_TYPE = DEFAULT_MISSING
    ) -> bytes | DEFAULT_TYPE:
        async with self._client() as client:
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
        self, char: Characteristic[CharacteristicType]
    ) -> CharacteristicType: ...

    @overload
    async def read_char(
        self,
        char: Characteristic[CharacteristicType],
        default: DEFAULT_TYPE,
    ) -> CharacteristicType | DEFAULT_TYPE: ...

    async def read_char(
        self,
        char: Characteristic[CharacteristicType],
        default: DEFAULT_TYPE = DEFAULT_MISSING,
    ) -> CharacteristicType | DEFAULT_TYPE:
        """Read data to from a characteristic."""
        try:
            return char.decode(await self.read_char_raw(char.uuid))
        except CharacteristicNotFound:
            if default is not DEFAULT_MISSING:
                return default
            raise

    async def write_char_raw(self, uuid: str, data: bytes, response: bool = True):
        async with self._client() as client:
            """Write data to a characteristic."""
            characteristic = client.services.get_characteristic(uuid)
            if characteristic is None:
                raise CharacteristicNotFound(f"Unable to find characteristic {uuid}")
            if "write" not in characteristic.properties:
                raise CharacteristicNoAccess(f"Characteristic {uuid} is not writable")
            await client.write_gatt_char(characteristic, data, response=response)

    async def write_char(
        self,
        char: Characteristic[CharacteristicType],
        value: CharacteristicType,
        response=True,
    ) -> None:
        """Write data to a characteristic."""
        data = char.encode(value)
        await self.write_char_raw(char.uuid, data, response)

    async def update_timestamp(self, now: datetime):
        try:
            timestamp = await self.read_char(DeviceConfiguration.unix_timestamp)
        except CharacteristicNoAccess:
            LOGGER.debug("No timestamp defined for device")
            return
        timestamp = timestamp.replace(tzinfo=now.tzinfo)
        delta = timestamp - now
        if abs(delta.total_seconds()) > 60:
            LOGGER.warning(
                "Updating time on device to match local time delta was %s", delta
            )
            await self.write_char(
                DeviceConfiguration.unix_timestamp,
                now.replace(tzinfo=None),
                True,
            )
        else:
            LOGGER.debug("No need to update timestamp local time delta was %s", delta)

    async def get_all_characteristics_uuid(self) -> set[str]:
        """Get all characteristics from device."""
        async with self._client() as client:
            characteristics = {
                characteristic.uuid
                for service in client.services
                for characteristic in service.characteristics
            }
            LOGGER.debug("Characteristics: %s", characteristics)
            return characteristics
