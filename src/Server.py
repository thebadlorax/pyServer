import socket, time
from threading import Thread

from packet.Packet import Packet
from packet.MessagePacket import MessagePacket

from Console import Console

HOST = "localhost"
PORT = 5001
DISCONNECT_TIME = 5 # in seconds

class Server:
    def __init__(self) -> None:
        self._SOCKET: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self._CONNECTIONS = []
        self._DEAD_CONNECTIONS = []
        
        self._OUTGOING_PACKETS: list[Packet] = []

        # daemon setup
        self.SP_D: Thread = Thread()
        self.RP_D: Thread = Thread()
        self.DC_D: Thread = Thread()

        self.console = Console()

        self._RUN()

    def _CONFIGURE_DAEMON(self, target) -> Thread:
        daemon: Thread = Thread(target=target)
        daemon.daemon = True
        return daemon

    def _CHECK_IF_CONNECTION_IS_ALIVE(self):
        for conn in self._CONNECTIONS:
            if(time.time() - conn[2] >= DISCONNECT_TIME):
                self.console.log(f'connection lost abruptly with client addr {conn[1][0]}')
                conn[0].close()
                self._DEAD_CONNECTIONS.append(conn)
                self._CONNECTIONS.remove(conn)
        time.sleep(0.5)
        self._CHECK_IF_CONNECTION_IS_ALIVE()

    def _SEND_PACKET(self, connection: socket.socket, packet: Packet):
        time.sleep(0.1) # need a lil delay
        data = b''.join(packet.getRawData())
        dataArr = bytearray(data)
        connection.send(dataArr)

    def _GET_CONNECTION(self, sock: socket.socket):
        for i in range(len(self._CONNECTIONS)):
            if self._CONNECTIONS[i][0] == sock:
                return i
        self.console.error("Server#GetConnection failed to find connection: returned -1, something broke :(")
        return -1


    def _RUN(self):
        self.DC_D = self._CONFIGURE_DAEMON(self._CHECK_IF_CONNECTION_IS_ALIVE)
        self.DC_D.start()

        with self._SOCKET as s:
            s.bind((HOST, PORT))
            self.console.log(f"server started on {HOST}, {PORT}")
            s.listen()
            conn, addr = s.accept()
            self._CONNECTIONS.append([conn, addr, time.time(), "NoUsername", "NoDisplayname"]) # CONNECTION datastructure: Socket: socket.socket, Address: [], Time: Time.time, Username: str, Displayname: str

            with conn:
                self.console.log(f"new incoming connection: {addr[0]}")
                self._SEND_PACKET(conn, MessagePacket("hello"))

                while True:
                    data = conn.recv(1024)
                    if not data:
                        break
                    
                    # demonic string manipulation
                    packetName = data[1:data[0]+1]
                    packetData = data[data[0]+1:]

                    match packetName:
                        case b'keepAlive':
                            if(self._GET_CONNECTION(conn)):
                                self._CONNECTIONS[self._GET_CONNECTION(conn)][3] = time.time() # refresh death time
                        case _:
                            self.console.log(f'recieved unknown data from {addr[0]}: {repr(data)}')

if __name__ == "__main__":
    server = Server()
