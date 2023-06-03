import utils
import time
import logging
from .sinc import Sinc


class Bully:
    DEFAULT_LISTENING_PORT = 9999
    K_MAX_LEADERS_GROUP = 3
    TIME_OUT = 1

    def __init__(self, coordinator, sleep_time=10):
        self.coordinator = coordinator
        self.leader = False
        self.in_leader_group = False
        self.sleep_time = sleep_time
        self.listen_port = utils.create_socket_and_listen(
            coordinator.host, port=Bully.DEFAULT_LISTENING_PORT)
        self.leader_host = None
        self.leaders_group = [self.coordinator.host]
        self.sinc = Sinc(coordinator, self, Bully.DEFAULT_LISTENING_PORT)
        self.send_election()

        self.hashs_dict = {}

    def is_in_k_best_aviables(self, k):
        '''Enviar sennal a los superiores y devuelve si esta entre los k mejores activos'''

        coordinators = self.coordinator.available_coordinator
        count_sup = 0
        for id, (host, port) in coordinators.items():
            if self.coordinator.id > id:
                # TODO aqui ver como se abre un hilo y esa talla,
                # y luego de n segundos hacer decidir si es el jefe
                socket = utils.connect_socket_to(
                    host, Bully.DEFAULT_LISTENING_PORT, timeout=Bully.TIME_OUT)
                if socket is None:
                    continue
                try:
                    # socket.settimeout(Bully.TIME_OUT)
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
        logging.info(str(self.coordinator.host) + ": init selection process ")

        if (not self.is_in_k_best_aviables(1)):
            self.leader = False
            self.coordinator.accepting_connections = False
            return

        if self.leader == True:
            logging.info(str(self.coordinator.host) + ": I'm the leader again")
        else:
            # Actualizar el hash porque se cayo un lider superior
            self.sinc.hash = self

            self.leader = True
            self.coordinator.accepting_connections = True
            self.leader_host = self.coordinator.host
            self.leaders_group = [self.leader_host]
            self.in_leader_group = True

            logging.info(str(self.coordinator.host) + ": I'm the leader")

        coordinators = self.coordinator.available_coordinator
        for id, (host, port) in coordinators.items():
            if self.coordinator.id < id:
                socket = utils.connect_socket_to(
                    host, Bully.DEFAULT_LISTENING_PORT, timeout=Bully.TIME_OUT)
                if socket is None:
                    continue
                try:
                    socket.send(b"leader")
                    buffer = socket.recv(2048)
                    if (buffer is not None):
                        # si a quien envio que ahora soy lider era lider entonces hay que entrar en el proceso de sincronizacion
                        self.sinc.get_sinc_from(buffer)

                except (TimeoutError):
                    continue
                finally:
                    socket.close()

    def send_election_for_leader_group(self):
        '''Enviar peticion de liderazgo a los otros coordinadores'''
        logging.info(str(self.coordinator.host) +
                     ": init selection leader group process ")

        socket = None
        if (not self.is_in_k_best_aviables(Bully.K_MAX_LEADERS_GROUP)):
            try:
                socket = utils.connect_socket_to(
                    self.leader_host, Bully.DEFAULT_LISTENING_PORT, timeout=Bully.TIME_OUT)

                if socket is None:
                    logging.info(str(self.coordinator.host) +
                                 ": selection leader socket is None ")
                    return

                logging.info(str(self.coordinator.host) +
                             ": try will remove from leader group")

                socket.send(b"remove_leader_group")
                is_ok = socket.recv(64)
                if (is_ok == b"ok"):
                    self.in_leader_group = False
                    logging.info(str(self.coordinator.host) +
                                 ": I was removed from leader group")
                else:
                    logging.warning(str(self.coordinator.host) +
                                    ": the operation removed from leader group failed: not recive message ok")

            except (TimeoutError):
                logging.warning(str(self.coordinator.host) +
                                ": the operation removed from leader group failed: TimeoutError")
            finally:
                if socket is not None:
                    socket.close()

        else:  # if (not self.leader):

            try:
                socket = utils.connect_socket_to(
                    self.leader_host, Bully.DEFAULT_LISTENING_PORT, timeout=Bully.TIME_OUT)

                if socket is None:
                    logging.info(str(self.coordinator.host) +
                                 ": selection leader socket is None ")
                    return

                logging.info(str(self.coordinator.host) +
                             ": try will append to leader group")

                socket.send(b"leader_group")
                is_ok = socket.recv(64)
                if (is_ok == b"ok"):
                    
                    self.in_leader_group = True
                    logging.info(str(self.coordinator.host) +
                                 ": I'm in the leader group")
                else:
                    logging.warning(str(self.coordinator.host) +
                                    ": the operation append to leader group failed: not recive message ok")

            except (TimeoutError):
                logging.warning(str(self.coordinator.host) +
                                ": the operation append to leader group failed: TimeoutError")

            finally:
                if socket is not None:
                    socket.close()

    def ping(self, host):
        logging.info(str(self.coordinator.host) + ": ping to " + host)

        if host is None:
            return False

        socket = utils.connect_socket_to(
            host, Bully.DEFAULT_LISTENING_PORT, timeout=Bully.TIME_OUT)
        if socket is None:
            return False

        try:
            # socket.settimeout(Bully.TIME_OUT)
            socket.send(b"ping")
            is_ok = socket.recv(64)
            if (is_ok == b"ok"):
                logging.info(str(self.coordinator.host) +
                             ": recieve ping 'ok' from " + str(host))
                return True
            else:
                return False
        except (TimeoutError, OSError):
            return False

    def receive_message(self):
        while True:
            socket, addr = self.listen_port.accept()
            socket.settimeout(Bully.TIME_OUT)
            host = addr[0]
            try:
                message = socket.recv(1024).decode('ascii')

                if message == "ping":
                    # recibe el ping y manda ok para atras para decir que esta disponible
                    socket.send(b"ok")

                elif message == "election":
                    # Dice que esta disponible y quien le pregunto entonces no puede ser lider
                    socket.send(b"ok")

                elif message == "leader":
                    # quien esta mandando del otro lado del socket es el lider actual
                    self.set_leader(host, socket)

                elif message.split(" ")[0] == "data_sinc":
                    # recibe datos de sincronizacion y los procesa en la funcion proxima
                    self.sinc.recieve_sinc(message, host)

                elif message == "leader_group":
                    # recibe el tag de que quien envia va a pertencer al grupo de lideres secundarios
                    logging.info(str(self.coordinator.host) +
                                 ": recived the peticion leader_group from " + str(host))
                    self.add_to_leader(host)
                    socket.send(b"ok")

                elif message == "remove_leader_group":
                    # recibe el tag de que quien envia va a ser eliminado del grupo de lideres secundarios
                    self.remove_from_leader(host)
                    socket.send(b"ok")

                elif (splited := message.split())[0] == "hash":
                    hash = splited[1]
                    self.hashs_dict[hash] = len(
                        self.coordinator.operations_log)
                    pass

            except (TimeoutError, OSError) as e:
                logging.error("Error in receiving_message"+str(e))

            finally:
                socket.close()

    def loop_ping(self):
        logging.info(str(self.coordinator.host) + ": loop ping init ")
        while True:
            if self.leader:

                for host in self.leaders_group:
                    if host != self.coordinator.host and not self.ping(host):
                        self.leaders_group.remove(host)

                logging.info(str(self.coordinator.host) +
                             ": the leader_group es " + str(self.leaders_group))
                self.send_election()

            else:
                if not self.ping(self.leader_host):
                    self.send_election()

                if not self.leader:
                    self.send_election_for_leader_group()

            time.sleep(self.sleep_time)

    def add_to_leader(self, host, socket):
        if (host not in self.leaders_group):
            self.leaders_group.append(host)
            logging.info(str(self.coordinator.host) + ": the leader " +
                         host + " has been append to the group")

    def remove_from_leader(self, host):
        if host in self.leaders_group:
            self.leaders_group.remove(host)
            logging.info(str(self.coordinator.host) + ": the leader " +
                         host + " has been remove from the group")

    def set_leader(self, host, socket=None):
        self.leader_host = host

        if self.coordinator.host == host:
            self.leader = True
        else:
            logging.info(str(self.coordinator.host) +
                         ": My leader is " + str(host))
            # logging.info(str(self.coordinator.host) +
            #              ": I'm not the leader")
            if self.leader:
                self.sinc.set_sinc_to(socket)

            self.leader = False
            self.accepting_connections = False