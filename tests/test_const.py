import pytest

from gardena_bluetooth.const import (
    AquaContourContours,
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
