import utils
import time
import logging
from .sinc import Sinc


class Bully:
    DEFAULT_LISTENING_PORT = 9999
    K_MAX_LEADERS_GROUP = 3

    def __init__(self, coordinator, sleep_time=10):
        self.coordinator = coordinator
        self.leader = True
        self.sleep_time = sleep_time
        self.listen_port = utils.create_socket_and_listen(
            coordinator.host, port=Bully.DEFAULT_LISTENING_PORT)
        self.leader_host = None
        self.leaders_group = []
        self.sinc = Sinc(coordinator, self, DEFAULT_LISTENING_PORT)

    def is_in_k_best_aviables(self, k):
        '''Enviar sennal a los superiores y devuelve si esta entre los k mejores activos'''

        coordinators = self.coordinator.available_coordinator
        count_sup = 0
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
                        count_sup += 1
                        if (count_sup >= k):
                            return False
                except (TimeoutError):
                    continue
                finally:
                    socket.close()
        return True

    def send_election(self):
        '''Enviar peticion de liderazgo a los otros coordinadores'''
        logging.info(str(self.coordinator.id) + ": init selection process ")

        if (not self.is_in_k_best_aviables(1)):
            return

        self.leader = True
        self.coordinator.accepting_connections = True
        self.leader_host = self.coordinator.host
        self.leaders_group = [self.leader_host]
        logging.info(str(self.coordinator.id) + ": I'm the leader")

        coordinators = self.coordinator.available_coordinator
        for id, (host, port) in coordinators.items():
            if self.coordinator.id < id:
                socket = utils.connect_socket_to(
                    host, Bully.DEFAULT_LISTENING_PORT)
                if socket is None:
                    continue
                try:
                    socket.settimeout(3)
                    socket.send(b"leader")
                except (TimeoutError):
                    continue
                finally:
                    socket.close()

    def send_election_for_leader_group(self):
        '''Enviar peticion de liderazgo a los otros coordinadores'''
        logging.info(str(self.coordinator.id) + ": init selection process ")

        socket = utils.connect_socket_to(
            self.leader_host, Bully.DEFAULT_LISTENING_PORT)

        if socket is None:
            return

        if (not self.is_in_k_best_aviables(Bully.K_MAX_LEADERS_GROUP)):
            try:
                socket.settimeout(3)
                socket.send(b"remove_leader_group")
            finally:
                socket.close()

        elif (not self.leader):
            try:
                socket.settimeout(3)
                socket.send(b"leader_group")
                logging.info(str(self.coordinator.id) + ": I'm in the leader group")
            finally:
                socket.close()

    def ping(self, host):
        logging.info(str(self.coordinator.id) + ": ping to " + host)

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
                logging.info(str(self.coordinator.id) +
                             ": recieve ping 'ok' from " + str(host))
                return True
            else:
                return False
        except (TimeoutError):
            return False

    def recive_message(self):
        while True:
            socket, addr = self.listen_port.accept()
            socket.settimeout(3)
            host = addr[0]
            message = socket.recv(256).decode('ascii')
            try:
                if message == "ping":
                    # recibe el ping y manda ok para atras para decir que esta disponible
                    socket.send(b"ok")

                elif message == "election":
                    # Dice que esta disponible y quien le pregunto entonces no puede ser lider
                    socket.send(b"ok")

                elif message == "leader":
                    # quien esta mandando del otro lado del socket es el lider actual
                    self.set_leader(host)

                elif message == "get_sinc":
                    # Dice que esta listo para enviar la informacion
                    socket.send(b"ok")

                elif message == "set_sinc":
                    # Dice que esta listo para recibir la informacion
                    socket.send(b"ok")

                elif message.split(" ")[0] == "data_sinc":
                    # recibe datos de sincronizacion y los procesa en la funcion proxima
                    self.sinc.recieve_sinc(message, host)

                elif message == "leader_group":
                    # recibe el tag de que quien envia va a pertencer al grupo de lideres secundarios
                    self.add_to_leader(host)
                    socket.send(b"ok")

                elif message == "remove_leader_group":
                    # recibe el tag de que quien envia va a ser eliminado del grupo de lideres secundarios
                    self.remove_from_leader(host)
                    socket.send(b"ok")

            except (TimeoutError):
                pass
            finally:
                socket.close()

    def loop_ping(self):
        logging.info(str(self.coordinator.id) + ": loop ping init ")
        while True:
            if self.leader:
                logging.info(str(self.coordinator.id) + ": the leader_group es "+ str(leaders_group))
                self.send_election()
            else:
                if not self.ping(self.leader_host):
                    self.send_election()
                    if not self.leader:
                        self.send_election_for_leader_group()
            time.sleep(self.sleep_time)

    def add_to_leader(self, host):
        if (host not in self.leaders_group):
            self.leaders_group.remove(host)
            logging.info(str(self.coordinator.id) + ": the leader "+ host +" has been append from group")

    def remove_from_leader(self, host):
        if host in self.leaders_group:
            self.leaders_group.remove(host)
            logging.info(str(self.coordinator.id) + ": the leader "+ host +" has been remove from group")

    def set_leader(self, host):
        self.leader_host = host
        if self.coordinator.host == host:
            self.leader = True
        else:
            logging.info(str(self.coordinator.id) +
                         ": My leader is " + str(host))
            logging.info(str(self.coordinator.id) +
                         ": I'm not the leader now")
            self.leader = False
            self.accepting_connections = False
