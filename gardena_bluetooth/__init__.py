from __future__ import annotations

from bleak.uuids import register_uuids

from .const import ScanService
from .parse import Service

register_uuids(
    {
        service.uuid: f"Gardena {service.__name__}"
        for service in Service.registry.values()
    }
)

register_uuids(
    {
        char.uuid: f"Gardena {service.__name__} {char.name}"
        for service in Service.registry.values()
        for char in service.characteristics()
    }
)

register_uuids({ScanService: "Husqvarna"})
