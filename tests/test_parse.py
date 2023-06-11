from gardena_bluetooth.parse import ManufacturerData, ProductGroup


def test_manufacturer_data():
    raw = b"\x02\x07d\x02\x05\x01\x02\x08\x00\x02\t\x01\x04\x06\x12\x00\x01"
    data = ManufacturerData.decode(raw)
    assert data == ManufacturerData(
        pairable=True, serial=None, group=ProductGroup.WATER_CONTROL, model=0, variant=1
    )

    raw = b"\x02\x07d\x02\x05\x01\x02\x08\x00\x02\t\x01\x04\x06\x20\x00\x01\x05\x04\x01\x02\x03\x04"
    data = ManufacturerData.decode(raw)
    assert data == ManufacturerData(
        pairable=True, serial=0x04030201, group=32, model=0, variant=1
    )
