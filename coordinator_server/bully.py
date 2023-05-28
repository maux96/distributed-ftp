
import utils
import time
import logging

class Bully:
    DEFAULT_LISTENING_PORT = 9999

    def __init__(self, coordinator, sleep_time=10):
        self.coordinator = coordinator
        self.leader = True
        self.sleep_time = sleep_time
        self.listen_port = utils.create_socket_and_listen(
            coordinator.host, port=Bully.DEFAULT_LISTENING_PORT)
        self.leader_host = None

    def send_election(self):
        '''Enviar peticion de liderazgo a los otros coordinadores'''
        logging.info(str(self.coordinator.id) +": init selection process ")

        coordinators = self.coordinator.available_coordinator
        for id, (host, port) in coordinators.items():
            if self.coordinator.id > id:
                # TODO aqui ver como se abre un hilo y esa talla,
                # y luego de n segundos hacer decidir si es el jefe
                socket = utils.connect_socket_to(
                    host, Bully.DEFAULT_LISTENING_PORT)
                if socket is None:
                    continue
                try:
                    socket.settimeout(3)
                    socket.send(b"election")
                    is_ok = socket.recv(64)
                    if (is_ok == b"ok"):
                        return
                except (TimeoutError):
                    continue
                finally:
                    socket.close()

        self.leader = True
        self.coordinator.accepting_connections = True
        self.leader_host = self.coordinator.host

        for id, (host, port) in coordinators.items():
            if self.coordinator.id < id:
                socket = utils.connect_socket_to(
                    host, Bully.DEFAULT_LISTENING_PORT)
                if socket is None:
                    continue
                try:
                    socket.settimeout(3)
                    socket.send(b"leader")
                    logging.info(str(self.coordinator.id) +": I'm the leader")
                except (TimeoutError):
                    continue
                finally:
                    socket.close()

    def ping(self, host):
        logging.info(str(self.coordinator.id) +": ping to "+ host)
        
        if host is None:
            return False

        socket = utils.connect_socket_to(host, Bully.DEFAULT_LISTENING_PORT)
        if socket is None:
            return False
        try:
            socket.settimeout(3)
            socket.send(b"ping")
            is_ok = socket.recv(64)
            if (is_ok == b"ok"):
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
                    socket.send(b"ok")
                elif message == "election":
                    socket.send(b"ok")
                elif message == "leader":
                    self.leader_host = host
                    if self.coordinator.host == host:
                        self.leader = True
                        logging.info(str(self.coordinator.id) +": My leader is " +str(host))
                    else:
                        logging.info(str(self.coordinator.id) +": I'mnt the leader now")
                        self.leader = False
                        self.accepting_connections = False
            except (TimeoutError):
                pass
            finally:
                socket.close()

    def loop_ping(self):
        logging.info(str(self.coordinator.id) +": loop ping init ")
        while True:
            if self.leader:
                self.send_election()
            else:
                if not self.ping(self.leader_host):
                    self.send_election()
            time.sleep(self.sleep_time)
