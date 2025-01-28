class Packet:
    def __init__(self, data: list[bytes] = [b'no data'], name: bytes = b'no name') -> None:
        self._DATA = [len(name).to_bytes(1, "big"), name] + data
        self._NAME = name

    def getRawData(self) -> list[bytes]: # i like having nice getter functions, you could always do Packet._DATA if you really had to
        return self._DATA

    def getName(self) -> bytes:
        return self._NAME
