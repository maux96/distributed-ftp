
from .. import utils
import time

class Bully:
    DEFAULT_LISTENING_PORT = 9999

    def __init__(self, coordinator, sleep_time=10):
        self.coordinator = coordinator
        self.coordinator.leader = False
        self.sleep_time = sleep_time
        self.listen_port = utils.create_socket_and_listen(
            coordinator.host, port=Bully.DEFAULT_LISTENING_PORT)
        self.leader_host = None
        self.recive_message()

    def send_election(self):
        '''Enviar peticion de liderazgo a los otros coordinadores'''
        coordinators = self.coordinator.available_coordinator
        for id,(host, port) in coordinators.items():
            if self.coordinator.id > id:
                #aqui ver como se abre un hilo y esa talla, y luego de n segundos hacer decidir si es el jefe
                socket = utils.connect_socket_to(host, DEFAULT_LISTENING_PORT)
                if socket == None:
                    continue
                try:
                    socket.settimeout(3)
                    socket.send(b"election")
                    is_ok = socket.recv(64)
                    if(is_ok == b"ok"):
                        return
                except (TimeoutError):
                    continue    
                finally:
                    socket.close()

        self.coordinator.leader = True            
        self.coordinator.accepting_connections = True
        self.leader_host = self.coordinator.host

        for id,(host, port) in coordinators.items():
            if self.coordinator.id < id:
                socket = utils.connect_socket_to(host, DEFAULT_LISTENING_PORT)
                if socket == None:
                    continue
                try:
                    socket.settimeout(3)
                    socket.send("leader")
                except (TimeoutError):
                    continue
                finally:
                    socket.close()

    def ping(self, host):
        if host == None: return False

        socket = utils.connect_socket_to(host, DEFAULT_LISTENING_PORT)
        if socket == None:
            return False
        try:
            socket.settimeout(3)
            socket.send("ping")
            is_ok = socket.recv(64)
            if(is_ok == b"ok"):
                return True
        except (TimeoutError):
            pass
        finally:    
            return False

    def recive_message(self):
        while True:
            socket, addr = self.listen_port.accept()
            socket.settimeout(3)
            host = addr[0]
            message = socket.recv(256).decode('ascii')
            try:
                if message == "ping":
                    socket.send("ok")
                elif message == "election":
                    socket.send("ok")
                elif message == "leader":
                    self.leader_host = host
            except (TimeoutError):
                pass
            finally:
                socket.close() 
             
    def loop_ping(self):
        while True:
            if self.leader == True:
                self.send_election()
            else:
                if not self.ping(self.leader_host):
                    self.send_election()
            time.sleep(self.sleep_time)    
