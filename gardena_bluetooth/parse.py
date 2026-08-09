import logging
from abc import ABC
from calendar import Day
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta, timezone
from enum import Enum, IntEnum, IntFlag, auto
from typing import ClassVar, Generic, Self, TypeVar

LOGGER = logging.getLogger(__name__)
CharacteristicType = TypeVar("CharacteristicType")


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


class EnumOrInt(IntEnum):
    @classmethod
    def enum_or_int(cls, value: int) -> Self | int:
        try:
            return cls(value)
        except ValueError:
            return value

    @classmethod
    def decode(cls, data: bytes) -> Self | int:
        raw = int.from_bytes(data, "little", signed=True)
        return cls.enum_or_int(raw)

    @classmethod
    def encode(cls, value: Self | int) -> bytes:
        return value.to_bytes(1, "little", signed=True)


class SkipReason(EnumOrInt):
    NONE = 0
    RAIN_PAUSE = 1
    HUMIDITY_SENSOR = 2
    RAIN_SENSOR = 3
    WATERING_ALREADY_ACTIVE = 4
    BATTERY_EMPTY = 5
    OTHER_SCHEDULE_WITH_SAME_START_TIME = 6
    CONTOUR_NOT_ACTIVE = 7
    CONTOUR_NOT_ENABLED_FOR_POSITION = 8
    CONTOUR_DATA_INVALID = 9
    POSITION_CHANGED = 10
    CHARGING_CABLE_PLUGGED = 11
    MANUAL_MODE = 12
    NO_WATER = 14
    VALVE_MOTOR_ERROR = 15
    SPRINKLER_MOTOR_ERROR = 16
    ROTATION_SENSOR_ERROR = 17
    OPERATIONAL_MODE_CHANGED = 18
    IRRIGATION_CONTROL_CHANGED = 19


class SMPGroup(EnumOrInt):
    OS = 0
    IMAGE = 1
    STATISTICS = 2
    SETTINGS = 3
    LOG = 4
    RUN_TEST = 5
    SPLIT_IMAGE = 6
    CRASH = 7
    FILE = 8
    SHELL = 9
    ZEPHYR = 63
    APPLICATION_BASE = 64


class SMPOperation(EnumOrInt):
    READ = 0
    READ_RSP = 1
    WRITE = 2
    WRITE_RSP = 3
    ERASE = 4
    ERASE_RSP = 5
    SHA256 = 6
    SHA256_RSP = 7
    UPLOAD = 8
    UPLOAD_RSP = 9
    FILE = 10
    FILE_RSP = 11


class ActivationReason(EnumOrInt):
    NONE = 0
    MANUAL = 1
    SCHEDULE = 2
    EXTERNAL = 3
    SETUP = 4


class WateringSource(EnumOrInt):
    MOBILE_APP = 10
    CLOUD = 18


@dataclass
class CharacteristicSMPData:
    res: int
    ver: int
    op: SMPOperation | int
    flags: int
    group: SMPGroup | int
    sequence_num: int
    command_id: int
    payload: bytes = b""

    @property
    def data_length(self) -> int:
        return len(self.payload)

    @classmethod
    def decode(cls, data: bytes) -> "CharacteristicSMPData":
        if len(data) < 7:
            raise ValueError(f"Invalid SMP frame length {len(data)}")

        header = data[0]
        res = (header >> 6) & 0x03
        ver = (header >> 4) & 0x03
        op = SMPOperation.enum_or_int(header & 0x0F)
        flags = data[1]
        data_length = int.from_bytes(data[2:4], "big")
        group = SMPGroup.enum_or_int(data[4])
        sequence_num = data[5]
        command_id = data[6]
        payload = data[7 : 7 + data_length]

        return cls(
            res=res,
            ver=ver,
            op=op,
            flags=flags,
            group=group,
            sequence_num=sequence_num,
            command_id=command_id,
            payload=payload,
        )

    @classmethod
    def encode(cls, value: "CharacteristicSMPData") -> bytes:
        header = (
            ((value.res & 0x03) << 6)
            | ((value.ver & 0x03) << 4)
            | (int(value.op) & 0x0F)
        )
        return (
            bytes([header, value.flags])
            + value.data_length.to_bytes(2, "big")
            + bytes([int(value.group), value.sequence_num, value.command_id])
            + value.payload
        )


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
class CharacteristicIgnore(Characteristic[None]):
    @classmethod
    def decode(cls, data: bytes) -> None:
        return None

    @classmethod
    def encode(cls, value: None) -> bytes:
        return b""


