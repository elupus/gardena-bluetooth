from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum, Enum, auto
from typing import ClassVar, Generic, Self, TypeVar


def pretty_name(name: str):
    data = name.split("_")
    return " ".join(f"{part[0].upper()}{part[1:]}" for part in data)


class ProductType(Enum):
    UNKNOWN = auto()
    MOWER = auto()
    WATER_COMPUTER = auto()
    VALVE = auto()
    PUMP = auto()
    PRESSURE_TANKS = auto()
    AQUA_CONTOURS = auto()
    AUTOMATS = auto()

    @staticmethod
    def from_manufacturer_data(data: "ManufacturerData") -> "ProductType":
        if data.group == 10:
            return ProductType.MOWER

        if data.group == 18:
            if data.model in (0, 1) and data.variant == 1:
                return ProductType.WATER_COMPUTER
            if data.model == 2 and data.variant == 1:
                return ProductType.VALVE
            if data.model == 16:
                return ProductType.AQUA_CONTOURS
            return ProductType.UNKNOWN

        if data.group == 17:
            if data.model == 1:
                return ProductType.PUMP
            if data.model == 2:
                return ProductType.PRESSURE_TANKS
            if data.model == 3:
                return ProductType.AUTOMATS
            return ProductType.UNKNOWN

        return ProductType.UNKNOWN


CharacteristicType = TypeVar("CharacteristicType")


@dataclass
class Characteristic(Generic[CharacteristicType]):
    uuid: str
    variant: str | None = None
    name: str = ""
    registry: ClassVar[dict[str, list[Self]]] = {}
    unique_id: str = field(init=False)

    def __set_name__(self, _, name: str):
        self.name = pretty_name(name)

    def __post_init__(self):
        if self.variant is not None:
            unique_id = self.uuid + ":" + self.variant
        else:
            unique_id = self.uuid
        object.__setattr__(self, "unique_id", unique_id)
        self.registry.setdefault(self.uuid, []).append(self)

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
class CharacteristicWeekday(Characteristic[list[bool]]):
    @classmethod
    def decode(cls, data: bytes) -> list[bool]:
        value = int.from_bytes(data, "little", signed=False)
        return [(value >> i) & 1 != 0 for i in range(7)]

    @classmethod
    def encode(cls, value: list[bool]) -> bytes:
        int_value = 0
        for i, day in enumerate(value):
            if day:
                int_value |= 1 << i
        return int_value.to_bytes(1, "little", signed=False)


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
    unique_id: ClassVar[str]
    uuid: ClassVar[str]
    variant: ClassVar[str | None] = None
    products: ClassVar[set[ProductType]] = set(ProductType)
    registry: ClassVar[dict[str, list[Self]]] = {}
    characteristics: ClassVar[dict[str, Characteristic]] = {}

    @classmethod
    def find_service(cls, uuid: str, product_type: ProductType) -> Self | None:
        services = cls.registry.get(uuid, [])
        for service in services:
            if product_type in service.products:
                return service
        return None

    @classmethod
    def services_for_product_type(cls, product_type: ProductType) -> list[Self]:
        """Get all services for a product type."""
        return [
            service
            for services in Service.registry.values()
            for service in services
            if product_type in service.products
        ]

    def __init_subclass__(cls, /, **kwargs):
        super().__init_subclass__(**kwargs)
        if ABC in cls.__bases__:
            return
        if cls.variant is not None:
            cls.unique_id = cls.uuid + ":" + cls.variant
        else:
            cls.unique_id = cls.uuid
        cls.registry.setdefault(cls.uuid, []).append(cls)

        cls.characteristics = {}
        for value in vars(cls).values():
            if isinstance(value, Characteristic):
                cls.characteristics[value.uuid] = value


class EnumOrInt(IntEnum):
    @classmethod
    def enum_or_int(cls, value: int):
        try:
            return cls(value)
        except ValueError:
            return value


class ProductGroup(EnumOrInt):
    MOWER = 10
    GARDEN_PUMP = 17
    WATER_CONTROL = 18


@dataclass
class ManufacturerData:
    company: ClassVar[int] = 0x0426
    pairable: bool | None = None
    serial: int | None = None
    group: int | ProductGroup | None = None
    model: int | None = None
    variant: int | None = None

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
        res = ManufacturerData()
        res.update(data)
        return res

    def update(self, data: bytes):
        value = ManufacturerData.decode_dict(data)
        info = dict(enumerate(value.get(6, b"")))

        if (data := info.get(0)) is not None:
            self.group = ProductGroup.enum_or_int(data)
        if (data := info.get(1)) is not None:
            self.model = data
        if (data := info.get(2)) is not None:
            self.variant = data

        if (data := value.get(4)) is not None:
            self.serial = int.from_bytes(data, "little")
        if (data := value.get(5)) is not None:
            self.pairable = bool.from_bytes(data, "little")
