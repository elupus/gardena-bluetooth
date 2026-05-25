import pytest

from gardena_bluetooth.const import (
    WATERING_COMMAND_SOURCE,
    Schedule,
    Schedule_1,
    Schedule_2,
    Schedule_3,
    Schedule_4,
    Schedule_5,
    Valve1,
    Valve2,
    ValveX,
    start_watering_payload,
    stop_watering_payload,
)
from gardena_bluetooth.parse import Characteristic, CharacteristicIntKeys, Service


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


def test_id_uniqueness():
    """Ensure our id's are globally unique for services and characteristics."""
    ids: dict[str, Service | Characteristic] = {}
    for services in Service.registry.values():
        for service in services:
            assert ids.setdefault(service.unique_id, service) is service

            for char in service.characteristics.values():
                assert ids.setdefault(char.unique_id, char) is char


def test_watering_command_source():
    """WATERING_COMMAND_SOURCE matches gardena-smart-local-api COMMAND_SOURCE."""
    assert WATERING_COMMAND_SOURCE == "18"


@pytest.mark.parametrize("service", [Valve1, Valve2])
def test_valvex_start_stop_are_int_keys(service: type[ValveX]):
    """start/stop_watering must be CharacteristicIntKeys (not String).

    The Valve1/Valve2 family expects the LWM2M Execute serialisation
    `0='<source>',1='<duration>'` — CharacteristicIntKeys is the codec
    for that.
    """
    assert isinstance(service.start_watering, CharacteristicIntKeys)
    assert isinstance(service.stop_watering, CharacteristicIntKeys)


def test_start_watering_payload_helper():
    """start_watering_payload builds the correct dict and encodes to expected bytes."""
    payload = start_watering_payload(30)
    assert payload == {0: "18", 1: "30"}
    assert Valve1.start_watering.encode(payload) == b"0='18',1='30'"


def test_stop_watering_payload_helper():
    """stop_watering_payload builds the correct dict and encodes to expected bytes."""
    payload = stop_watering_payload()
    assert payload == {0: "18"}
    assert Valve1.stop_watering.encode(payload) == b"0='18'"
