from datetime import datetime, timedelta
from enum import IntEnum

import pytest

from gardena_bluetooth.parse import (
    BatteryChargeLevel,
    BatteryChargeState,
    BatteryChargingFaultReason,
    BatteryChargingType,
    BatteryServiceRequired,
    CharacteristicBatteryLevelStatus,
    CharacteristicBatteryLevelStatusData,
    CharacteristicErrorData,
    CharacteristicIntEnum,
    CharacteristicIntKeys,
    CharacteristicNullString,
    CharacteristicNullStringUf8,
    CharacteristicSMPData,
    CharacteristicStartStopWatering,
    CharacteristicString,
    ManufacturerData,
    PowerSourceConnected,
    ProductGroup,
    ProductType,
    WateringSource,
)


@pytest.mark.parametrize(
    ("raw", "manufacturer_data", "product_type"),
    [
        (
            b"\x02\x07d\x02\x05\x01\x02\x08\x00\x02\t\x01\x04\x06\x12\x00\x01",
            ManufacturerData(
                pairable=True,
                serial=None,
                group=ProductGroup.WATER_CONTROL,
                model=0,
                variant=1,
                name="",
            ),
            ProductType.WATER_COMPUTER,
        ),
        (
            (
                b"\x02\x07d\x02\x05\x01\x02\x08\x00\x02"
                b"\t\x01\x04\x06\x20\x00\x01\x05\x04\x01\x02\x03\x04"
            ),
            ManufacturerData(
                pairable=True, serial=0x04030201, group=32, model=0, variant=1, name=""
            ),
            ProductType.UNKNOWN,
        ),
        (
            (
                b"\x05\x04\x14\x18\x00\x00\x02\x05\x01\x04\x06\x11\x02\x02"
                b"\t\x01\x04\x06\x20\x00\x01\x05\x04\x01\x02\x03\x04"
            ),
            ManufacturerData(pairable=True, serial=6164, group=17, model=2, variant=2),
            ProductType.PRESSURE_TANKS,
        ),
        (
            (b"\x04\x06\x12\x04\x00\x03\x05\x00\x00\x05\x04\xfd3\x00\x00"),
            ManufacturerData(
                pairable=False,
                serial=13309,
                group=ProductGroup.WATER_CONTROL,
                model=4,
                variant=0,
            ),
            ProductType.WATER_COMPUTER,
        ),
    ],
)
def test_manufacturer_data(raw, manufacturer_data, product_type):
    data = ManufacturerData.decode(raw)
    assert data == manufacturer_data
    assert ProductType.from_manufacturer_data(data) == product_type


def test_parse_manufacturer_data_segmented():
    """Test segmented manufacturer data."""

    data = ManufacturerData()
    raw = bytes.fromhex("0205000406121001")
    data.update(raw)

    assert data == ManufacturerData(
        pairable=False,
        group=ProductGroup.WATER_CONTROL,
        model=16,
        variant=1,
    )

    raw = bytes.fromhex("0504f162c103")
    data.update(raw)

    assert data == ManufacturerData(
        pairable=False,
        serial=63005425,
        group=ProductGroup.WATER_CONTROL,
        model=16,
        variant=1,
    )
    assert ProductType.from_manufacturer_data(data) is ProductType.AQUA_CONTOURS


def test_string_firmware_invalid():
    raw = b"abc\xe4"
    data = CharacteristicString.decode(raw)
    assert data == "abc�"


def test_string_nulled_utf8():
    raw = "åäö".encode("utf-8") + b"\x00junk"
    data = CharacteristicNullStringUf8.decode(raw)
    assert data == "åäö"


def test_string_nulled():
    raw = b"abc\x00junk"
    data = CharacteristicNullString.decode(raw)
    assert data == "abc"


