import logging
import json
import random

import utils

def create_random_hash():
    return random.randint(5_000, 1_000_000_000)
class Sinc:
    def __init__(self, coordinator, bully, host):
        self.DEFAULT_LISTENING_PORT = host
        self.coordinator = coordinator
        self.bully = bully
        self.logs_dict = {}
        self.hash = create_random_hash()

    def update_hash(self):
        self.hash = create_random_hash()

    def get_sinc_from(self, buffer):
        logging.info(str(self.coordinator.id) + ": sinc the buffer " + buffer.decode())

        info = json.loads(buffer.decode())
        hash = info["hash"]
        logs = info["logs_dict"]

        merge = False
        for log in logs:
            if log not in self.logs_dict:
                self.logs_dict[log] = logs[log]

            if len(self.logs_dict[log]) != len(logs[log]):
                if len(self.logs_dict[log]) < len(logs[log]):
                    self.logs_dict[log] = logs[log]
                else:
                    # Si el log del nuevo lider es mayor que el viejo, este lider estuvo trabajando por otra rama, Notese que ambos
                    # no pueden escribir sobre el mismo hash, luego un hash solo es modificable desde una subred y nunk desde dos al
                    # mismo tiempo
                    merge = True

        for log in self.logs_dict:
            if log not in logs:
                # Si el nuevo lider tiene un log que no tiene el viejo entonces se hicieron modificaciones por otra subred usando
                # lider nuevo
                merge = True

        if not merge:
            self.hash = hash
        else:
            self.update_hash()

        logging.info(str(self.coordinator.id) +
                     ": sync success: \n" + str(self.logs_dict))

    def send_sinc_to(self, socket):
        logging.info(str(self.coordinator.id) + ": sending info for sync")

        if socket is None:
            logging.error("Esta tratando de enviar informacion con socket None")
            return
        try:
            to_send = {
                "hash": self.hash,
                "logs_dict": self.logs_dict
            }
            logging.debug("send:" + str(to_send))            
            to_send = json.dumps(to_send)
            socket.send(bytes(to_send, encoding='ascii'))
            
        except:
            pass

    def sinc_with_leader(self, buffer):
        # recibir todo el puto buffer y ponerlo
        logging.info(str(self.coordinator.id) +
                     ": recieve the buffer "+str(buffer)+" for sinc")
                     
        info = json.loads(buffer.decode())
        hash = info["hash"]
        logs = info["logs_dict"]
        self.logs_dict = logs #TODO ver como funciona el decodificador de este json, a ver si pincha bien
        self.hash = hash #TODO ver como funciona el decodificador de este json, a ver si pincha bien
             
