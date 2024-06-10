import anyio
import asyncclick as click
from bleak import (
    AdvertisementData,
    BleakClient,
    BleakGATTCharacteristic,
    BleakScanner,
    BLEDevice,
)
from bleak.uuids import uuidstr_to_str

from .const import FotaService, ScanService
from .parse import Characteristic, ManufacturerData


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
        await anyio.sleep_forever()


@main.command()
@click.argument("address")
async def connect(address: str):
    click.echo(f"Connecting to: {address}")
    async with BleakClient(address, timeout=20) as client:
        for service in client.services:
            click.echo(f"Service: {service}")

            async def read_print(char: BleakGATTCharacteristic):
                parser = Characteristic.registry.get(char.uuid)
                if "read" in char.properties:
                    data = await client.read_gatt_char(char.uuid)
                else:
                    data = None
                click.echo(f" -  {char}")
                click.echo(f" -  {char.properties}")
                if data is not None and parser:
                    click.echo(f" -  Data: {parser.decode(data)}")

            async with anyio.create_task_group() as tg:
                for char in service.characteristics:
                    tg.start_soon(read_print, char)


@main.command()
async def chars():
    for char in Characteristic.registry.values():
        click.echo(char.name)


try:
    main()
except KeyboardInterrupt:
    pass
