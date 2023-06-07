from enum import Enum


class Value(Enum):
    Service = "98bd0f10-0b0e-421a-84e5-ddbf75dc6de4"

    State = "98bd0f11-0b0e-421a-84e5-ddbf75dc6de4"
    ConnectedState = "98bd0f12-0b0e-421a-84e5-ddbf75dc6de4"
    RemainingOpenState = "98bd0f13-0b0e-421a-84e5-ddbf75dc6de4"
    ManualWateringTime = "98bd0f14-0b0e-421a-84e5-ddbf75dc6de4"
    ActivationReason = "98bd0f15-0b0e-421a-84e5-ddbf75dc6de4"


class DeviceConfiguration(Enum):
    Service = "98bd0b10-0b0e-421a-84e5-ddbf75dc6de4"

    RainPause = "98bd0b11-0b0e-421a-84e5-ddbf75dc6de4"
    SeasonPause = "98bd0b12-0b0e-421a-84e5-ddbf75dc6de4"
    UnixTimestamp = "98bd0b13-0b0e-421a-84e5-ddbf75dc6de4"
    MobileDeviceName = "98bd0b14-0b0e-421a-84e5-ddbf75dc6de4"
    DeviceLanguage = "98bd0b15-0b0e-421a-84e5-ddbf75dc6de4"
    DisplayBrightness = "98bd0b16-0b0e-421a-84e5-ddbf75dc6de4"
    FirstUserStart = "98bd0b17-0b0e-421a-84e5-ddbf75dc6de4"
    CustomDeviceName = "98bd0b18-0b0e-421a-84e5-ddbf75dc6de4"


class DeviceInformation(Enum):
    Service = "0000180a-0000-1000-8000-00805f9b34fb"

    ModelNumber = "00002a24-0000-1000-8000-00805f9b34fb"
    FirmwareVersion = "00002a26-0000-1000-8000-00805f9b34fb"
    ManufacturerName = "00002a29-0000-1000-8000-00805f9b34fb"


class Battery(Enum):
    Service = "98bd180f-0b0e-421a-84e5-ddbf75dc6de4"

    BatteryLevel = "98bd2a19-0b0e-421a-84e5-ddbf75dc6de4"
