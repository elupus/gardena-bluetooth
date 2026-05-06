import asyncio
from functools import partial

import asyncclick as click
from bleak import (
    BleakClient,
    BleakError,
)
from bleak.backends.characteristic import BleakGATTCharacteristic
from bleak.uuids import uuidstr_to_str

from .parse import Characteristic, CharacteristicBytes, Service
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
                    char_parser = service_parser.characteristics.get(char.uuid)

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

    def _char_callback(
        service_name: str,
        char_parser: Characteristic,
        gatt_char: BleakGATTCharacteristic,
        data: bytes,
    ):
        try:
            value = char_parser.decode(data)
        except ValueError:
            click.echo(
                "%s.%s failed to decode %s with char parser %s",
                service_name,
                char_parser.name,
                data,
                char_parser,
                err=True,
            )
        click.echo(f"{service_name}.{char_parser.name}: {value!r}")

    async def _char_read(
        client: BleakClient,
        gatt_char: BleakGATTCharacteristic,
        char_parser: Characteristic,
        service_name: str,
    ):
        try:
            data = await client.read_gatt_char(char.uuid)
        except BleakError as exc:
            click.echo(
                f"{service_name}.{char_parser.name}: Failed - {repr(exc)}",
                err=True,
            )
            return
        _char_callback(service_name, char_parser, gatt_char, data)

    click.echo(f"Connecting: {address}")
    async with BleakClient(device.ble_device, timeout=20) as client:
        for service in client.services:
            service_parser = Service.find_service(service.uuid, product_type)
            service_name = service_parser.__name__ if service_parser else service.uuid

            for char in service.characteristics:
                char_parser = None
                if service_parser:
                    char_parser = service_parser.characteristics.get(char.uuid)
                if char_parser is None:
                    char_parser = CharacteristicBytes(char.uuid, name=char.uuid)

                if "read" in char.properties:
                    await _char_read(client, char, char_parser, service_name)

                if "notify" in char.properties:
                    await client.start_notify(
                        char, partial(_char_callback, service_name, char_parser)
                    )

        while True:
            await asyncio.sleep(1)


@main.command()
async def chars():
    for char in Characteristic.registry.values():
        click.echo(char.name)


try:
    main()
except KeyboardInterrupt:
    pass
