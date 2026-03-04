from abc import ABC
from .parse import (
    CharacteristicBool,
    CharacteristicWeekday,
    CharacteristicBytes,
    CharacteristicInt,
    CharacteristicLong,
    CharacteristicLongArray,
    CharacteristicString,
    CharacteristicTime,
    CharacteristicNullString,
    CharacteristicNullStringUf8,
    CharacteristicTimeArray,
    CharacteristicUInt16,
    Service,
    ProductType,
)

PRODUCT_NAMES = {
    ProductType.PUMP: "Gardena Garden Pump",
    ProductType.WATER_COMPUTER: "Gardena Water Computer",
    ProductType.VALVE: "Gardena Irrigation Valve",
    ProductType.MOWER: "Gardena Mower",
    ProductType.AQUA_CONTOURS: "Gardena Aqua Precise",
    ProductType.AUTOMATS: "Gardena Automats",
    ProductType.PRESSURE_TANKS: "Gardena Pressure Tanks",
    ProductType.UNKNOWN: "Gardena Unknown Product",
}

ScanService = "98bd0001-0b0e-421a-84e5-ddbf75dc6de4"
FotaService = "0000ffc0-0000-1000-8000-00805f9b34fb"


class Scan(Service):
    uuid = "98bd0001-0b0e-421a-84e5-ddbf75dc6de4"

    write_characteristic = CharacteristicBytes("98bd0002-0b0e-421a-84e5-ddbf75dc6de4")
    read_characteristic = CharacteristicBytes("98bd0003-0b0e-421a-84e5-ddbf75dc6de4")
    read_protocol_descriptor = CharacteristicNullString(
        "98bd0004-0b0e-421a-84e5-ddbf75dc6de4"
    )


class Valve(Service):
    uuid = "98bd0f10-0b0e-421a-84e5-ddbf75dc6de4"

    state = CharacteristicBool("98bd0f11-0b0e-421a-84e5-ddbf75dc6de4")
    connected_state = CharacteristicBool("98bd0f12-0b0e-421a-84e5-ddbf75dc6de4")
    remaining_open_time = CharacteristicLong("98bd0f13-0b0e-421a-84e5-ddbf75dc6de4")
    manual_watering_time = CharacteristicLong("98bd0f14-0b0e-421a-84e5-ddbf75dc6de4")
    activation_reason = CharacteristicInt("98bd0f15-0b0e-421a-84e5-ddbf75dc6de4")


class DeviceConfiguration(Service):
    uuid = "98bd0b10-0b0e-421a-84e5-ddbf75dc6de4"
    products = set(ProductType) - {ProductType.AQUA_CONTOURS}

    rain_pause = CharacteristicLong("98bd0b11-0b0e-421a-84e5-ddbf75dc6de4")
    seasonal_adjust = CharacteristicInt("98bd0b12-0b0e-421a-84e5-ddbf75dc6de4")
    unix_timestamp = CharacteristicTime("98bd0b13-0b0e-421a-84e5-ddbf75dc6de4")
    mobile_device_name = CharacteristicInt("98bd0b14-0b0e-421a-84e5-ddbf75dc6de4")
    device_language = CharacteristicInt("98bd0b15-0b0e-421a-84e5-ddbf75dc6de4")
    display_brightness = CharacteristicInt("98bd0b16-0b0e-421a-84e5-ddbf75dc6de4")
    first_user_start = CharacteristicBool("98bd0b17-0b0e-421a-84e5-ddbf75dc6de4")
    custom_device_name = CharacteristicNullStringUf8(
        "98bd0b18-0b0e-421a-84e5-ddbf75dc6de4"
    )


class AquaContourContours(Service):
    uuid = "98bd0b10-0b0e-421a-84e5-ddbf75dc6de4"
    products = {ProductType.AQUA_CONTOURS}
    variant = "1"

    contour_receive = CharacteristicBytes(
        "98bd0b11-0b0e-421a-84e5-ddbf75dc6de4", variant="1"
    )
    contour_transmit = CharacteristicBytes(
        "98bd0b12-0b0e-421a-84e5-ddbf75dc6de4", variant="1"
    )
    contour_info = CharacteristicBytes(
        "98bd0b13-0b0e-421a-84e5-ddbf75dc6de4", variant="1"
    )
    contour_name_1 = CharacteristicNullStringUf8(
        "98bd0b1a-0b0e-421a-84e5-ddbf75dc6de4", variant="1"
    )
    contour_name_2 = CharacteristicNullStringUf8(
        "98bd0b1b-0b0e-421a-84e5-ddbf75dc6de4", variant="1"
    )
    contour_name_3 = CharacteristicNullStringUf8(
        "98bd0b1c-0b0e-421a-84e5-ddbf75dc6de4", variant="1"
    )
    contour_name_4 = CharacteristicNullStringUf8(
        "98bd0b1d-0b0e-421a-84e5-ddbf75dc6de4", variant="1"
    )
    contour_name_5 = CharacteristicNullStringUf8(
        "98bd0b1e-0b0e-421a-84e5-ddbf75dc6de4", variant="1"
    )


