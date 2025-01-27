class Packet:
    def __init__(self, data: list[bytes] = [b'no data'], name: bytes = b'no name') -> None:
        self._DATA = [len(name).to_bytes(1, "big"), name] + data

    def getRawData(self) -> list[bytes]:
        return self._DATA
