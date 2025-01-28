from .Packet import Packet

class HeartbeatPacket(Packet):
    def __init__(self) -> None:
        super().__init__(
                [b'heartbeat'],
                b'heartbeat')
