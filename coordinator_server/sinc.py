import logging
import json

class Sinc:
    def __init__(self, coordinator, bully, host):
        self.DEFAULT_LISTENING_PORT = host
        self.coordinator = coordinator
        self.bully = bully
        self.logs_dict: dict[int, list] = {}
        self.tree = coordinator.ftp_tree

    def get_sinc_from(self, buffer):
        recieved_tree = json.loads(buffer)
        for dir in recieved_tree.keys():
            if dir not in self.tree:
                self.coordinator.ftp_tree[dir] = recieved_tree.value()    

        logging.info(str(self.coordinator.id) +
                     ": sync success: \n" + str(self.tree))

    def send_sinc_to(self, socket):
        if socket is None:
            logging.error("Esta tratando de enviar informacion con socket None")
            return
        try:
            to_send = self.tree
            to_send = json.dumps(to_send)
            socket.send(bytes(to_send, encoding='ascii'))
        except:
            pass

    def sinc_with_leader(self, buffer):
        recieved_tree = json.loads(buffer.decode())
        for dir in recieved_tree.keys():
            if dir not in self.tree:
                self.coordinator.ftp_tree[dir] = recieved_tree.value()    