@dataclass
class CharacteristicBytes(Characteristic[bytes]):
    @classmethod
    def decode(cls, data: bytes) -> bytes:
        return data

    @classmethod
    def encode(cls, value: bytes) -> bytes:
        return value


@dataclass
class CharacteristicSMP(Characteristic[CharacteristicSMPData]):
    @classmethod
    def decode(cls, data: bytes) -> CharacteristicSMPData:
        return CharacteristicSMPData.decode(data)

    @classmethod
    def encode(cls, value: CharacteristicSMPData) -> bytes:
        return CharacteristicSMPData.encode(value)


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
        data = ",".join(f"{key}='{value}'" for key, value in value.items())
        return data.encode("ASCII")


@dataclass
class CharacteristicStartStopWatering(
    Characteristic[tuple[WateringSource | int, timedelta | None]]
):
    @classmethod
    def decode(cls, data: bytes) -> tuple[WateringSource | int, timedelta | None]:
        value = CharacteristicIntKeys.decode(data)
        source = WateringSource.enum_or_int(int(value[0]))
        duration = value.get(1)
        if duration is not None:
            duration = timedelta(seconds=int(duration))
        return source, duration

    @classmethod
    def encode(cls, value: tuple[WateringSource | int, timedelta | None]) -> bytes:
        data = {0: str(int(value[0]))}
        if value[1] is not None:
            data[1] = str(int(value[1].total_seconds()))
        return CharacteristicIntKeys.encode(data)


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
class PositionContourMaskEntry:
    position: int
    """1-indexed position (1-5)."""
    assigned_contours: set[Contour]
    """Contours available to this position - a position can have several."""
    is_segmented_watering: bool
    is_externally_managed: bool
    is_automatic_mode: bool


PositionContourMask = list[PositionContourMaskEntry]
"""One entry per position, in position order (1-5)."""


@dataclass
class CharacteristicPositionContourMask(Characteristic[PositionContourMask]):
    @classmethod
    def decode(cls, data: bytes) -> PositionContourMask:
        return [
            PositionContourMaskEntry(
                position=i + 1,
                assigned_contours={Contour(c) for c in range(5) if b & (1 << c)},
                is_segmented_watering=bool(b & 0x20),
                is_externally_managed=bool(b & 0x40),
                is_automatic_mode=bool(b & 0x80),
            )
            for i, b in enumerate(data)
        ]

    @classmethod
    def encode(cls, value: PositionContourMask) -> bytes:
        result = bytearray(5)
        for entry in value:
            b = 0
            for contour in entry.assigned_contours:
                b |= 1 << int(contour)
            b |= int(entry.is_segmented_watering) << 5
            b |= int(entry.is_externally_managed) << 6
            b |= int(entry.is_automatic_mode) << 7
            result[entry.position - 1] = b
        return bytes(result)


class SegmentCommand(EnumOrInt):
    FIRST = 0
    NEXT = 1
    ACK = 2
    QUERY = 3


