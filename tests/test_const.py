import pytest

from gardena_bluetooth.const import (
    AquaContourContours,
    AquaContourWatering,
    HybridValveActivationReason,
    Pump,
    Schedule,
    Schedule_1,
    Schedule_2,
    Schedule_3,
    Schedule_4,
    Schedule_5,
    Sensor,
    StandardBattery,
    Valve,
    Valve1,
    Valve2,
    ValveActivationReason,
    WateringHistory,
    WateringHistorySkipReason,
)
from gardena_bluetooth.parse import (
    ActivationReason,
    Characteristic,
    ProductType,
    Service,
)


@pytest.mark.parametrize(
    "schedule,base",
    [
        (Schedule_1, "1"),
        (Schedule_2, "2"),
        (Schedule_3, "3"),
        (Schedule_4, "4"),
        (Schedule_5, "5"),
    ],
)
def test_schedule(schedule: type[Schedule], base: str):
    assert schedule.uuid == f"98bd0c{base}0-0b0e-421a-84e5-ddbf75dc6de4"
    assert schedule.start_time.uuid == f"98bd0c{base}1-0b0e-421a-84e5-ddbf75dc6de4"
    assert schedule.duration.uuid == f"98bd0c{base}2-0b0e-421a-84e5-ddbf75dc6de4"
    assert schedule.weekdays.uuid == f"98bd0c{base}3-0b0e-421a-84e5-ddbf75dc6de4"
    assert schedule.valve_link.uuid == f"98bd0c{base}4-0b0e-421a-84e5-ddbf75dc6de4"
    assert schedule.active.uuid == f"98bd0c{base}5-0b0e-421a-84e5-ddbf75dc6de4"
    assert schedule.sensor_link.uuid == f"98bd0c{base}6-0b0e-421a-84e5-ddbf75dc6de4"


def test_standard_battery_level_status_uuid():
    assert (
        StandardBattery.battery_level_status.uuid
        == "00002bed-0000-1000-8000-00805f9b34fb"
    )


def test_id_uniqueness():
    """Ensure our id's are globally unique for services and characteristics."""
    ids: dict[str, Service | Characteristic] = {}
    for services in Service.registry.values():
        for service in services:
            assert ids.setdefault(service.unique_id, service) is service

            for char in service.characteristics.values():
                assert ids.setdefault(char.unique_id, char) is char


@pytest.mark.parametrize(
    "service",
    [service for services in Service.registry.values() for service in services],
)
def test_service_characteristics_not_shadowed(service: type[Service]) -> None:
    """Ensure no characteristic of a service is hidden by another with the same id."""
    declared = [
        value for value in vars(service).values() if isinstance(value, Characteristic)
    ]
    assert len(service.characteristics) == len(declared)


@pytest.mark.parametrize(
    "product_type",
    [
        ProductType.AQUA_CONTOURS,
        ProductType.WATER_COMPUTER,
        ProductType.VALVE,
    ],
)
def test_standard_battery_service_covers_water_control_family(
    product_type: ProductType,
) -> None:
    """Battery service resolves for all supported product types."""
    assert product_type in StandardBattery.products
    assert StandardBattery in Service.services_for_product_type(product_type)


def test_contour_points_share_transmit_uuid_but_have_distinct_query_index():
    points = [
        AquaContourContours.contour_points_1,
        AquaContourContours.contour_points_2,
        AquaContourContours.contour_points_3,
        AquaContourContours.contour_points_4,
        AquaContourContours.contour_points_5,
    ]

    assert all(
        char.uuid == AquaContourContours.contour_transmit.uuid for char in points
    )
    assert all(
        char.write_uuid == AquaContourContours.contour_receive.uuid for char in points
    )
    assert [char.query_index for char in points] == [1, 2, 3, 4, 5]
    assert len({char.unique_id for char in points}) == len(points)