class AquaContourSchedule(Service):
    uuid = "98bd0c10-0b0e-421a-84e5-ddbf75dc6de4"
    products = {ProductType.AQUA_CONTOURS}
    variant = "1"

    schedule_1 = CharacteristicBytes("98bd0c11-0b0e-421a-84e5-ddbf75dc6de4")
    schedule_2 = CharacteristicBytes("98bd0c12-0b0e-421a-84e5-ddbf75dc6de4")
    schedule_3 = CharacteristicBytes("98bd0c13-0b0e-421a-84e5-ddbf75dc6de4")
    schedule_4 = CharacteristicBytes("98bd0c14-0b0e-421a-84e5-ddbf75dc6de4")
    schedule_5 = CharacteristicBytes("98bd0c15-0b0e-421a-84e5-ddbf75dc6de4")
    schedule_6 = CharacteristicBytes("98bd0c16-0b0e-421a-84e5-ddbf75dc6de4")
    schedule_7 = CharacteristicBytes("98bd0c17-0b0e-421a-84e5-ddbf75dc6de4")
    schedule_8 = CharacteristicBytes("98bd0c18-0b0e-421a-84e5-ddbf75dc6de4")
    schedule_9 = CharacteristicBytes("98bd0c19-0b0e-421a-84e5-ddbf75dc6de4")
    schedule_10 = CharacteristicBytes("98bd0c1a-0b0e-421a-84e5-ddbf75dc6de4")
    schedule_11 = CharacteristicBytes("98bd0c1b-0b0e-421a-84e5-ddbf75dc6de4")
    schedule_12 = CharacteristicBytes("98bd0c1c-0b0e-421a-84e5-ddbf75dc6de4")
    schedule_13 = CharacteristicBytes("98bd0c1d-0b0e-421a-84e5-ddbf75dc6de4")
    schedule_14 = CharacteristicBytes("98bd0c1e-0b0e-421a-84e5-ddbf75dc6de4")
    schedule_15 = CharacteristicBytes("98bd0c1f-0b0e-421a-84e5-ddbf75dc6de4")


class Schedule(Service, ABC):
    products = set(ProductType) - {ProductType.AQUA_CONTOURS}

    def __init_subclass__(cls, *, instance: int, **kwargs):
        def _uuid(offset: int) -> str:
            return f"98bd0c{0x10 * instance + offset:02x}-0b0e-421a-84e5-ddbf75dc6de4"

        cls.uuid = _uuid(0)
        cls.start_time = CharacteristicLong(_uuid(1), name="Start Time")
        cls.duration = CharacteristicLong(_uuid(2), name="Duration")
        cls.weekdays = CharacteristicWeekday(_uuid(3), name="Weekdays")
        cls.valve_link = CharacteristicBytes(_uuid(4), name="Valve Link")
        cls.active = CharacteristicBool(_uuid(5), name="Active")
        cls.sensor_link = CharacteristicBool(_uuid(6), name="Sensor Link")
        super().__init_subclass__(**kwargs)


class Schedule_1(Schedule, instance=1):
    pass


class Schedule_2(Schedule, instance=2):
    pass


class Schedule_3(Schedule, instance=3):
    pass


class Schedule_4(Schedule, instance=4):
    pass


class Schedule_5(Schedule, instance=5):
    pass


class DeviceInformation(Service):
    uuid = "0000180a-0000-1000-8000-00805f9b34fb"
    model_number = CharacteristicString("00002a24-0000-1000-8000-00805f9b34fb")
    firmware_version = CharacteristicString("00002a26-0000-1000-8000-00805f9b34fb")
    manufacturer_name = CharacteristicString("00002a29-0000-1000-8000-00805f9b34fb")


class Battery(Service):
    uuid = "98bd180f-0b0e-421a-84e5-ddbf75dc6de4"

    battery_level = CharacteristicInt("98bd2a19-0b0e-421a-84e5-ddbf75dc6de4")


