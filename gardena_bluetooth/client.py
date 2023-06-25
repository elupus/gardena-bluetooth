import asyncio
import logging
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager

from bleak import BleakClient
from bleak.backends.device import BLEDevice
from bleak_retry_connector import establish_connection

LOGGER = logging.getLogger(__name__)


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


class CachedClient:
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

        async with self._lock:
            if not (client := self._client) or not client.is_connected:
                client = await self._connect()

            self._count += 1
            try:
                yield client
            except:
                LOGGER.debug("Disconnecting client due to exception")
                await self._disconnect_job.call_now()
                raise

            finally:
                self._count -= 1

                if not self._count and self._client:
                    self._disconnect_job.call_later(self._disconnect_delay)
