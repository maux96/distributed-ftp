
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
        self.sinc = Sinc(coordinator, self)

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
                        if(count_sup >= k):
                            return False
                except (TimeoutError):
                    continue
                finally:
                    socket.close()
        return True            

    def send_election(self):
        '''Enviar peticion de liderazgo a los otros coordinadores'''
        logging.info(str(self.coordinator.id) + ": init selection process ")

        if(not is_in_k_best_aviables(1)):
            return

        self.leader = True
        self.coordinator.accepting_connections = True
        self.leader_host = self.coordinator.host
        self.leaders_group = [self.leader_host]
        logging.info(str(self.coordinator.id) + ": I'm the leader")

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

        if(not is_in_k_best_aviables(Bully.K_MAX_LEADERS_GROUP)):
            return

        self.leaders_group = [self.leader_host, self.coordinator.host]    
        #TODO implementar la entrada al leader group, deben tenerlo todos los que pertencen a este grupo principalmente el lider general

        logging.info(str(self.coordinator.id) + ": I'm in the leader group")


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
                    socket.send(b"ok")
                elif message == "election":
                    socket.send(b"ok")
                elif message == "leader":
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
                elif message == "get_sinc":
                    # Dice que esta listo para enviar la informacion
                    socket.send(b"ok")

                elif message == "set_sinc":
                    # Dice que esta listo para recibir la informacion
                    socket.send(b"ok")

                elif message is not None:
                    self.sinc.recieve_sinc(message)

            except (TimeoutError):
                pass
            finally:
                socket.close()

    def loop_ping(self):
        logging.info(str(self.coordinator.id) + ": loop ping init ")
        while True:
            if self.leader:
                self.send_election()
            else:
                if not self.ping(self.leader_host):
                    self.send_election()
            time.sleep(self.sleep_time)
