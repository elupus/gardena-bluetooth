from .parse import (
    CharacteristicBool,
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
}

ScanService = "98bd0001-0b0e-421a-84e5-ddbf75dc6de4"
FotaService = "0000ffc0-0000-1000-8000-00805f9b34fb"


class Scan(Service):
    uuid = "98bd0001-0b0e-421a-84e5-ddbf75dc6de4"

    write_characteristic = CharacteristicBytes("98BD0002-0B0E-421A-84E5-DDBF75DC6DE4")
    read_characteristic = CharacteristicBytes("98BD0003-0B0E-421A-84E5-DDBF75DC6DE4")
    read_protocol_descriptor = CharacteristicNullString(
        "98BD0004-0B0E-421A-84E5-DDBF75DC6DE4"
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
