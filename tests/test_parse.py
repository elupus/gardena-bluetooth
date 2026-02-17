from gardena_bluetooth.parse import (
    ManufacturerData,
    ProductGroup,
    ProductType,
    CharacteristicString,
    CharacteristicNullStringUf8,
    CharacteristicNullString,
)


def test_manufacturer_data():
    raw = b"\x02\x07d\x02\x05\x01\x02\x08\x00\x02" b"\t\x01\x04\x06\x12\x00\x01"
    data = ManufacturerData.decode(raw)
    assert data == ManufacturerData(
        pairable=True, serial=None, group=ProductGroup.WATER_CONTROL, model=0, variant=1
    )

    assert ProductType.from_manufacturer_data(data) == ProductType.WATER_COMPUTER

    raw = (
        b"\x02\x07d\x02\x05\x01\x02\x08\x00\x02"
        b"\t\x01\x04\x06\x20\x00\x01\x05\x04\x01\x02\x03\x04"
    )
    data = ManufacturerData.decode(raw)
    assert data == ManufacturerData(
        pairable=True, serial=0x04030201, group=32, model=0, variant=1
    )

    assert ProductType.from_manufacturer_data(data) is None

    raw = (
        b"\x05\x04\x14\x18\x00\x00\x02\x05\x01\x04\x06\x11\x02\x02"
        b"\t\x01\x04\x06\x20\x00\x01\x05\x04\x01\x02\x03\x04"
    )
    data = ManufacturerData.decode(raw)
    assert data == ManufacturerData(
        pairable=True, serial=6164, group=17, model=2, variant=2
    )

    assert ProductType.from_manufacturer_data(data) is ProductType.PRESSURE_TANKS


def test_parse_manufacturer_data_aquaprecise():
    # For some reason the device seem to send different manufacture data
    # while app is connection, this data is from same device in different
    # states. Could be bootloader state maybe?

    raw = bytes.fromhex("0205000406121001")
    data = ManufacturerData.decode(raw)
    assert data == ManufacturerData(
        pairable=False,
        serial=None,
        group=ProductGroup.WATER_CONTROL,
        model=16,
        variant=1,
    )
    assert ProductType.from_manufacturer_data(data) is ProductType.AQUA_CONTOURS

    raw = bytes.fromhex("0504f162c103")
    data = ManufacturerData.decode(raw)
    assert data == ManufacturerData(
        pairable=None, serial=63005425, group=None, model=None, variant=None
    )


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
