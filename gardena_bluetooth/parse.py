from typing import ClassVar, TypeVar, Generic
from dataclasses import dataclass
from datetime import datetime
from bleak import BleakClient
from .exceptions import CharacteristicNoAccess, CharacteristicNotFound

def pretty_name(name: str):
    data = name.split("_")
    return " ".join(f"{part[0].upper()}{part[1:]}" for part in data)


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
    def encode(data: bool) -> bytes:
        if data:
            return b"\x01"
        return b"\x00"


@dataclass
class CharacteristicString(Characteristic[str]):
    @classmethod
    def decode(cls, data: bytes) -> str:
        return data.decode("ASCII")

    @classmethod
    def encode(cls, value: str) -> bytes:
        return value.encode("ASCII")


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
        return [int.from_bytes(data[i : i + 4]) for i in range(0, len(data), 4)]


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


async def read_characteristic(
    client: BleakClient, char: Characteristic[CharacteristicType]
) -> CharacteristicType:
    """Read data to from a characteristic."""
    characteristic = client.services.get_characteristic(char.uuid)
    if characteristic is None:
        raise CharacteristicNotFound(f"Unable to find characteristic {char.uuid}")
    if "read" not in characteristic.properties:
        raise CharacteristicNoAccess(f"Characteristic {char.uuid} is not writable")
    data = await client.read_gatt_char(characteristic)
    return char.decode(data)


async def write_characteristic(
    client: BleakClient,
    char: Characteristic[CharacteristicType],
    value: CharacteristicType,
    response=False,
) -> None:
    """Write data to a characteristic."""
    characteristic = client.services.get_characteristic(char.uuid)
    if characteristic is None:
        raise CharacteristicNotFound(f"Unable to find characteristic {char.uuid}")
    if "write" not in characteristic.properties:
        raise CharacteristicNoAccess(f"Characteristic {char.uuid} is not writable")
    data = char.encode(value)
    await client.write_gatt_char(characteristic, data, response=response)