@dataclass
class Segment:
    """A single frame of a multi-frame segmented characteristic transfer.

    This is the generic frame envelope (command, resource index, frames
    remaining) - the payload itself is opaque here. Reassemble frames with
    `SegmentAssembler` and parse the completed payload with a data-specific
    parser.
    """

    cmd: SegmentCommand | int
    index: int
    frames_left: int
    """1-indexed count of frames remaining, inclusive - 1 marks the final frame."""
    payload: bytes

    @classmethod
    def decode(cls, data: bytes) -> "Segment":
        header = data[0]
        cmd = SegmentCommand.enum_or_int(header // 32)
        index = header % 32
        frames_left = data[1]
        return cls(cmd=cmd, index=index, frames_left=frames_left, payload=data[2:])


@dataclass
class SegmentQuery:
    """A request for a segmented resource, addressed by index.

    Write the encoded result to the requesting characteristic, having
    subscribed to notifications on it beforehand to receive the response.
    """

    index: int

    def encode(self) -> bytes:
        return bytes([(int(SegmentCommand.QUERY) << 5) | self.index])

    @classmethod
    def decode(cls, data: bytes) -> "SegmentQuery":
        return cls(index=data[0] % 32)


@dataclass
class SegmentAck:
    """An acknowledgement for a segmented transfer, addressed by index.

    Write it back to the requesting characteristic once the final response
    frame (`frames_left == 1`) has been received.
    """

    index: int

    def encode(self) -> bytes:
        return bytes([(int(SegmentCommand.ACK) << 5) | self.index])

    @classmethod
    def decode(cls, data: bytes) -> "SegmentAck":
        return cls(index=data[0] % 32)


@dataclass
class SegmentAssembler:
    """Reassembles a stream of Segment notifications into a full payload.

    Frames for an index other than the one being assembled are ignored, to
    tolerate stray notifications from an unrelated in-flight request. The
    first frame is expected to carry `SegmentCommand.FIRST` and subsequent
    frames `SegmentCommand.NEXT`; a frame that breaks this order aborts the
    transfer, discarding whatever was accumulated so far. Frames received
    after completion are rejected.
    """

    index: int
    payload: bytes = b""
    done: bool = False
    started: bool = False

    def add_frame(self, frame: Segment) -> bool:
        """Merge a frame's payload, return True once the transfer is complete."""
        if self.done:
            LOGGER.debug("Rejecting frame for segment %s, already complete", self.index)
            return self.done
        if frame.index != self.index:
            LOGGER.debug(
                "Ignoring frame for segment %s, expected %s", frame.index, self.index
            )
            return self.done

        expected_cmd = SegmentCommand.NEXT if self.started else SegmentCommand.FIRST
        if frame.cmd != expected_cmd:
            LOGGER.warning(
                "Unexpected command %s for segment %s, expected %s, aborting",
                frame.cmd,
                self.index,
                expected_cmd,
            )
            self.payload = b""
            self.done = True
            return self.done
        self.started = True

        self.payload += frame.payload
        if frame.frames_left == 1:
            self.done = True
        return self.done


@dataclass
class CharacteristicSegmented(Characteristic[CharacteristicType]):
    """A characteristic whose value is transferred via a multi-frame segmented read.

    The transfer uses two distinct characteristics: `uuid` (inherited) is
    the receiving side - subscribed to for the notified response frames -
    while `write_uuid` is the separate characteristic the request is
    written to. `query_index` addresses which segmented resource to
    request, and is folded into `unique_id` so that multiple indexed
    resources sharing a UUID/variant remain distinguishable.
    """

    write_uuid: str = field(kw_only=True)
    query_index: int = field(kw_only=True)

    def __post_init__(self):
        super().__post_init__()
        object.__setattr__(
            self, "unique_id", f"{self.unique_id}:segment{self.query_index}"
        )


@dataclass
class ContourPoint:
    angle: int
    """Angle in degrees (0-359)."""
    distance: int
    """Distance in cm."""


ContourPoints = list[ContourPoint]
"""A contour's curve, as points in the order they were received."""


@dataclass
class CharacteristicContourPoints(CharacteristicSegmented[ContourPoints]):
    @classmethod
    def decode(cls, data: bytes) -> ContourPoints:
        points: ContourPoints = []
        for i in range(0, len(data) - 1, 2):
            angle_byte, distance_byte = data[i], data[i + 1]
            if angle_byte == 0 and distance_byte == 0:
                continue
            angle = (angle_byte << 1) | (distance_byte >> 7)
            distance = (distance_byte & 0x7F) * 10
            points.append(ContourPoint(angle, distance))
        return points


@dataclass
class CharacteristicTime(Characteristic[datetime]):
    @classmethod
    def decode(cls, data: bytes) -> datetime:
        value = int.from_bytes(data, "little")
        try:
            return datetime.fromtimestamp(value, timezone.utc).replace(tzinfo=None)
        except OverflowError as exc:
            raise ValueError(f"Invalid timestamp {value}") from exc

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
    index: int
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
            *value.index.to_bytes(1, "little", signed=True),
            *value.total_events.to_bytes(1, "little", signed=True),
            *int(value.time_stamp.replace(tzinfo=timezone.utc).timestamp()).to_bytes(
                4, "little", signed=True
            ),
            *value.error_code.to_bytes(1, "little", signed=True),
        ]