class Sensor(Service):
    uuid = "98bd0010-0b0e-421a-84e5-ddbf75dc6de4"

    value = CharacteristicInt("98bd0011-0b0e-421a-84e5-ddbf75dc6de4")
    connected_state = CharacteristicBool("98bd0012-0b0e-421a-84e5-ddbf75dc6de4")
    type = CharacteristicString("98bd0013-0b0e-421a-84e5-ddbf75dc6de4")
    threshold = CharacteristicInt("98bd0014-0b0e-421a-84e5-ddbf75dc6de4")
    battery_level = CharacteristicInt("98bd0015-0b0e-421a-84e5-ddbf75dc6de4")
    measurement_timestamp = CharacteristicTime("98bd0016-0b0e-421a-84e5-ddbf75dc6de4")
    force_measurement = CharacteristicInt("98bd0017-0b0e-421a-84e5-ddbf75dc6de4")


class WateringHistory(Service):
    uuid = "98bd0d10-0b0e-421a-84e5-ddbf75dc6de4"

    timestamp_array = CharacteristicTimeArray("98bd0d11-0b0e-421a-84e5-ddbf75dc6de4")
    timestamp_count = CharacteristicInt("98bd0d12-0b0e-421a-84e5-ddbf75dc6de4")
    skip_reason = CharacteristicBytes("98bd0d13-0b0e-421a-84e5-ddbf75dc6de4")
    watering_duration = CharacteristicLongArray("98bd0d14-0b0e-421a-84e5-ddbf75dc6de4")
    watering_skipped = CharacteristicBool("98bd0d15-0b0e-421a-84e5-ddbf75dc6de4")
    skipped_schedule_number = CharacteristicInt("98bd0d16-0b0e-421a-84e5-ddbf75dc6de4")
    water_control_error = CharacteristicInt("98bd0d17-0b0e-421a-84e5-ddbf75dc6de4")
    watering_pause = CharacteristicLong("98bd0d18-0b0e-421a-84e5-ddbf75dc6de4")
    seasonal_adjust = CharacteristicInt("98bd0d19-0b0e-421a-84e5-ddbf75dc6de4")
    rain_sensitivity = CharacteristicInt("98bd0d1a-0b0e-421a-84e5-ddbf75dc6de4")


class ErrorHistory(Service):
    uuid = "98bdeeee-0b0e-421a-84e5-ddbf75dc6de4"

    error_id = CharacteristicBytes("98bdeeef-0b0e-421a-84e5-ddbf75dc6de4")
    error_count = CharacteristicInt("98bdeef0-0b0e-421a-84e5-ddbf75dc6de4")


class Pump(Service):
    uuid = "98bd0100-0b0e-421a-84e5-ddbf75dc6de4"

    status = CharacteristicInt("98bd0101-0b0e-421a-84e5-ddbf75dc6de4")
    tank_preassure = CharacteristicUInt16("98bd0102-0b0e-421a-84e5-ddbf75dc6de4")
    flow_rate = CharacteristicUInt16("98bd0103-0b0e-421a-84e5-ddbf75dc6de4")
    ptu_mode = CharacteristicInt("98bd0104-0b0e-421a-84e5-ddbf75dc6de4")
    leakage_detection = CharacteristicBool("98bd0105-0b0e-421a-84e5-ddbf75dc6de4")
    min_preassure = CharacteristicInt("98bd0106-0b0e-421a-84e5-ddbf75dc6de4")
    max_preassure = CharacteristicInt("98bd0107-0b0e-421a-84e5-ddbf75dc6de4")
    child_lock = CharacteristicBool("98bd0108-0b0e-421a-84e5-ddbf75dc6de4")
    filter_reminder = CharacteristicInt("98bd0109-0b0e-421a-84e5-ddbf75dc6de4")
    direct_start = CharacteristicBool("98bd010a-0b0e-421a-84e5-ddbf75dc6de4")
    max_runtime = CharacteristicInt("98bd010b-0b0e-421a-84e5-ddbf75dc6de4")
    safety_pump_time = CharacteristicInt("98bd010c-0b0e-421a-84e5-ddbf75dc6de4")
    cool_down_timer = CharacteristicUInt16("98bd010d-0b0e-421a-84e5-ddbf75dc6de4")
    water_temperature = CharacteristicInt("98bd010e-0b0e-421a-84e5-ddbf75dc6de4")
    error_code = CharacteristicBytes("98bd010f-0b0e-421a-84e5-ddbf75dc6de4")
    user_motor_runtime = CharacteristicLong("98bd0110-0b0e-421a-84e5-ddbf75dc6de4")
    total_motor_runtime = CharacteristicLong("98bd0111-0b0e-421a-84e5-ddbf75dc6de4")


