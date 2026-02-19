from gardena_bluetooth.const import (
    Schedule_1,
    Schedule,
    Schedule_2,
    Schedule_3,
    Schedule_4,
    Schedule_5,
)
import pytest


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