class PowerSourceConnected(EnumOrInt):
    NOT_CONNECTED = 0
    CONNECTED = 1
    UNKNOWN = 2


class BatteryChargeState(EnumOrInt):
    UNKNOWN = 0
    CHARGING = 1
    DISCHARGING_ACTIVE = 2
    DISCHARGING_INACTIVE = 3


class BatteryChargeLevel(EnumOrInt):
    UNKNOWN = 0
    GOOD = 1
    LOW = 2
    CRITICAL = 3


class BatteryChargingType(EnumOrInt):
    UNKNOWN = 0
    CONSTANT_CURRENT = 1
    CONSTANT_VOLTAGE = 2
    TRICKLE = 3
    FLOAT = 4


class BatteryChargingFaultReason(IntFlag):
    NONE = 0
    BATTERY = 1 << 0
    EXTERNAL_POWER_SOURCE = 1 << 1
    OTHER = 1 << 2


class BatteryServiceRequired(EnumOrInt):
    NOT_REQUIRED = 0
    REQUIRED = 1
    UNKNOWN = 2


@dataclass
class CharacteristicBatteryLevelStatusData:
    battery_present: bool
    wired_external_power_source_connected: PowerSourceConnected | int
    wireless_external_power_source_connected: PowerSourceConnected | int
    battery_charge_state: BatteryChargeState | int
    battery_charge_level: BatteryChargeLevel | int
    battery_charging_type: BatteryChargingType | int
    battery_charging_fault_reason: BatteryChargingFaultReason
    identifier: int | None = None
    battery_level: int | None = None
    service_required: BatteryServiceRequired | int | None = None
    battery_fault: bool | None = None


