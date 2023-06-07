import asyncclick as click
import anyio
from bleak import BleakScanner, BLEDevice, AdvertisementData
from bleak.uuids import uuidstr_to_str

@click.group()
async def main():
    pass

@main.command()
async def scan():
    click.echo("Scanning for devices")

    devices = set()
    def detected(device: BLEDevice, advertisement: AdvertisementData):
        if device not in devices:
            click.echo(f"Device: {device}")
            for service in advertisement.service_uuids:
                click.echo(f" - Service: {service} {uuidstr_to_str(service)}")
            click.echo()
            devices.add(device)

    async with BleakScanner(detected):
        await anyio.sleep_forever()

try:
    main()
except KeyboardInterrupt:
    pass
