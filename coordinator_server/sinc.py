class Sinc:
    def __init__(self, coordinator, bully):
        self.coordinator = coordinator
        self.bully = bully

    def get_sinc_from_coord(self, host):
        logging.info(str(self.coordinator.id) + ": sinc from " + host)

        if host is None:
            return Exception("Esta tratando de sincronizar desde un host None")

        socket = utils.connect_socket_to(host, Bully.DEFAULT_LISTENING_PORT)
        if socket is None:
            return Exception("Esta tratando de sincronizar desde un socket None")
        try:
            socket.settimeout(3)
            socket.send(b"get_sinc")
            is_ok = socket.recv(64)
            if (is_ok == b"ok"):
                logging.info(str(self.coordinator.id) +
                             ": recieve sinc from " + str(host))
        except:
            pass

    def set_sinc_to_coord(self, host):
        logging.info(str(self.coordinator.id) + ": sinc to " + host)

        if host is None:
            return Exception("Esta tratando de sincronizar hacia un host None")

        socket = utils.connect_socket_to(host, Bully.DEFAULT_LISTENING_PORT)
        if socket is None:
            return Exception("Esta tratando de sincronizar hacia un socket None")
        try:
            socket.settimeout(3)
            socket.send(b"set_sinc")
            is_ok = socket.recv(64)
            if (is_ok == b"ok"):
                logging.info(str(self.coordinator.id) +
                             ": send sinc to " + str(host))
        except:
            pass

    def send_sinc_to(self, host):
        logging.info(str(self.coordinator.id) + ": sending info to " + host)

        if host is None:
            return Exception("Esta tratando de enviar informacion a un host None")

        socket = utils.connect_socket_to(host, Bully.DEFAULT_LISTENING_PORT)
        if socket is None:
            return Exception("Esta tratando de enviar informacion con socket None")
        try:
            buffer = ""

            socket.settimeout(3)
            socket.send("data_sinc " + buffer)
            is_ok = socket.recv(64)
            if (is_ok == b"ok"):
                logging.info(str(self.coordinator.id) +
                             ": send full info to " + str(host))
        except:
            pass

    def recieve_sinc(self, message):
        # recibir todo el puto buffer y ponerlo
        logging.info(str(self.coordinator.id) +
                     ": recieve the buffer "+message+" for sinc from" + str(host))
