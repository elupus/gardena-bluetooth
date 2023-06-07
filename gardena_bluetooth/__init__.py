from bleak.uuids import register_uuids
from .const import Value, DeviceConfiguration, DeviceInformation, Battery
from enum import Enum
from typing import Type


def register_enum_uuids(enum: Type[Enum]):
    uuids = {data.value: f"Gardena {enum.__name__} {data.name}" for data in enum}
    register_uuids(uuids)


register_enum_uuids(Value)
register_enum_uuids(DeviceConfiguration)
register_enum_uuids(DeviceInformation)
register_enum_uuids(Battery)
