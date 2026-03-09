import asyncio
import asyncclick as click
from bleak import (
    AdvertisementData,
    BleakClient,
    BleakError,
    BleakScanner,
    BLEDevice,
)
from bleak.uuids import uuidstr_to_str

from .const import FotaService, ScanService
from .parse import Characteristic, ManufacturerData, ProductType, Service


@click.group()
async def main():
    pass


@main.command()
async def scan():
    click.echo("Scanning for devices")

    devices = set()

    def detected(device: BLEDevice, advertisement: AdvertisementData):
        if device not in devices:
            if ScanService not in advertisement.service_uuids:
                return
            devices.add(device)

        click.echo(f"Device: {device}")
        for service in advertisement.service_uuids:
            click.echo(f" - Service: {service} {uuidstr_to_str(service)}")
        click.echo(f" - Data: {advertisement.service_data}")
        click.echo(f" - Manu: {advertisement.manufacturer_data}")

        if data := advertisement.manufacturer_data.get(ManufacturerData.company):
            decoded = ManufacturerData.decode(data)
            click.echo(f" -     : {decoded}")

        click.echo(f" - RSSI: {advertisement.rssi}")
        click.echo()

    async with BleakScanner(detected, service_uuids=[ScanService, FotaService]):
        while True:
            await asyncio.sleep(1)


@main.command()
@click.argument("address")
async def connect(address: str):
    click.echo(f"Connecting to: {address}")

    manufacturer_data = ManufacturerData()
    async with BleakScanner(service_uuids=[ScanService, FotaService]) as scanner:
        async with asyncio.timeout(10):
            async for device, data in scanner.advertisement_data():
                if device.address != address:
                    continue

                raw = data.manufacturer_data.get(ManufacturerData.company)
                if raw is None:
                    continue

                manufacturer_data.update(raw)

                product_type = ProductType.from_manufacturer_data(manufacturer_data)
                if product_type is ProductType.UNKNOWN:
                    continue

                break

    click.echo(f"Advertised data: {manufacturer_data}")
    click.echo(f"Product type: {product_type}")

    async with BleakClient(device, timeout=20) as client:
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
                    if char_parser:
                        click.echo(f"    Data: {char_parser.decode(data)!r}")
                    else:
                        click.echo(f"    Data: {data}")


@main.command()
async def chars():
    for char in Characteristic.registry.values():
        click.echo(char.name)


try:
    main()
except KeyboardInterrupt:
    pass
