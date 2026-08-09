import asyncio
from functools import partial

import asyncclick as click
from bleak import (
    BleakClient,
    BleakError,
)
from bleak.uuids import uuidstr_to_str

from .client import CachedConnection, Client
from .exceptions import CharacteristicNoAccess, GardenaBluetoothException
from .parse import Characteristic, CharacteristicSegmented, ManufacturerData, Service
from .scan import async_get_devices, async_scan_devices

IGNORED_NOTIFY_UUIDS = {
    # SMP
    "da2e7828-fbce-4e01-ae9e-261174997c48"
}


@click.group()
async def main():
    pass


@main.command()
async def scan():
    click.echo("Scanning for devices")

    async for data in async_scan_devices():
        advertisement = data.advertisement
        device = data.ble_device
        manufacturer_data = data.manufacturer_data

        click.echo(f"Device: {device}")
        for service in advertisement.service_uuids:
            click.echo(f" - Service: {service} {uuidstr_to_str(service)}")
        click.echo(f" - Data: {advertisement.service_data}")
        click.echo(f" - Manu: {advertisement.manufacturer_data}")
        click.echo(f" -     : {manufacturer_data}")

        click.echo(f" - RSSI: {advertisement.rssi}")
        click.echo()


@main.command()
@click.argument("address")
async def connect(address: str):
    click.echo(f"Detecting: {address}")

    devices = await async_get_devices({address})
    device = devices[address]
    product_type = device.manufacturer_data.product_type

    click.echo(f"Advertised data: {device.manufacturer_data}")
    click.echo(f"Product type: {product_type}")

    click.echo(f"Connecting to: {address}")
    async with BleakClient(device.ble_device, timeout=20) as client:
        for service in client.services:
            service_parser = Service.find_service(service.uuid, product_type)

            click.echo(
                f"Service: {service.uuid}: {service_parser.__name__ if service_parser else service.description}"
            )

            for char in service.characteristics:
                char_parser = None
                if service_parser:
                    chars = service_parser.find_characteristics(char.uuid)
                    char_parser = chars[0] if chars else None

                click.echo(
                    f" -  {char.uuid}: {char_parser.name if char_parser else char.description}"
                )
                click.echo(f"    Prop: {char.properties}")

                data = None
                if "read" in char.properties:
                    try:
                        data = await client.read_gatt_char(char.uuid)
                    except BleakError as exc:
                        click.echo(f"    Failed: {repr(exc)}")

                if data is not None:
                    click.echo(f"    Raw: {data}")
                    if char_parser:
                        click.echo(f"    Data: {char_parser.decode(data)!r}")


@main.command()
@click.argument("address")
async def monitor(address: str):
    click.echo(f"Detecting: {address}")

    devices = await async_get_devices({address})
    device = devices[address]
    product_type = device.manufacturer_data.product_type

    click.echo(f"Advertised data: {device.manufacturer_data}")
    click.echo(f"Product type: {product_type}")

    def _callback(char: Characteristic, value):
        click.echo(f"{char.name}: {value!r}")

    # monitor runs for the life of the process, unlike Client's usual
    # short-lived operations, so keep the connection open far longer than
    # the default idle-disconnect delay.
    connection = CachedConnection(3600 * 24, lambda: device.ble_device)
    client = Client(connection, product_type)

    try:
        click.echo(f"Connecting: {address}")
        characteristics = await client.get_all_characteristics()
        for char in characteristics.values():
            try:
                value = await client.read_char(char)
            except GardenaBluetoothException as exc:
                click.echo(f"{char.name}: Failed to read - {repr(exc)}", err=True)
            else:
                click.echo(f"{char.name}: {value!r}")

            if isinstance(char, CharacteristicSegmented):
                continue

            try:
                await client.subscribe_char(char, partial(_callback, char))
            except CharacteristicNoAccess:
                pass
            except GardenaBluetoothException as exc:
                click.echo(f"{char.name}: Failed to subscribe - {repr(exc)}", err=True)

        while True:
            await asyncio.sleep(1)
    finally:
        await client.disconnect()


@main.command()
@click.argument("manufacturer_data")
async def parse(manufacturer_data: str):
    data = ManufacturerData()
    data.update(bytes.fromhex(manufacturer_data))
    click.echo(data)
    click.echo(data.product_type)


@main.command()
async def chars():
    for char in Characteristic.registry.values():
        click.echo(char.name)


try:
    main()
except KeyboardInterrupt:
    pass
