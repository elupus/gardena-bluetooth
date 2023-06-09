from .parse import Service, CharacteristicBool, CharacteristicInt, CharacteristicString, CharacteristicBytes

ScanService = "98bd0001-0b0e-421a-84e5-ddbf75dc6de4"
FotaService = "0000ffc0-0000-1000-8000-00805f9b34fb"


class Value(Service):
    uuid = "98bd0f10-0b0e-421a-84e5-ddbf75dc6de4"

    state = CharacteristicBool("98bd0f11-0b0e-421a-84e5-ddbf75dc6de4")
    connected_state = CharacteristicBool("98bd0f12-0b0e-421a-84e5-ddbf75dc6de4")
    remaining_open_state = CharacteristicInt("98bd0f13-0b0e-421a-84e5-ddbf75dc6de4")
    manual_watering_time = CharacteristicInt("98bd0f14-0b0e-421a-84e5-ddbf75dc6de4")
    activation_reason = CharacteristicInt("98bd0f15-0b0e-421a-84e5-ddbf75dc6de4")

class DeviceConfiguration(Service):
    uuid = "98bd0b10-0b0e-421a-84e5-ddbf75dc6de4"

    rain_pause = CharacteristicBytes("98bd0b11-0b0e-421a-84e5-ddbf75dc6de4")
    season_pause = CharacteristicBytes("98bd0b12-0b0e-421a-84e5-ddbf75dc6de4")
    unix_timestamp = CharacteristicBytes("98bd0b13-0b0e-421a-84e5-ddbf75dc6de4")
    mobile_device_name = CharacteristicBytes("98bd0b14-0b0e-421a-84e5-ddbf75dc6de4")
    device_language = CharacteristicBytes("98bd0b15-0b0e-421a-84e5-ddbf75dc6de4")
    display_brightness = CharacteristicBytes("98bd0b16-0b0e-421a-84e5-ddbf75dc6de4")
    first_user_start = CharacteristicBytes("98bd0b17-0b0e-421a-84e5-ddbf75dc6de4")
    custom_device_name = CharacteristicString("98bd0b18-0b0e-421a-84e5-ddbf75dc6de4")

class DeviceInformation(Service):
    uuid = "0000180a-0000-1000-8000-00805f9b34fb"
    model_number = CharacteristicString("00002a24-0000-1000-8000-00805f9b34fb")
    firmware_version = CharacteristicString("00002a26-0000-1000-8000-00805f9b34fb")
    manufacturer_name = CharacteristicString("00002a29-0000-1000-8000-00805f9b34fb")

class Battery(Service):
    uuid = "98bd180f-0b0e-421a-84e5-ddbf75dc6de4"

    battery_level = CharacteristicInt("98bd2a19-0b0e-421a-84e5-ddbf75dc6de4")
