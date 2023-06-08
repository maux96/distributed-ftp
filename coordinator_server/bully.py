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

        listen_port = utils.create_socket_and_listen(
            coordinator.host, port=Bully.DEFAULT_LISTENING_PORT)
        self.leader_host = None
        if listen_port is None:
            logging.error(
                f"port used in bully protocol {Bully.DEFAULT_LISTENING_PORT} is busy!")
            exit(1)
        else:
            self.listen_port = listen_port

        self.leaders_group = [(self.coordinator.host, self.coordinator.port)]
        self.sinc = Sinc(coordinator, self, Bully.DEFAULT_LISTENING_PORT)
        self.send_election()

        #self.hashs_dict = {}

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
            self.sinc.update_hash()

            #TODO mandar a que todos los del grupo de lider dejen de serlo xq se puede quedar uno con eso activado y creer para si
            #mismo que pertenece al grupo

            self.leader = True
            self.coordinator.accepting_connections = True
            self.leader_host = self.coordinator.host
            self.leaders_group = [(self.leader_host, self.coordinator.port)]
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
                    #True o falso indica si a quien le estoy enviando es o no coolider, en caso de serlo no pasa nada, si no lo es entonces debe hacer falsa la variable que lo hace coolider

                    hosts = [host_ for host_,_ in self.leaders_group]
                    if host in hosts:
                        socket.send(b"leader True")
                    else:
                        socket.send(b"leader False")

                    buffer = socket.recv(2048)
                    logging.debug(str(self.coordinator.host) + ": recieve the buffer " + str(buffer))

                    if (buffer != b"no"):
                        # si a quien envio que ahora soy lider era lider entonces hay que entrar en el proceso de sincronizacion
                        self.sinc.get_sinc_from(buffer)

                except (TimeoutError):
                    continue
                finally:
                    socket.close()

        #logging.debug("Current Hash: " + str(self.sinc.hash))
        #logging.debug("Hash Table Operations: " + str(self.sinc.logs_dict))

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

                socket.send(f"remove_leader_group {self.coordinator.port}".encode("ascii"))
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
            logging.debug("Current Hash: " + str(self.sinc.hash))
            logging.debug("Hash Table Operations: " + str(self.sinc.logs_dict))
            try:
                socket = utils.connect_socket_to(
                    self.leader_host, Bully.DEFAULT_LISTENING_PORT, timeout=Bully.TIME_OUT)

                if socket is None:
                    logging.info(str(self.coordinator.host) +
                                 ": selection leader socket is None ")
                    return

                logging.info(str(self.coordinator.host) +
                             ": try will append to leader group")
                
                socket.send(f"leader_group {self.coordinator.port}".encode("ascii"))
                is_ok = socket.recv(64)
                if (is_ok == b"ok"):

                    if (not self.in_leader_group):
                        socket.send(b"get_sync")
                        try:
                            recived_buffer = socket.recv(2048)
                            logging.debug("recibe el buffer del lider: " + str(recived_buffer))
                            self.sinc.sinc_with_leader(recived_buffer)
                            #socket.send(b"ok")
                        except:
                            logging.error(str(self.coordinator.host) + " sync with leader failed")

                        return
                    else: 
                        socket.send(b"no")

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

                elif message.split()[0] == "leader":
                    # quien esta mandando del otro lado del socket es el lider actual
                    self.set_leader(host, socket, message.split()[1])
                    
                elif message.split()[0] == "leader_group":
                    # recibe el tag de que quien envia va a pertencer al grupo de lideres secundarios
                    logging.info(str(self.coordinator.host) +
                                 ": recived the peticion leader_group from " + str(host))
                    self.add_to_leader(host, message.split()[1])
                    socket.send(b"ok")

                    logging.debug("Esperando el mensaje Get_sync de " + str(host))
                    resp=socket.recv(2048).decode('ascii')
                    logging.debug("Recibio el mensaje "+str(resp)+" de " + str(host))

                    if resp == 'get_sync':
                        logging.debug("Recibio el mensaje Get_sync de " + str(host))
                        self.sinc.send_sinc_to(socket)


                elif message.split()[0] == "remove_leader_group":
                    # recibe el tag de que quien envia va a ser eliminado del grupo de lideres secundarios
                    self.remove_from_leader(host, message.split()[1])
                    socket.send(b"ok")

               #elif message == "get_sync":
               #    logging.debug("Recibio el mensaje Get_sync de " + str(host))
               #    self.sinc.send_sinc_to(socket)

            except (TimeoutError, OSError) as e:
                logging.error("Error in receiving_message"+str(e))
            except Exception as e:
                logging.error("*Error in receiving_message "+str(e))

            finally:
                socket.close()

    def loop_ping(self):
        logging.info(str(self.coordinator.host) + ": loop ping init ")
        while True:
            if self.leader:

                for host,port in self.leaders_group:
                    if host != self.coordinator.host and not self.ping(host):
                        self.leaders_group.remove((host,port))

                logging.info(str(self.coordinator.host) +
                             ": the leader_group es " + str(self.leaders_group))
                self.send_election()

            else:
                if not self.ping(self.leader_host):
                    self.send_election()

                if not self.leader:
                    self.send_election_for_leader_group()

            time.sleep(self.sleep_time)

    def add_to_leader(self, host, port):
        if (host,port) not in self.leaders_group:
            self.leaders_group.append((host, port))
            logging.info(str(self.coordinator.host) + ": the leader " +
                         host + " has been append to the group")

    def remove_from_leader(self, host, port):
        if (host, port) in self.leaders_group:
            self.leaders_group.remove((host, port))
            logging.info(str(self.coordinator.host) + ": the leader " +
                         host + " has been remove from the group")

    def set_leader(self, host, socket, cooleader):
        self.leader_host = host

        if self.coordinator.host == host:
            self.leader = True
        else:
            logging.info(str(self.coordinator.host) +
                         ": My leader is " + str(host))
            # logging.info(str(self.coordinator.host) +
            #              ": I'm not the leader")
            if self.leader:
                logging.debug(str(self.coordinator.host) +" entro a soy lider para enviar buffer ")
                self.sinc.send_sinc_to(socket)
            else:
                socket.send(b"no")
                        
            self.leader = False
            self.accepting_connections = False
            if cooleader == "False":
                #Si hay un lider nuevo entonces en un primer momento solo ese lider pertenece al grupo de lideres
                self.in_leader_group = False