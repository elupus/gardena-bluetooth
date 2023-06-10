from typing import Any, ClassVar
from dataclasses import dataclass
from datetime import datetime


def pretty_name(name: str):
    data = name.split("_")
    return " ".join(f"{part[0].upper()}{part[1:]}" for part in data)


@dataclass
class Characteristic:
    uuid: str
    name: str = ""
    registry: ClassVar[dict[str, "Characteristic"]] = {}

    def __set_name__(self, _, name: str):
        self.name = pretty_name(name)

    def __post_init__(self):
        self.registry[self.uuid] = self

    @classmethod
    def decode(cls, data: bytes) -> Any:
        raise NotImplementedError(f"Decoding of {type(cls)} is not implemented")

    @classmethod
    def encode(cls, data: Any) -> bytes:
        raise NotImplementedError(f"Encoding of {type(cls)} is not implemented")


@dataclass
class CharacteristicBytes(Characteristic):
    @classmethod
    def decode(cls, data: bytes) -> bytes:
        return data

    @classmethod
    def encode(cls, value: bytes) -> bytes:
        return value


@dataclass
class CharacteristicBool(Characteristic):
    @classmethod
    def decode(cls, data: bytes) -> bool:
        return data[0] != 0

    @classmethod
    def encode(data: bool) -> bytes:
        if data:
            return b"\x01"
        return b"\x00"


@dataclass
class CharacteristicString(Characteristic):
    @classmethod
    def decode(cls, data: bytes) -> str:
        return data.decode("ASCII")

    @classmethod
    def encode(cls, value: str) -> bytes:
        return value.encode("ASCII")


@dataclass
class CharacteristicInt(Characteristic):
    @classmethod
    def decode(cls, data: bytes) -> int:
        return int.from_bytes(data, "little", signed=True)

    @classmethod
    def encode(cls, value: int) -> bytes:
        return value.to_bytes(1, "little", signed=True)


@dataclass
class CharacteristicLong(Characteristic):
    @classmethod
    def decode(cls, data: bytes) -> int:
        return int.from_bytes(data, "little", signed=True)

    @classmethod
    def encode(cls, value: int) -> bytes:
        return value.to_bytes(4, "little", signed=True)


@dataclass
class CharacteristicUInt16(Characteristic):
    @classmethod
    def decode(cls, data: bytes) -> int:
        return int.from_bytes(data, "little", signed=False)

    @classmethod
    def encode(cls, value: int) -> bytes:
        return value.to_bytes(2, "little", signed=False)


@dataclass
class CharacteristicLongArray(Characteristic):
    @classmethod
    def decode(cls, data: bytes) -> list[datetime]:
        return [int.from_bytes(data[i : i + 4]) for i in range(0, len(data), 4)]


@dataclass
class CharacteristicTime(Characteristic):
    @classmethod
    def decode(cls, data: bytes) -> datetime:
        value = int.from_bytes(data, "little")
        return datetime.fromtimestamp(value)

    @classmethod
    def encode(cls, value: datetime) -> bytes:
        return int(value.timestamp).to_bytes(4, "little", signed=True)


@dataclass
class CharacteristicTimeArray(Characteristic):
    @classmethod
    def decode(cls, data: bytes) -> list[datetime]:
        return [
            datetime.fromtimestamp(value)
            for value in CharacteristicLongArray.decode(data)
        ]


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
