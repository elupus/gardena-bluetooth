import pytest

from gardena_bluetooth.const import (
    Schedule,
    Schedule_1,
    Schedule_2,
    Schedule_3,
    Schedule_4,
    Schedule_5,
    StandardBattery,
)
from gardena_bluetooth.parse import Characteristic, ProductType, Service


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
