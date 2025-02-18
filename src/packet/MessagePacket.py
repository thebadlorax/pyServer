from .Packet import Packet

class MessagePacket(Packet):
    def __init__(self, message: str) -> None:
        super().__init__(
                [len(message).to_bytes(1, "big"), message.encode("utf-8")], # message data
                b'message') # name
