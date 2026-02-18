from __future__ import annotations

from bleak.uuids import register_uuids

from .const import ScanService
from .parse import Service, Characteristic


def prefix(name: str) -> str:
    return f"Gardena {name}"


register_uuids(
    {
        uuid: prefix(", ".join(service.__name__ for service in services))
        for uuid, services in Service.registry.items()
    }
)

register_uuids(
    {
        uuid: prefix(", ".join(char.name for char in chars))
        for uuid, chars in Characteristic.registry.items()
    }
)

register_uuids({ScanService: "Husqvarna"})
