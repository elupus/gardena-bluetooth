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
    async with BleakScanner(service_uuids=[ScanService, FotaService]) as scanner:
        async with asyncio.timeout(10):
            async for device, data in scanner.advertisement_data():
                if device.address != address:
                    continue
                if ManufacturerData.company not in data.manufacturer_data:
                    click.echo("No manufacturer data found in advertisement skipping")
                    continue
                manufacturer_data = ManufacturerData.decode(
                    data.manufacturer_data[ManufacturerData.company]
                )
                if manufacturer_data.model is None:
                    click.echo("No model found in manufacturer data skipping")
                    continue

                break

    product_type = ProductType.from_manufacturer_data(manufacturer_data)

    click.echo(f"Advertised data: {manufacturer_data}")
    click.echo(f"Product type: {ProductType.from_manufacturer_data(manufacturer_data)}")

    async with BleakClient(device, timeout=20) as client:
        for service in client.services:
            click.echo(f"Service: {service}")

            service_parser = Service.find_service(service.uuid, product_type)

            for char in service.characteristics:
                click.echo(f" -  {char}")
                click.echo(f"    Prop: {char.properties}")

                data = None
                if "read" in char.properties:
                    try:
                        data = await client.read_gatt_char(char.uuid)
                    except BleakError as exc:
                        click.echo(f"    Failed: {repr(exc)}")

                if data is not None:
                    if service_parser and (
                        parser := service_parser.characteristics.get(char.uuid)
                    ):
                        click.echo(f"    Data: {parser.decode(data)}")
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
