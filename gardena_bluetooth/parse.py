from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone, time
from enum import IntEnum, Enum, auto
from typing import ClassVar, Generic, Self, TypeVar
from calendar import Day


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
            if data.model in (
                ProductModelWaterControl.CLASSIC1,
                ProductModelWaterControl.CLASSIC2,
                ProductModelWaterControl.SINGLE_WATER_CONTROL,
                ProductModelWaterControl.DUAL_WATER_CONTROL,
                ProductModelWaterControl.CLASSIC_PIPELINE,
                ProductModelWaterControl.SMART_PIPELINE,
            ) and (data.variant in (0, 1)):
                return ProductType.WATER_COMPUTER
            if (
                data.model == ProductModelWaterControl.IRRIGATION_VALVE
                and data.variant == 1
            ):
                return ProductType.VALVE
            if data.model == ProductModelWaterControl.AQUA_CONTOURS:
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
class CharacteristicPnpIdData:
    source_id: int
    vendor_id: int
    product_id: int
    product_version: int


@dataclass
class CharacteristicPnpId(Characteristic[CharacteristicPnpIdData]):
    @classmethod
    def decode(cls, data: bytes) -> CharacteristicPnpIdData:
        if len(data) != 7:
            raise ValueError(f"Invalid length of pnp data {data}")

        return CharacteristicPnpIdData(
            int.from_bytes(data[0:1], "little"),
            int.from_bytes(data[1:3], "little"),
            int.from_bytes(data[3:5], "little"),
            int.from_bytes(data[5:7], "little"),
        )

    @classmethod
    def encode(cls, value: CharacteristicPnpIdData) -> bytes:
        return (
            value.source_id.to_bytes(1, "little", signed=False)
            + value.vendor_id.to_bytes(2, "little", signed=False)
            + value.product_id.to_bytes(2, "little", signed=False)
            + value.product_version.to_bytes(2, "little", signed=False)
        )


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
class CharacteristicIntKeys(Characteristic[dict[int, str]]):
    @classmethod
    def decode(cls, data: bytes) -> dict[int, str]:
        res = {}
        for value in data.decode("ASCII", "replace").split(","):
            if "=" not in value:
                continue
            key, value = value.split("=", 1)
            if value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            res[int(key)] = value
        return res

    @classmethod
    def encode(cls, value: dict[int, str]) -> bytes:
        data = ",".join(f"{key}={value!r}" for key, value in value.items())
        return data.encode("ASCII")


@dataclass
class CharacteristicNullString(Characteristic[str]):
    @classmethod
    def decode(cls, data: bytes) -> str:
        return data.partition(b"\x00")[0].decode("latin-1", "replace")

    @classmethod
    def encode(cls, value: str) -> bytes:
        return value.encode("latin-1")


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
class CharacteristicIntArray(Characteristic[list[int]]):
    @classmethod
    def decode(cls, data: bytes) -> list[int]:
        return [
            int.from_bytes(data[i : i + 1], "little", signed=True)
            for i in range(0, len(data), 1)
        ]

    @classmethod
    def encode(cls, value: list[int]) -> bytes:
        return b"".join(v.to_bytes(1, "little", signed=True) for v in value)


@dataclass
class CharacteristicLongArray(Characteristic[list[int]]):
    @classmethod
    def decode(cls, data: bytes) -> list[int]:
        return [
            int.from_bytes(data[i : i + 4], "little", signed=True)
            for i in range(0, len(data), 4)
        ]


@dataclass
class CharacteristicUInt16Array(Characteristic[list[int]]):
    @classmethod
    def decode(cls, data: bytes) -> list[int]:
        return [
            int.from_bytes(data[i : i + 2], "little", signed=False)
            for i in range(0, len(data), 2)
        ]

    @classmethod
    def encode(cls, value: list[int]) -> bytes:
        return b"".join(v.to_bytes(2, "little", signed=False) for v in value)