def test_find_characteristics_returns_all_sharing_a_uuid():
    chars = AquaContourContours.find_characteristics(
        AquaContourContours.contour_transmit.uuid
    )

    assert AquaContourContours.contour_transmit in chars
    assert AquaContourContours.contour_points_1 in chars
    assert AquaContourContours.contour_points_5 in chars
    assert len(chars) == 6


@pytest.mark.parametrize(
    "product_type",
    [ProductType.PUMP, ProductType.PRESSURE_TANKS, ProductType.AUTOMATS],
)
def test_pump_service_for_pump_family(product_type: ProductType) -> None:
    assert Service.find_service(Pump.uuid, product_type) is Pump


@pytest.mark.parametrize(
    "product_type",
    [ProductType.WATER_COMPUTER, ProductType.VALVE, ProductType.AQUA_CONTOURS],
)
def test_pump_service_not_for_water_control_family(product_type: ProductType) -> None:
    """Service 0100 is device configuration on hybrid water controls."""
    assert Service.find_service(Pump.uuid, product_type) is None
    assert Pump not in Service.services_for_product_type(product_type)


@pytest.mark.parametrize(
    ("char", "raw", "expected"),
    [
        (Valve.activation_reason, b"\x00", ValveActivationReason.MANUAL),
        (Valve.activation_reason, b"\x01", ValveActivationReason.SCHEDULE),
        (
            Valve1.activation_reason,
            b"\x01",
            HybridValveActivationReason.PHYSICAL_BUTTON,
        ),
        (Valve1.activation_reason, b"\x03", HybridValveActivationReason.SCHEDULE),
        (Valve2.activation_reason, b"\x0a", HybridValveActivationReason.OTHER_SOURCES),
        (AquaContourWatering.activation_reason, b"\x02", ActivationReason.SCHEDULE),
        (AquaContourWatering.activation_reason, b"\x04", ActivationReason.SETUP),
    ],
)
def test_activation_reason(char, raw: bytes, expected) -> None:
    assert char.decode(raw) is expected


def test_watering_history_skip_reason() -> None:
    char = WateringHistory.skip_reason
    value = [
        WateringHistorySkipReason.NONE,
        WateringHistorySkipReason.SENSOR | WateringHistorySkipReason.BATTERY,
        WateringHistorySkipReason.TEMPERATURE,
    ]
    raw = char.encode(value)
    assert raw == b"\x00\x05\x80"
    assert char.decode(raw) == value


@pytest.mark.parametrize(
    ("raw", "minutes"),
    [(b"\x58\x02", 600), (b"\xc0\xa8", 43200), (b"\xff\xff", 65535)],
)
def test_aqua_contour_watering_pause(raw: bytes, minutes: int) -> None:
    char = AquaContourWatering.watering_pause
    assert char.decode(raw) == minutes
    assert char.encode(minutes) == raw


@pytest.mark.parametrize(
    ("char", "raw", "service_id"),
    [
        (Schedule_1.valve_link, b"\x10\x0f", 0x0F10),
        (Schedule_1.valve_link, b"\x00\x00", 0),
        (Schedule_1.sensor_link, b"\x10\x00", 0x0010),
        (Schedule_1.sensor_link, b"\x00\x00", 0),
    ],
)
def test_schedule_links(char, raw: bytes, service_id: int) -> None:
    assert char.decode(raw) == service_id
    assert char.encode(service_id) == raw


@pytest.mark.parametrize(
    ("raw", "value"),
    [(b"\x00" * 10, ""), (b"abc\x00\x00\x00", "abc")],
)
def test_sensor_type(raw: bytes, value: str) -> None:
    assert Sensor.type.decode(raw) == value


@pytest.mark.parametrize(
    ("raw", "hours"),
    [(b"\x00\x00", 0), (b"\x18\x00", 24), (b"\xc8\x00", 200), (b"\xff\x00", 255)],
)
def test_pump_filter_reminder(raw: bytes, hours: int) -> None:
    assert Pump.filter_reminder.decode(raw) == hours
    assert Pump.filter_reminder.encode(hours) == raw