class Spray(Service):
    uuid = "98bd0110-0b0e-421a-84e5-ddbf75dc6de4"
    variant = "1"

    distance = CharacteristicInt("98bd0111-0b0e-421a-84e5-ddbf75dc6de4", variant="1")
    sector = CharacteristicInt("98bd0112-0b0e-421a-84e5-ddbf75dc6de4", variant="1")
    current_distance = CharacteristicInt(
        "98bd0113-0b0e-421a-84e5-ddbf75dc6de4", variant="1"
    )
    current_sector = CharacteristicInt(
        "98bd0114-0b0e-421a-84e5-ddbf75dc6de4", variant="1"
    )
    watering_mode_error = CharacteristicInt(
        "98bd0115-0b0e-421a-84e5-ddbf75dc6de4", variant="1"
    )


class EventHistory(Service):
    uuid = "98bd0120-0b0e-421a-84e5-ddbf75dc6de4"
    history = CharacteristicBytes("98bd0121-0b0e-421a-84e5-ddbf75dc6de4")
    error = CharacteristicBytes("98bd0122-0b0e-421a-84e5-ddbf75dc6de4")


class AquaContour(Service):
    uuid = "98bd0a10-0b0e-421a-84e5-ddbf75dc6de4"

    unix_timestamp = CharacteristicTime("98bd0a11-0b0e-421a-84e5-ddbf75dc6de4")
    custom_device_name = CharacteristicNullStringUf8(
        "98bd0a12-0b0e-421a-84e5-ddbf75dc6de4"
    )
    frost_warning = CharacteristicBool("98bd0a15-0b0e-421a-84e5-ddbf75dc6de4")
    active_contour = CharacteristicBytes("98bd0a16-0b0e-421a-84e5-ddbf75dc6de4")


class FlowStatistics(Service):
    uuid = "98bd0e10-0b0e-421a-84e5-ddbf75dc6de4"
    overall = CharacteristicLong("98bd0e16-0b0e-421a-84e5-ddbf75dc6de4")
    resettable = CharacteristicLong("98bd0e17-0b0e-421a-84e5-ddbf75dc6de4")
    last_reset = CharacteristicTime("98bd0e18-0b0e-421a-84e5-ddbf75dc6de4")
    current = CharacteristicInt("98bd0e19-0b0e-421a-84e5-ddbf75dc6de4")


class AquaContourPosition(Service):
    uuid = "98bd0130-0b0e-421a-84e5-ddbf75dc6de4"
    active_position = CharacteristicInt("98bd0132-0b0e-421a-84e5-ddbf75dc6de4")
    position_mask = CharacteristicBytes("98bd0135-0b0e-421a-84e5-ddbf75dc6de4")
    position_name_1 = CharacteristicNullStringUf8(
        "98bd013a-0b0e-421a-84e5-ddbf75dc6de4"
    )
    position_name_2 = CharacteristicNullStringUf8(
        "98bd013b-0b0e-421a-84e5-ddbf75dc6de4"
    )
    position_name_3 = CharacteristicNullStringUf8(
        "98bd013c-0b0e-421a-84e5-ddbf75dc6de4"
    )
    position_name_4 = CharacteristicNullStringUf8(
        "98bd013d-0b0e-421a-84e5-ddbf75dc6de4"
    )
    position_name_5 = CharacteristicNullStringUf8(
        "98bd013e-0b0e-421a-84e5-ddbf75dc6de4"
    )


class AquaContourBattery(Service):
    uuid = "0000180f-0000-1000-8000-00805f9b34fb"
    battery_level = CharacteristicInt("00002a19-0000-1000-8000-00805f9b34fb")
    battery_level_status = CharacteristicInt("00002bed-0000-1000-8000-00805f9b34fb")


class Reset(Service):
    uuid = "98bdff00-0b0e-421a-84e5-ddbf75dc6de4"

    factory_reset = CharacteristicBool("98bdff01-0b0e-421a-84e5-ddbf75dc6de4")


class Oad(Service):
    uuid = "f000ffd0-0451-4000-b000-000000000000"

    enable_oad = CharacteristicBool("f000ffd1-0451-4000-b000-000000000000")


class Fota(Service):
    uuid = "f000ffc0-0451-4000-b000-000000000000"

    image_identify = CharacteristicBytes("f000ffc1-0451-4000-b000-000000000000")
    image_block_id = CharacteristicBytes("f000ffc2-0451-4000-b000-000000000000")
    control_point = CharacteristicBytes("f000ffc5-0451-4000-b000-000000000000")
