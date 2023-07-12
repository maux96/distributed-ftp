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
            else:
                for _,ftps in recieved_tree[dir]:
                    for ftp in ftps:
                        if ftp not in self.coordinator.ftp_tree[dir]['ftps']: #TODO Arreglar esto donde se crea el ft_tree
                            #Si no esta un ftp asociado a este archivo que si esta otra red llamar este
                            self.coordinator.ftp_tree[dir]['ftps'].append(ftp)

        logging.info(str(self.coordinator.id) +
                     ": sync success: \n" + str(self.coordinator.ftp_tree))

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
        #como se esta coordinando con el lider nos interesa que tome exactamente lo que tiene el lider, luego se limpia el tree de este coordinador y se replica exactamente igual al del lider
        self.coordinator.ftp_tree = {}
        for dir in recieved_tree.keys():
            self.coordinator.ftp_tree[dir] = recieved_tree.value()    