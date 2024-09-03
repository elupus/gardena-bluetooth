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
