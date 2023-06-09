from typing import Any, ClassVar
from dataclasses import dataclass


def pretty_name(name: str):
    data = name.split("_")
    return " ".join(
        f"{part[0].upper()}{part[1:]}"
        for part in data
    )

@dataclass
class Characteristic:
    uuid: str
    name: str = ""
    registry: ClassVar[dict[str, "Characteristic"]] = {}

    def __set_name__(self, _, name: str):
        self.name = pretty_name(name)

    def __post_init__(self):
        self.registry[self.uuid] = self

    @staticmethod
    def decode(data: bytes) -> Any:
        return None


@dataclass
class CharacteristicBytes(Characteristic):
    @staticmethod
    def decode(data: bytes) -> bytes:
        return data


@dataclass
class CharacteristicBool(Characteristic):
    @staticmethod
    def decode(data: bytes) -> bool:
        return data[0] != 0


@dataclass
class CharacteristicString(Characteristic):
    @staticmethod
    def decode(data: bytes) -> str:
        return data.decode("ASCII")


@dataclass
class CharacteristicInt(Characteristic):
    @staticmethod
    def decode(data: bytes) -> int:
        return int.from_bytes(data, "little")


class Service:
    uuid: ClassVar[str]
    registry: ClassVar[dict[str, "Service"]] = {}

    def __init_subclass__(cls, /, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.registry[cls.uuid] = cls

    @classmethod
    def characteristics(cls):
        for value in vars(cls).values():
            if isinstance(value, Characteristic):
                yield value
