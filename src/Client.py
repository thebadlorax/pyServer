import socket, time
from threading import Thread

from packet.HeartbeatPacket import HeartbeatPacket
from packet.MessagePacket import MessagePacket
from packet.Packet import Packet

from Console import Console

HOST = "localhost"
PORT = 5001

class Client:
    def __init__(self) -> None:
        self._SOCKET: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.HOST: str = HOST
        self.PORT: int = PORT

        self._OUTGOING_PACKETS: list[Packet] = []

        self.INTENSIVE_LOGGING: bool = False

        self._HEARTBEAT_INTERVAL: int = 3 # Must be less than Server#DISCONNECT_TIME

        self._CONSOLE: Console = Console()
        self._CONSOLE.setIntensiveLogging(self.INTENSIVE_LOGGING)

        self._CN_D: Thread = Thread() # Connection daemon -> _RUN
        self._RP_D: Thread = Thread() # Recieve packets daemon -> _HANDLE_INCOMING_PACKETS
        self._SP_D: Thread = Thread() # Send packets daemon -> _SEND_OUTGOING_PACKETS
        self._HB_D: Thread = Thread() # Heartbeat daemon -> _HEARTBEAT

        self._CN_D = self._CONFIGURE_DAEMON(self._RUN())
        self._CN_D.start() # actually start the client

    def _CONFIGURE_DAEMON(self, target) -> Thread:
        # normally, threads dont let the program exit if they are still running, but daemons
        # dont care if you exit during them.
        daemon: Thread = Thread(target=target)
        daemon.daemon = True
        return daemon

    def _RUN(self) -> None:
        try:
            self._SOCKET.connect((self.HOST, self.PORT))
        except ConnectionRefusedError:
            self._CONSOLE.error("Connection Refused : Client#_RUN")
            raise SystemExit

        self._CONSOLE.log(f"Connected to server - {self.HOST}")
        self._CONSOLE.setBanner(f"Connected to {self.HOST}:{self.PORT}")
        self.addPacketToQueue(MessagePacket(f"Hello, my heartbeat interval is {self._HEARTBEAT_INTERVAL} seconds."))
        if self.INTENSIVE_LOGGING: self.addPacketToQueue(MessagePacket("INTENSIVE_LOGGING IS ENABLED CLIENTSIDE"))

        self._RP_D = self._CONFIGURE_DAEMON(self._HANDLE_INCOMING_PACKETS)
        self._RP_D.start()

        self._SP_D = self._CONFIGURE_DAEMON(self._SEND_OUTGOING_PACKETS)
        self._SP_D.start()

        self._HB_D = self._CONFIGURE_DAEMON(self._HEARTBEAT)
        self._HB_D.start()

        while True:
            time.sleep(1)
            if not self._SP_D.is_alive():
                self._CONSOLE.error("connection to server lost")
                raise SystemExit

    def _SEND_PACKET(self, packet: Packet) -> None:
        time.sleep(0.1) # keeps stuff in sync (dont ask why it works)
        if(issubclass(packet.__class__, Packet)):
            try:
                data = b''.join(packet.getRawData())
                dataArr = bytearray(data)
                self._SOCKET.send(dataArr)
                if self.INTENSIVE_LOGGING: self._CONSOLE.log(f"sending packet: {packet.getName()}")
            except BrokenPipeError:
                self._CONSOLE.error(f"error sending packet {repr(packet.getName())} - BrokenPipeError : Client#_SEND_PACKET")
                self._SOCKET.close()
                raise SystemExit

    def _HANDLE_INCOMING_PACKETS(self) -> None:
        while True:
            data = self._SOCKET.recv(1024)
            if not data:
                break

            # demonic string manip
            packetName = data[1:data[0]+1]
            packetData = data[data[0]+1:]

            match packetName:
                case b'message':
                    message = packetData[1:packetData[0]+1].decode("utf-8")
                    self._CONSOLE.messageFromServer(message)
                case _:
                    self._CONSOLE.warn(f"recieved unknown data from server: {repr(data)}")

    def addPacketToQueue(self, packet: Packet):
        if(issubclass(packet.__class__, Packet)):
            if self.INTENSIVE_LOGGING: self._CONSOLE.log(f"adding packet to queue: {packet.getName()}")
            self._OUTGOING_PACKETS.append(packet)
        else:
            self._CONSOLE.error("packet could not be added to queue, it wasn't a subclass of Packet. Client#addPacketToQueue")

    def _SEND_OUTGOING_PACKETS(self) -> None:
        while True:
            for packet in self._OUTGOING_PACKETS:
                if(issubclass(packet.__class__, Packet)):
                    self._SEND_PACKET(packet)
                    self._OUTGOING_PACKETS.remove(packet)
                else:
                    self._CONSOLE.error("packet send error, not a packet : Client#_SEND_OUTGOING_PACKETS")


    def serverIsAlive(self) -> bool:
        return self._CN_D.is_alive()

    def _HEARTBEAT(self) -> None:
        while True:
            time.sleep(self._HEARTBEAT_INTERVAL)
            self.addPacketToQueue(HeartbeatPacket())
            #if(self.INTENSIVE_LOGGING): self._CONSOLE.log("sent keepalive packet")

if __name__ == "__main__":
    client = Client()
    time.sleep(1) # just stalls out for now, its important that the client doesn't block the main thread because you would want to actually do stuff while networking is running