@dataclass
class CharacteristicBatteryLevelStatus(
    Characteristic[CharacteristicBatteryLevelStatusData]
):
    @classmethod
    def decode(cls, data: bytes) -> CharacteristicBatteryLevelStatusData:
        flags = data[0]
        power_state = int.from_bytes(data[1:3], "little", signed=False)
        offset = 3

        identifier = None
        if flags & 0x01:
            identifier = int.from_bytes(
                data[offset : offset + 2], "little", signed=False
            )
            offset += 2

        battery_level = None
        if flags & 0x02:
            battery_level = data[offset]
            offset += 1

        service_required = None
        battery_fault = None
        if flags & 0x04:
            additional_status = data[offset]
            service_required = BatteryServiceRequired.enum_or_int(
                additional_status & 0x03
            )
            battery_fault = bool((additional_status >> 2) & 0x01)
            offset += 1

        return CharacteristicBatteryLevelStatusData(
            battery_present=bool(power_state & 0x01),
            wired_external_power_source_connected=PowerSourceConnected.enum_or_int(
                (power_state >> 1) & 0x03
            ),
            wireless_external_power_source_connected=PowerSourceConnected.enum_or_int(
                (power_state >> 3) & 0x03
            ),
            battery_charge_state=BatteryChargeState.enum_or_int(
                (power_state >> 5) & 0x03
            ),
            battery_charge_level=BatteryChargeLevel.enum_or_int(
                (power_state >> 7) & 0x03
            ),
            battery_charging_type=BatteryChargingType.enum_or_int(
                (power_state >> 9) & 0x07
            ),
            battery_charging_fault_reason=BatteryChargingFaultReason(
                (power_state >> 12) & 0x07
            ),
            identifier=identifier,
            battery_level=battery_level,
            service_required=service_required,
            battery_fault=battery_fault,
        )

    @classmethod
    def encode(cls, value: CharacteristicBatteryLevelStatusData) -> bytes:
        power_state = (
            (int(value.battery_present) & 0x01)
            | ((int(value.wired_external_power_source_connected) & 0x03) << 1)
            | ((int(value.wireless_external_power_source_connected) & 0x03) << 3)
            | ((int(value.battery_charge_state) & 0x03) << 5)
            | ((int(value.battery_charge_level) & 0x03) << 7)
            | ((int(value.battery_charging_type) & 0x07) << 9)
            | ((int(value.battery_charging_fault_reason) & 0x07) << 12)
        )

        flags = 0
        tail = b""
        if value.identifier is not None:
            flags |= 0x01
            tail += value.identifier.to_bytes(2, "little", signed=False)
        if value.battery_level is not None:
            flags |= 0x02
            tail += bytes([value.battery_level])
        if value.service_required is not None or value.battery_fault is not None:
            flags |= 0x04
            additional_status = (int(value.service_required or 0) & 0x03) | (
                (int(bool(value.battery_fault)) & 0x01) << 2
            )
            tail += bytes([additional_status])

        return bytes([flags]) + power_state.to_bytes(2, "little", signed=False) + tail


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

    @classmethod
    def find_characteristics(cls, uuid: str) -> list[Characteristic]:
        """Get all characteristics declared for a given physical UUID.

        Usually a single match, but a UUID can be shared by several logical
        characteristics (e.g. segmented reads multiplexed over one UUID).
        """
        return [char for char in cls.characteristics.values() if char.uuid == uuid]

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
                cls.characteristics[value.unique_id] = value


@dataclass
class CharacteristicEventHistoryData:
    index: int
    total_events: int
    timestamp: datetime
    schedule_index: int
    skip_reason: SkipReason
    duration: timedelta

    @classmethod
    def decode(cls, data: bytes) -> Self:
        return CharacteristicEventHistoryData(
            CharacteristicInt.decode(data[0:1]),
            CharacteristicInt.decode(data[1:2]),
            CharacteristicTime.decode(data[2:6]),
            CharacteristicInt.decode(data[6:7]),
            SkipReason.decode(data[7:8]),
            CharacteristicTimeDelta.decode(data[8:12]),
        )

    @classmethod
    def encode(cls, value: Self) -> bytes:
        return (
            CharacteristicInt.encode(value.index)
            + CharacteristicInt.encode(value.total_events)
            + CharacteristicTime.encode(value.timestamp)
            + CharacteristicInt.encode(value.schedule_index)
            + SkipReason.encode(value.skip_reason)
            + CharacteristicTimeDelta.encode(value.duration)
        )


class CharacteristicEventHistory(Characteristic[CharacteristicEventHistoryData]):
    @classmethod
    def decode(cls, data: bytes) -> CharacteristicEventHistoryData:
        return CharacteristicEventHistoryData.decode(data)

    @classmethod
    def encode(cls, value: CharacteristicEventHistoryData) -> bytes:
        return CharacteristicEventHistoryData.encode(value)


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