@dataclass
class CharacteristicUInt16PairArray(Characteristic[list[tuple[int, int]]]):
    @classmethod
    def decode(cls, data: bytes) -> list[tuple[int, int]]:
        return [
            (
                int.from_bytes(data[i : i + 2], "little", signed=False),
                int.from_bytes(data[i + 2 : i + 4], "little", signed=False),
            )
            for i in range(0, len(data), 4)
        ]

    @classmethod
    def encode(cls, value: list[tuple[int, int]]) -> bytes:
        return b"".join(
            v[0].to_bytes(2, "little", signed=False)
            + v[1].to_bytes(2, "little", signed=False)
            for v in value
        )


@dataclass
class CharacteristicWeekdays(Characteristic[set[Day]]):
    @classmethod
    def decode(cls, data: bytes) -> set[Day]:
        value = int.from_bytes(data, "little", signed=False)
        return {Day(i) for i in range(8) if (value >> i) & 1}

    @classmethod
    def encode(cls, value: set[Day]) -> bytes:
        int_value = 0
        for day in value:
            int_value |= 1 << day.value
        return int_value.to_bytes(1, "little", signed=False)


class Contour(IntEnum):
    CONTOUR_1 = 0
    CONTOUR_2 = 1
    CONTOUR_3 = 2
    CONTOUR_4 = 3
    CONTOUR_5 = 4
    CONTOUR_6 = 5
    CONTOUR_7 = 6
    CONTOUR_8 = 7


@dataclass
class CharacteristicContours(Characteristic[set[Contour]]):
    @classmethod
    def decode(cls, data: bytes) -> set[Contour]:
        value = int.from_bytes(data, "little", signed=False)
        return {Contour(i) for i in range(8) if (value >> i) & 1}

    @classmethod
    def encode(cls, value: set[Contour]) -> bytes:
        int_value = 0
        for x in value:
            int_value |= 1 << x.value
        return int_value.to_bytes(1, "little", signed=False)


@dataclass
class CharacteristicTime(Characteristic[datetime]):
    @classmethod
    def decode(cls, data: bytes) -> datetime:
        value = int.from_bytes(data, "little")
        return datetime.fromtimestamp(value, timezone.utc).replace(tzinfo=None)

    @classmethod
    def encode(cls, value: datetime) -> bytes:
        return int(value.replace(tzinfo=timezone.utc).timestamp()).to_bytes(
            4, "little", signed=True
        )


@dataclass
class CharacteristicTimeOfDay(Characteristic[time]):
    @classmethod
    def decode(cls, data: bytes) -> time:
        value = int.from_bytes(data, "little")
        minutes, seconds = divmod(value, 60)
        hours, minutes = divmod(minutes, 60)
        return time(hours, minutes, seconds)

    @classmethod
    def encode(cls, value: time) -> bytes:
        return (
            timedelta(hours=value.hour, minutes=value.minute, seconds=value.second)
            .total_seconds()
            .to_bytes(4, "little", signed=True)
        )


@dataclass
class CharacteristicTimeDelta(Characteristic[timedelta]):
    @classmethod
    def decode(cls, data: bytes) -> timedelta:
        value = int.from_bytes(data, "little")
        return timedelta(seconds=value)

    @classmethod
    def encode(cls, value: timedelta) -> bytes:
        return value.total_seconds().to_bytes(4, "little", signed=True)


@dataclass
class CharacteristicTimeArray(Characteristic[list[datetime]]):
    @classmethod
    def decode(cls, data: bytes) -> list[datetime]:
        return [
            datetime.fromtimestamp(value, timezone.utc).replace(tzinfo=None)
            for value in CharacteristicLongArray.decode(data)
        ]


@dataclass
class CharacteristicIntEnum[T: IntEnum](CharacteristicInt):
    enum: type[T] = field(kw_only=True)

    def decode(self, data: bytes) -> T | int:
        raw = int.from_bytes(data, "little", signed=True)
        try:
            return self.enum(raw)
        except ValueError:
            return raw

    def encode(self, value: T | int) -> bytes:
        return value.to_bytes(1, "little", signed=True)


@dataclass
class ErrorData[T: IntEnum]:
    current_event_index: int
    total_events: int
    time_stamp: datetime
    error_code: T | int


