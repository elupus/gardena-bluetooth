from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum, Enum, auto
from typing import ClassVar, Generic, TypeVar


def pretty_name(name: str):
    data = name.split("_")
    return " ".join(f"{part[0].upper()}{part[1:]}" for part in data)


class ProductType(Enum):
    MOWER = auto()
    WATER_COMPUTER = auto()
    VALVE = auto()
    PUMP = auto()

    @staticmethod
    def from_manufacturer_data(data: "ManufacturerData") -> "ProductType":
        if data.group == 10:
            return ProductType.MOWER
        if data.group == 18 and data.model in (0, 1) and data.variant == 1:
            return ProductType.WATER_COMPUTER
        if data.group == 18 and data.model == 2 and data.variant == 1:
            return ProductType.VALVE
        if data.group == 17 and data.model == 1:
            return ProductType.PUMP
        return None


CharacteristicType = TypeVar("CharacteristicType")


@dataclass
class Characteristic(Generic[CharacteristicType]):
    uuid: str
    name: str = ""
    registry: ClassVar[dict[str, "Characteristic"]] = {}

    def __set_name__(self, _, name: str):
        self.name = pretty_name(name)

    def __post_init__(self):
        self.registry[self.uuid] = self

    @classmethod
    def decode(cls, data: bytes) -> CharacteristicType:
        raise NotImplementedError(f"Decoding of {type(cls)} is not implemented")

    @classmethod
    def encode(cls, data: CharacteristicType) -> bytes:
        raise NotImplementedError(f"Encoding of {type(cls)} is not implemented")


@dataclass
class CharacteristicBytes(Characteristic[bytes]):
    @classmethod
    def decode(cls, data: bytes) -> bytes:
        return data

    @classmethod
    def encode(cls, value: bytes) -> bytes:
        return value


@dataclass
class CharacteristicBool(Characteristic[bool]):
    @classmethod
    def decode(cls, data: bytes) -> bool:
        return data[0] != 0

    @classmethod
    def encode(cls, data: bool) -> bytes:
        if data:
            return b"\x01"
        return b"\x00"


@dataclass
class CharacteristicString(Characteristic[str]):
    @classmethod
    def decode(cls, data: bytes) -> str:
        return data.decode("ASCII", "replace")

    @classmethod
    def encode(cls, value: str) -> bytes:
        return value.encode("ASCII")


@dataclass
class CharacteristicNullString(Characteristic[str]):
    @classmethod
    def decode(cls, data: bytes) -> str:
        return data.partition(b"\x00")[0].decode("ASCII", "replace")

    @classmethod
    def encode(cls, value: str) -> bytes:
        return value.encode("ASCII")


@dataclass
class CharacteristicNullStringUf8(Characteristic[str]):
    @classmethod
    def decode(cls, data: bytes) -> str:
        return data.partition(b"\x00")[0].decode("utf-8", "replace")

    @classmethod
    def encode(cls, value: str) -> bytes:
        return value.encode("utf-8")


@dataclass
class CharacteristicInt(Characteristic[int]):
    @classmethod
    def decode(cls, data: bytes) -> int:
        return int.from_bytes(data, "little", signed=True)

    @classmethod
    def encode(cls, value: int) -> bytes:
        return value.to_bytes(1, "little", signed=True)


@dataclass
class CharacteristicLong(Characteristic[int]):
    @classmethod
    def decode(cls, data: bytes) -> int:
        return int.from_bytes(data, "little", signed=True)

    @classmethod
    def encode(cls, value: int) -> bytes:
        return value.to_bytes(4, "little", signed=True)


@dataclass
class CharacteristicUInt16(Characteristic[int]):
    @classmethod
    def decode(cls, data: bytes) -> int:
        return int.from_bytes(data, "little", signed=False)

    @classmethod
    def encode(cls, value: int) -> bytes:
        return value.to_bytes(2, "little", signed=False)


@dataclass
class CharacteristicLongArray(Characteristic[list[int]]):
    @classmethod
    def decode(cls, data: bytes) -> list[int]:
        return [
            int.from_bytes(data[i : i + 4], "little", signed=True)
            for i in range(0, len(data), 4)
        ]


@dataclass
class CharacteristicTime(Characteristic[datetime]):
    @classmethod
    def decode(cls, data: bytes) -> datetime:
        value = int.from_bytes(data, "little")
        return datetime.fromtimestamp(value)

    @classmethod
    def encode(cls, value: datetime) -> bytes:
        return int(value.timestamp()).to_bytes(4, "little", signed=True)


@dataclass
class CharacteristicTimeArray(Characteristic[list[datetime]]):
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


class EnumOrInt(IntEnum):
    @classmethod
    def enum_or_int(cls, value: int):
        try:
            return cls(value)
        except ValueError:
            return value


class ProductGroup(EnumOrInt):
    MOWER = 1
    GARDEN_PUMP = 17
    WATER_CONTROL = 18


@dataclass
class ManufacturerData:
    company: ClassVar[int] = 0x0426
    pairable: bool | None
    serial: int | None
    group: int | ProductGroup | None
    model: int | None
    variant: int | None

    @staticmethod
    def decode_dict(data: bytes):
        res: dict[int, bytes] = {}
        idx = 0
        while idx < len(data):
            size = data[idx]
            key = data[idx + 1]
            res[key] = data[idx + 2 : idx + size + 1]
            idx += size + 1
        return res

    @staticmethod
    def decode(data: bytes):
        value = ManufacturerData.decode_dict(data)
        info = dict(enumerate(value.get(6, b"")))
        serial = value.get(4)
        pairable = value.get(5)
        return ManufacturerData(
            pairable=bool.from_bytes(pairable, "little") if pairable else None,
            serial=int.from_bytes(serial, "little") if serial else None,
            group=ProductGroup.enum_or_int(info.get(0)),
            model=info.get(1),
            variant=info.get(2),
        )
