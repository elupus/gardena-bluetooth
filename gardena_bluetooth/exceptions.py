class GardenaBluetoothException(Exception):
    pass


class CharacteristicNoAccess(GardenaBluetoothException):
    pass


class CharacteristicNotFound(CharacteristicNoAccess):
    pass