@dataclass
class CharacteristicErrorData[T: IntEnum](Characteristic[ErrorData[T]]):
    enum: type[T] = field(kw_only=True)

    def decode(self, data: bytes) -> ErrorData[T]:
        error_code = int.from_bytes(data[6:7], "little")
        try:
            error_code = self.enum(error_code)
        except ValueError:
            pass

        return ErrorData(
            int.from_bytes(data[0:1], "little"),
            int.from_bytes(data[1:2], "little"),
            datetime.fromtimestamp(
                int.from_bytes(data[2:6], "little"), timezone.utc
            ).replace(tzinfo=None),
            error_code,
        )

    @classmethod
    def encode(cls, value: ErrorData[T]) -> bytes:
        return [
            *value.current_event_index.to_bytes(1, "little", signed=True),
            *value.total_events.to_bytes(1, "little", signed=True),
            *int(value.time_stamp.replace(tzinfo=timezone.utc).timestamp()).to_bytes(
                4, "little", signed=True
            ),
            *value.error_code.to_bytes(1, "little", signed=True),
        ]


@dataclass
class CharacteristicScheduleData:
    start_time: time
    duration: timedelta
    weekdays: set[Day]
    active: bool
    contours: set[Contour]


@dataclass
class CharacteristicSchedule(Characteristic[CharacteristicScheduleData]):
    @classmethod
    def decode(cls, data: bytes) -> CharacteristicScheduleData:
        return CharacteristicScheduleData(
            CharacteristicTimeOfDay.decode(data[0:4]),
            CharacteristicTimeDelta.decode(data[4:8]),
            CharacteristicWeekdays.decode(data[8:9]),
            CharacteristicBool.decode(data[9:10]),
            CharacteristicContours.decode(data[10:11]),
        )

    @classmethod
    def encode(cls, value: CharacteristicScheduleData) -> bytes:
        return (
            CharacteristicTimeOfDay.encode(value.start_time)
            + CharacteristicTimeDelta.encode(value.duration)
            + CharacteristicWeekdays.encode(value.weekdays)
            + CharacteristicBool.encode(value.active)
            + CharacteristicContours.encode(value.contours)
        )


class Service:
    unique_id: ClassVar[str]
    uuid: ClassVar[str]
    variant: ClassVar[str | None] = None
    products: ClassVar[set[ProductType]] = set(ProductType)
    registry: ClassVar[dict[str, list[type[Self]]]] = {}
    characteristics: ClassVar[dict[str, Characteristic]] = {}

    @classmethod
    def find_service(cls, uuid: str, product_type: ProductType) -> type[Self] | None:
        services = cls.registry.get(uuid, [])
        for service in services:
            if product_type in service.products:
                return service
        return None

    @classmethod
    def services_for_product_type(cls, product_type: ProductType) -> list[type[Self]]:
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


class ProductModelWaterControl(EnumOrInt):
    CLASSIC1 = 1
    CLASSIC2 = 0
    IRRIGATION_VALVE = 2
    SINGLE_WATER_CONTROL = 3
    DUAL_WATER_CONTROL = 4
    CLASSIC_PIPELINE = 5
    SMART_PIPELINE = 6
    AQUA_CONTOURS = 16


@dataclass
class ManufacturerData:
    company: ClassVar[int] = 0x0426
    pairable: bool | None = None
    serial: int | None = None
    group: int | ProductGroup | None = None
    model: int | ProductModelWaterControl = None
    variant: int | None = None
    name: str | None = None

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

    @property
    def product_type(self) -> ProductType:
        return ProductType.from_manufacturer_data(self)

    def update(self, data: bytes):
        value = ManufacturerData.decode_dict(data)
        info = dict(enumerate(value.get(6, b"")))

        if (data := info.get(0)) is not None:
            self.group = ProductGroup.enum_or_int(data)
        if (data := info.get(1)) is not None:
            if self.group == ProductGroup.WATER_CONTROL:
                self.model = ProductModelWaterControl.enum_or_int(data)
            else:
                self.model = data
        if (data := info.get(2)) is not None:
            self.variant = data

        if (data := value.get(4)) is not None:
            self.serial = int.from_bytes(data, "little")
        if (data := value.get(5)) is not None:
            self.pairable = bool.from_bytes(data, "little")
        if (data := value.get(8)) is not None:
            self.name = data.partition(b"\x00")[0].decode("utf-8", "replace")
