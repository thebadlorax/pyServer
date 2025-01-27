import socket, time
from threading import Thread

from packet.Packet import Packet
from packet.MessagePacket import MessagePacket

from Console import Console # nice console i made

HOST = "localhost"
PORT = 5001 # port doesnt really matter so long as nothing else is using it (try to keep under 10000 i think)
DISCONNECT_TIME = 5 # in seconds

class Server:
    def __init__(self) -> None:
        self._SOCKET: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self._CONNECTIONS = []
        self._DEAD_CONNECTIONS = [] # dead connections are connections that have disconnected but i want to know they are returning instead of a new connection
        
        #self._OUTGOING_PACKETS: list[Packet] = [] # i wanna refactor this to use a list of packets per packet send

        # daemon setup                these get started and configured later
        #self.SP_D: Thread = Thread() # send packet daemon (not used yet)
        #self.RP_D: Thread = Thread() # recieve packet daemon (not used yet)
        self.DC_D: Thread = Thread()  # disconnect daemon -> _CHECK_IF_CONNECTION_IS_ALIVE

        self.console = Console()

        self._RUN() # could move into here but this looks better tbh

    def _CONFIGURE_DAEMON(self, target) -> Thread: # got tired of manually doing this
        # normally, threads dont let the program exit if they are still running, but daemons
        # -dont care if you exit during them.
        daemon: Thread = Thread(target=target)
        daemon.daemon = True
        return daemon

    def _CHECK_IF_CONNECTION_IS_ALIVE(self) -> None:
        for conn in self._CONNECTIONS:
            if(time.time() - conn[2] >= DISCONNECT_TIME):
                self.console.log(f'connection lost abruptly with client addr {conn[1][0]}')
                conn[0].close()
                self._DEAD_CONNECTIONS.append(conn)
                self._CONNECTIONS.remove(conn)
        time.sleep(0.5)
        self._CHECK_IF_CONNECTION_IS_ALIVE()

    def _SEND_PACKET(self, connection: socket.socket, packet: Packet) -> None: # maybe make this return boolean of if sent
        time.sleep(0.1) # need a lil delay, or it gets out of sync
        data = b''.join(packet.getRawData())
        dataArr = bytearray(data) # byte arrays are needed
        connection.send(dataArr)

    def _GET_CONNECTION(self, sock: socket.socket) -> int: # see if a socket is in the connection list, if so then return the index
        for i in range(len(self._CONNECTIONS)):
            if self._CONNECTIONS[i][0] == sock:
                return i
        self.console.error("Server#GetConnection failed to find connection: returned -1, something broke :(")
        raise Exception("connection not found : Server#_GET_CONNECTION")# this should only be called if the connection actually is in this list, so this shouldn't ever happen


    def _RUN(self) -> None:
        self.DC_D = self._CONFIGURE_DAEMON(self._CHECK_IF_CONNECTION_IS_ALIVE) # start processing dead clients
        self.DC_D.start()

        with self._SOCKET as s:
            s.bind((HOST, PORT))
            self.console.log(f"server started on {HOST}, {PORT}")
            s.listen()
            conn, addr = s.accept()
            self._CONNECTIONS.append([conn, addr, time.time(), "NoUsername", "NoDisplayname"]) 
          # CONNECTION datastructure: [Socket: socket.socket, Address: [], Time: Time.time, Username: str, Displayname: str]

            with conn:
                self.console.log(f"new incoming connection: {addr[0]}")
                self._SEND_PACKET(conn, MessagePacket("hello"))

                while True:
                    data = conn.recv(1024) # can increase byte buffer, but probably slower
                    if not data:
                        break
                    
                    # demonic string manipulation - dont even ask me how these work tbh
                    packetName = data[1:data[0]+1]
                    packetData = data[data[0]+1:]

                    match packetName: # switch but python
                        case b'keepAlive':
                            if(self._GET_CONNECTION(conn)):
                                self._CONNECTIONS[self._GET_CONNECTION(conn)][3] = time.time() # refresh death time
                        case _:
                            self.console.log(f'recieved unknown data from {addr[0]}: {repr(data)}')

if __name__ == "__main__": # debug basically
    server = Server()
