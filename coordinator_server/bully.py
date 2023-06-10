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

        self.leader_host = coordinator.host
        # self.leader_host = None TODO este pinchaba en la version estable

        if listen_port is None:
            logging.error(
                f"port used in bully protocol {Bully.DEFAULT_LISTENING_PORT} is busy!")
            exit(1)
        else:
            self.listen_port = listen_port

        self.leaders_group = [(self.coordinator.host, self.coordinator.port)]
        self.sinc = Sinc(coordinator, self, Bully.DEFAULT_LISTENING_PORT)
        self.send_election()

        # self.hashs_dict = {}

    def is_in_k_best_aviables(self, k):
        '''Enviar sennal a los superiores y devuelve si esta entre los k mejores activos'''
        coordinators = self.coordinator.available_coordinator
        count_sup = 0
        for id, (host, port) in coordinators.items():
            if self.coordinator.id > id:
                # TODO aqui ver como se abre un hilo y esa talla, y luego de n segundos hacer decidir si es el jefe
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
            #Las proximas lineas no son necesarias, el deja de ser lider cuando otro se lo ordena, de esta manera se puede hacer bien la sincronizacion.

            # self.leader = False
            # self.coordinator.accepting_connections = False
            return
        old_leader = self.leader_host

        if self.leader == True:
            logging.info(str(self.coordinator.host) + ": I'm the leader again")
            # return
        else:
            # Actualizar el hash porque se cayo un lider superior
            self.sinc.update_hash()

            self.leader = True
            self.coordinator.accepting_connections = True
            self.leader_host = self.coordinator.host
            self.leaders_group = [(self.leader_host, self.coordinator.port)]
            self.in_leader_group = True

            logging.info(str(self.coordinator.host) + ": ******** I'M THE NEW LEADER ********")

        # En un principio por aqui se debe enviar el lider viejo de ambos para el caso de que se cae un lider y entra uno nuevo no intente sincronizarse con un coolider de la misma subred.
        merge_hosts = old_leader + "|"
 
        coordinators = self.coordinator.available_coordinator
        for id, (host, port) in coordinators.items():
            if self.coordinator.id < id:
                socket = utils.connect_socket_to(
                    host, Bully.DEFAULT_LISTENING_PORT, timeout=Bully.TIME_OUT)
                if socket is None:
                    continue
                try:
                    # True o falso indica si a quien le estoy enviando es o no coolider, en caso de serlo no pasa nada, si no lo es entonces debe hacer falsa la variable que lo hace coolider. Esto solo es necesario cuando se cambia el lider, ya que mientras el lider no cambie el control de la variable in_leader_group lo llevan los coolideres. 

                    hosts = [host_ for host_, _ in self.leaders_group]
                    if host in hosts:
                        socket.send(f"leader True {merge_hosts}".encode())
                    else:
                        socket.send(f"leader False {merge_hosts}".encode())

                    buffer = socket.recv(4096)
                    logging.debug(str(self.coordinator.host) +
                                  ": recieve the buffer " + buffer.decode())

                    if (buffer != b"no"):
                        # si a quien envio que ahora soy lider era lider entonces hay que entrar en el proceso de sincronizacion
                        buffer_tuple = buffer.decode().split("|")

                        self.sinc.get_sinc_from(buffer_tuple[0])

                        #Dado que los lideres y coolideres tienen la misma informacion que se debe compartir da igual desde cual se sincronice, luego cada vez que hagamos una sincronizacion guardamos el host con el cual sincronizamos y se lo   pasamos al metodo que se encarga se setear el lider, en ese metodo se revisa que si alguien es lider, o   coolider y ademas no esta reconocido por este nuevo lider, entonces se le pregunta si ya se utilizo el host de    su lider para sincronizar, en caso positivo no se hace nada, en caso negativo se envia un buffer para  sincronizar. Hay otra opcion mas optima y es controlar eso desde este coordinador que esta dando ordenes, es     mejor recibir la informacion de que se ha sincronizado aqui y asi solo se envia un host por la red, la parte    mala de esto es que implica hacer esto para despues llamar la sicronizacion con el buffer. Eso implica que     entre lo que se pide lo ultimo y se va despues a pedir el buffer  para sincronizar entonces se desconecte este  ultimo. Esto ademas solo ocurre en los casos que se necesita hacer el merge, asi que no supone un alto costo     para la red ya que es un caso especifico
                        logging.debug("Esta recibiendo el mensaje de buffer: " + buffer.decode())
                        try:
                            used_host = buffer_tuple[1]
                            merge_hosts+= used_host+"|"    
                            logging.debug("used host: " + str(used_host))
                        except (IndexError):
                            used_host = socket.recv(128)
                            merge_hosts+= used_host.decode("ascii")+"|"    
                            logging.debug("used host: " + str(used_host))



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
            if not self.in_leader_group:
                return
            try:
                socket = utils.connect_socket_to(
                    self.leader_host, Bully.DEFAULT_LISTENING_PORT, timeout=Bully.TIME_OUT)

                if socket is None:
                    logging.info(str(self.coordinator.host) +
                                 ": selection leader socket is None ")
                    return

                logging.info(str(self.coordinator.host) +
                             ": try will remove from leader group")

                socket.send(
                    f"remove_leader_group {self.coordinator.port}".encode("ascii"))
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
            if self.in_leader_group:
                return
            try:
                socket = utils.connect_socket_to(
                    self.leader_host, Bully.DEFAULT_LISTENING_PORT, timeout=Bully.TIME_OUT)

                if socket is None:
                    logging.info(str(self.coordinator.host) +
                                 ": selection leader socket is None ")
                    return

                logging.info(str(self.coordinator.host) +
                             ": try will append to leader group")

                socket.send(
                    f"leader_group {self.coordinator.port}".encode("ascii"))
                is_ok = socket.recv(64)
                if (is_ok == b"ok"):

                    if (not self.in_leader_group):
                        socket.send(b"get_sync")
                        try:
                            recived_buffer = socket.recv(2048)
                            logging.debug(
                                "recibe el buffer del lider: " + str(recived_buffer))
                            self.sinc.sinc_with_leader(recived_buffer)
                            # socket.send(b"ok")
                        except:
                            logging.error(
                                str(self.coordinator.host) + " sync with leader failed")

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
        '''Devuelve si se hace ping, y de hacerse si a quien se hizo ping es o no lider, tupla de (bool,bool)'''
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
            is_ok = socket.recv(128).decode().split()
            if (is_ok[0] == "ok"):
                logging.info(str(self.coordinator.host) +
                             ": recieve ping 'ok' from " + str(host))
                if(is_ok[1] == "leader"):
                    return True,True
                else:
                    return True, False    
            else:
                return False, False
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
                    if(self.leader == True):
                        socket.send(b"ok leader")
                    elif self.in_leader_group == True :
                        socket.send(b"ok cooleader")
                    else:
                        socket.send(b"ok no")

                elif message == "election":
                    # Dice que esta disponible y quien le pregunto entonces no puede ser lider
                    socket.send(b"ok")
                    
                    #TODO aqui hace falta mandar a hacer eleccion al que dice Ok. Con esto se gana que el lider no tenga que estar diciendo todo el tiempo que el es lider
                    # if self.leader:
                    # self.send_election()

                elif message.split()[0] == "leader":
                    # quien esta mandando del otro lado del socket es el lider actual
                    split = message.split()
                    self.set_leader(host, socket, split[1], split[2])

                elif message.split()[0] == "leader_group":
                    # recibe el tag de que quien envia va a pertencer al grupo de lideres secundarios
                    logging.info(str(self.coordinator.host) +
                                 ": recived the peticion leader_group from " + str(host))
                    self.add_to_leader(host, message.split()[1])
                    socket.send(b"ok")

                    logging.debug(
                        "Esperando el mensaje Get_sync de " + str(host))
                    resp = socket.recv(2048).decode('ascii')
                    logging.debug("Recibio el mensaje " +
                                  str(resp)+" de " + str(host))

                    if resp == 'get_sync':
                        logging.debug(
                            "Recibio el mensaje Get_sync de " + str(host))
                        self.sinc.send_sinc_to(socket)

                elif message.split()[0] == "remove_leader_group":
                    # recibe el tag de que quien envia va a ser eliminado del grupo de lideres secundarios
                    self.remove_from_leader(host, message.split()[1])
                    socket.send(b"ok")

            except (TimeoutError, OSError) as e:
                logging.error("Error in receiving_message"+str(e))
            except Exception as e:
                logging.error("*Error in receiving_message "+str(e))

            finally:
                socket.close()

    def loop_ping(self):
        logging.info(str(self.coordinator.host) + ": loop ping init ")

        while True:
            logging.debug("Current Hash: " + str(self.sinc.hash))
            logging.debug("Hash Table Operations: " + str(utils.commands_logs(self.sinc.logs_dict)))
        
            if self.leader:

                for host, port in self.leaders_group:
                    pin = self.ping(self.leader_host)
                    if host != self.coordinator.host and not pin[0]:
                        self.leaders_group.remove((host, port))

                logging.info(str(self.coordinator.host) +
                             ": the leader_group es " + str(self.leaders_group))
                self.send_election()

            else:
                pin = self.ping(self.leader_host)
                #Si el lider deja de ser lider entonces hay que hacer proceso de seleccion, dado que la entrada de un tipo nuevo que no es lider que se conecto a la red y es mejor que el lider implica que el lider deje de ser lider pero el nuevo que entra no sabe que tiene que hacer proceso de seleccion.
                
                # TODO El tipo que entra nuevo tratara de hacer ping a su lider y no lo encontrara, al pasar esto hara un proceso de eleccion y de esta forma le dice a todos que el es el nuevo lider. Luego => linea Comentada

                if not pin[0]: #or not pin[1]:
                    self.send_election()

                if not self.leader:
                    self.send_election_for_leader_group()

            time.sleep(self.sleep_time)

    def add_to_leader(self, host, port):
        if (host, port) not in self.leaders_group:
            self.leaders_group.append((host, port))
            logging.info(str(self.coordinator.host) + ": the leader " +
                         host + " has been append to the group")

    def remove_from_leader(self, host, port):
        if (host, port) in self.leaders_group:
            self.leaders_group.remove((host, port))
            logging.info(str(self.coordinator.host) + ": the leader " +
                         host + " has been remove from the group")

    def set_leader(self, host, socket, cooleader, used_hosts):
        #esto es para definir si el alguien de esta subred ya ha hecho merge con el nuevo lider
        used_hosts_array = used_hosts.split("|")
        used_contain_leader = self.leader_host in used_hosts_array
        sender_buff = False

        logging.info(str(self.coordinator.host) +
                     ": My leader is " + str(host))
        if self.leader:

            #TODO aqui hay que mandar al nuevo lider que ya hice merge con el, y decirle que guarde en su diccionario en mi llave el mismo host como value, de esta forma despues se pregunta por los coolideres y solo se actualiza en caso
            if not used_contain_leader:
                logging.debug(str(self.coordinator.host) +
                          " entro a soy lider y no ha sido usado mi host para enviar buffer ")
                self.sinc.send_sinc_to(socket)
                socket.send(f"|{self.leader_host}".encode())
                used_contain_leader = True
                sender_buff = True

            # else:
            #     socket.send(b"no")    
        
        self.leader = False
        self.accepting_connections = False

        if cooleader == "False":
            if self.in_leader_group:
                # Si el lider actual no te cuenta como coolider entonces quiere decir que no estan sincronizados, puede entonces pedir sincronizacion a este coolider(self) en caso de que el lider viejo u otro coordinador con la misma informacion no haya sido utilizado para sincronizarse. Para ello esto se debe recibir un buffer aqui con todos los hosts que han sido utilizados para sincronizar

                #TODO mandar por el socket el host de mi lider
                if not used_contain_leader:
                    logging.debug(str(self.coordinator.host) +
                          " entro a soy coolider de unared sin lider para enviar buffer a una subred distinta")
                    self.sinc.send_sinc_to(socket)
                    socket.send(f"|{self.leader_host}".encode())
                    # used_contain_leader = True
                elif not sender_buff:
                    socket.send(b"no")
            elif not sender_buff:
                socket.send(b"no")
        
            # Si hay un lider nuevo entonces en un primer momento solo ese lider pertenece al grupo de lideres
            self.in_leader_group = False
        
        elif not sender_buff:
            socket.send(b"no")


        self.leader_host = host