def test_smp_data_encode_decode():
    data = CharacteristicSMPData(
        res=0,
        ver=1,
        op=2,
        flags=0,
        group=63,
        sequence_num=7,
        command_id=4,
        payload=b"hello",
    )
    encoded = CharacteristicSMPData.encode(data)
    decoded = CharacteristicSMPData.decode(encoded)

    assert decoded == data
    assert decoded.data_length == 5
    assert decoded.payload == b"hello"


def test_enum():
    class Values(IntEnum):
        A = 0
        B = 2

    char = CharacteristicIntEnum("", enum=Values)
    raw = b"\x00"
    data = char.decode(raw)
    assert data is Values.A
    raw = b"\x01"
    data = char.decode(raw)
    assert data == 1
    assert char.encode(Values.B) == b"\x02"


def test_error_code():
    class Errors(IntEnum):
        A = 0
        B = 1
        C = 2

    char = CharacteristicErrorData("", enum=Errors)
    data = char.decode(b"\x01\x01\xc3,\xafi\x01")
    assert data.error_code is Errors.B
    assert data.time_stamp == datetime(2026, 3, 9, 20, 25, 39)
    assert data.index == 1
    assert data.total_events == 1


def test_int_keys():
    char = CharacteristicIntKeys("")
    raw = char.encode({0: "10", 1: "20"})
    assert raw == b"0='10',1='20'"
    data = char.decode(raw)
    assert data == {0: "10", 1: "20"}


def test_int_enum():
    class Values(IntEnum):
        A = 0
        B = 1
        C = 2

    char = CharacteristicIntEnum("", enum=Values)
    raw = char.encode(Values.A)
    assert raw == b"\x00"
    data = char.decode(raw)
    assert data is Values.A


def test_watering_start():
    char = CharacteristicStartStopWatering("")
    value = (WateringSource.MOBILE_APP, timedelta(minutes=60))
    raw = char.encode(value)
    assert raw == b"0='10',1='3600'"
    data = char.decode(raw)
    assert data == value


def test_battery_level_status_full():
    char = CharacteristicBatteryLevelStatus("")
    value = CharacteristicBatteryLevelStatusData(
        battery_present=True,
        wired_external_power_source_connected=PowerSourceConnected.CONNECTED,
        wireless_external_power_source_connected=PowerSourceConnected.NOT_CONNECTED,
        battery_charge_state=BatteryChargeState.CHARGING,
        battery_charge_level=BatteryChargeLevel.GOOD,
        battery_charging_type=BatteryChargingType.CONSTANT_CURRENT,
        battery_charging_fault_reason=BatteryChargingFaultReason.NONE,
        identifier=42,
        battery_level=77,
        service_required=BatteryServiceRequired.NOT_REQUIRED,
        battery_fault=False,
    )
    raw = char.encode(value)
    assert raw == b"\x07\xa3\x02\x2a\x00\x4d\x00"
    data = char.decode(raw)
    assert data == value


def test_battery_level_status_minimal_with_fault_flags():
    char = CharacteristicBatteryLevelStatus("")
    value = CharacteristicBatteryLevelStatusData(
        battery_present=False,
        wired_external_power_source_connected=PowerSourceConnected.UNKNOWN,
        wireless_external_power_source_connected=PowerSourceConnected.UNKNOWN,
        battery_charge_state=BatteryChargeState.UNKNOWN,
        battery_charge_level=BatteryChargeLevel.UNKNOWN,
        battery_charging_type=BatteryChargingType.UNKNOWN,
        battery_charging_fault_reason=(
            BatteryChargingFaultReason.BATTERY | BatteryChargingFaultReason.OTHER
        ),
    )
    raw = char.encode(value)
    assert raw == b"\x00\x14\x50"
    data = char.decode(raw)
    assert data == value


def test_watering_stop():
    char = CharacteristicStartStopWatering("")
    value = (WateringSource.MOBILE_APP, None)
    raw = char.encode(value)
    assert raw == b"0='10'"
    data = char.decode(raw)
    assert data == value
