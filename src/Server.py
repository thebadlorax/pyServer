import socket, time

from threading import Thread
from _thread import start_new_thread

from packet.Packet import Packet
from packet.MessagePacket import MessagePacket

from dataclasses import dataclass

from Console import Console # nice console i made

HOST = "localhost"
PORT = 5001 # port doesnt really matter so long as nothing else is using it
DISCONNECT_TIME = 10 # in seconds

@dataclass
class Connection:
    socket: socket.socket
    address: list
    time: float
    

class Server:
    def __init__(self) -> None:
        self._SOCKET: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self._CONNECTIONS: list[Connection] = []
        self._DEAD_CONNECTIONS: list[Connection] = [] # dead connections are connections that have disconnected but i want to know they are returning instead of a new connection

        self.INTENSIVE_LOGGING: bool = False

        self.HOST: str = HOST
        self.PORT: int = PORT
        self._DISCONNECT_TIME: int = DISCONNECT_TIME # in seconds
        
        #self._OUTGOING_PACKETS: list[Packet] = [] # i wanna refactor this to use a list of packets per packet send

        # daemon setup                these get started and configured later
        self.DC_D: Thread = Thread()  # disconnect daemon -> _CHECK_IF_CONNECTION_IS_ALIVE

        self._CONSOLE: Console = Console()
        self._CONSOLE.setIntensiveLogging(self.INTENSIVE_LOGGING)

        self._RUN() # could move into here but this looks better tbh

    def _CONFIGURE_DAEMON(self, target) -> Thread: # got tired of manually doing this
        # normally, threads dont let the program exit if they are still running, but daemons
        # -dont care if you exit during them.
        daemon: Thread = Thread(target=target)
        daemon.daemon = True
        return daemon

    def _CHECK_IF_CONNECTION_IS_ALIVE(self) -> None:
        while True:
            for conn in self._CONNECTIONS:
                if(time.time() - conn.time >= DISCONNECT_TIME):
                    self._CONSOLE.warn(f'connection lost abruptly with client {conn.address[0]}')
                    conn.socket.close()
                    self._DEAD_CONNECTIONS.append(conn)
                    self._CONNECTIONS.remove(conn)
                    self._UPDATE_BANNER()
            time.sleep(0.5) # not needed but i like not wasting compute

    def _SEND_PACKET(self, connection: socket.socket, packet: Packet) -> None: # maybe make this return boolean of if sent
        time.sleep(0.1) # need a lil delay, or it gets out of sync
        data = b''.join(packet.getRawData())
        dataArr = bytearray(data) # byte arrays are needed
        if self.INTENSIVE_LOGGING: self._CONSOLE.log(f"sending packet: {repr(packet.getName())}")
        connection.send(dataArr)

    def _GET_CONNECTION(self, sock: socket.socket) -> int: # see if a socket is in the connection list, if so then return the index
        for i in range(len(self._CONNECTIONS)):
            if self._CONNECTIONS[i].socket == sock:
                return i
        self._CONSOLE.error("Server#GetConnection failed to find connection: returned -1")
        raise SystemExit # this should only be called if the connection actually is in this list, so this shouldn't ever happen


    def _RUN(self) -> None:
        self.DC_D = self._CONFIGURE_DAEMON(self._CHECK_IF_CONNECTION_IS_ALIVE) # start processing dead clients
        self.DC_D.start()

        self._UPDATE_BANNER()

        with self._SOCKET as s:
            try:
                s.bind((self.HOST, self.PORT))
            except OSError:
                self._CONSOLE.error("failure to bind server socket, common issue when you exited too recently, try again later")
                raise SystemExit
            self._CONSOLE.log(f"server started on {self.HOST}, {self.PORT}")
            while True:
                s.listen()
                conn, addr = s.accept()
                connection: Connection = Connection(conn, addr, time.time())
                self._CONNECTIONS.append(Connection(conn, addr, time.time()))
                start_new_thread(self._HANDLE_INCOMING, (connection,))

    def _UPDATE_BANNER(self):
        self._CONSOLE.setBanner(f"Connection Count: {len(self._CONNECTIONS)}")
            
    def _HANDLE_INCOMING(self, conn: Connection):
        self._UPDATE_BANNER()
        with conn.socket:
            self._CONSOLE.log(f"new incoming connection: {conn.address[0]}")
            self._SEND_PACKET(conn.socket, MessagePacket(f"Welcome, heartbeat cutoff is set to {self._DISCONNECT_TIME} seconds."))
            self._SEND_PACKET(conn.socket, MessagePacket(f"You are here with {len(self._CONNECTIONS)-1} others."))
            if self.INTENSIVE_LOGGING: self._SEND_PACKET(conn.socket, MessagePacket("INTENSIVE LOGGING IS ENABLED SERVERSIDE"))

            while True:
                data = conn.socket.recv(1024) # can increase byte buffer, but probably slower
                if not data:
                    break
                    
                # demonic string manipulation - dont even ask me how these work tbh
                packetName = data[1:data[0]+1]
                packetData = data[data[0]+1:]

                if self.INTENSIVE_LOGGING: self._CONSOLE.log(f"recieved packet: {repr(packetData)}")

                match packetName: # switch but python
                    case b'heartbeat':
                        if self.INTENSIVE_LOGGING: self._CONSOLE.log(f"recieved heartbeat packet from {conn.address[0]}")
                        self._CONNECTIONS[self._GET_CONNECTION(conn.socket)].time = time.time() # refresh death time
                    case b'message':
                        message = packetData[1:packetData[0]+1].decode("utf-8")
                        self._CONSOLE.messageFromClient(message)
                    case _:
                        self._CONSOLE.warn(f'recieved unknown data from {conn.address[0]}: {repr(data)}')


if __name__ == "__main__": # debug basically
    server = Server()
