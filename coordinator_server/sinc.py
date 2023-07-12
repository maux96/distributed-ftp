import logging
import json
import random

def create_random_hash():
    return random.randint(5_000, 1_000_000_000)

class Sinc:
    def __init__(self, coordinator, bully, host):
        self.DEFAULT_LISTENING_PORT = host
        self.coordinator = coordinator
        self.bully = bully
        self.tree = coordinator.ftp_tree
        self.hash = create_random_hash()
    
    def update_hash(self):
        self.hash = create_random_hash()

    def get_sinc_from(self, buffer):
        recieved_tree = json.loads(buffer) ['tree']
        merge = False

        for dir in recieved_tree.keys():
            if dir not in self.tree:
                self.coordinator.ftp_tree[dir] = recieved_tree[dir]
                merge = True    
            else:
                if recieved_tree[dir]['deleted'] and not self.coordinator.ftp_tree[dir]['deleted']:
                    #Si se elimino el archivo en otra subred y no se elimino en esta 
                    if recieved_tree[dir]['hash'] == self.coordinator.ftp_tree[dir]['hash']:
                        #si el hash es el mismo, es decir es el mismo archivo dado que se crearon en la misma subred en cierto momento entonces esta direccion se debe 'eliminar'
                        recieved_tree[dir]['deleted'] = True
                        merge = True    
                        #luego ya no tengo que volver a tratar con este archivo 
                        continue

                if  self.coordinator.ftp_tree[dir]['deleted'] and not recieved_tree[dir]['deleted']:
                    # Si esta eliminada una ruta en esta subred y no lo esta en la otra, entonces hay que mantenerla o no eliminada segun lo que se hizo en la subred de la cual se esta sincronizando
                    if recieved_tree[dir]['hash'] != self.coordinator.ftp_tree[dir]['hash']:
                        # Si el hash es distinto entonces el momento de creacion de un archivo y otro fue distinto, luego no es el mismo archivo resultante de la subdivicion de la red, entonces me interesa la informacion del archivo nuevo que estoy sincornizando
                        self.coordinator.ftp_tree[dir] = recieved_tree[dir]
                        merge = True    
                        #luego ya no tengo que volver a tratar con este archivo 
                        continue

                if self.coordinator.ftp_tree[dir]['hash'] == recieved_tree[dir]['hash']:
                    #Si esto pasa lo ideal es que se conserven ambos archivos, esta pasando que hay dos archivos distintos o al menos creados por suredes distintas que poseen el mismo path
                    pass

                for item in recieved_tree[dir]:
                    for ftp in item['ftps']:
                        if ftp not in self.coordinator.ftp_tree[dir]['ftps']:
                            #Si no esta un ftp asociado a este archivo que si esta otra red llamar este
                            self.coordinator.ftp_tree[dir]['ftps'].append(ftp)
                            merge = True
                if merge:
                    #Si hay merge hay que updatear el hash para evitar conflictos y trabajar sobre un hash nuevo
                    self.update_hash()

        logging.info(str(self.coordinator.id) +
                     ": sync success: \n" + str(self.coordinator.ftp_tree))

    def send_sinc_to(self, socket):
        if socket is None:
            logging.error("Esta tratando de enviar informacion con socket None")
            return
        try:
            to_send = {'hash': self.hash, 'tree':self.tree }
            to_send = json.dumps(to_send)
            socket.send(bytes(to_send, encoding='ascii'))
        except:
            pass

    def sinc_with_leader(self, buffer):
        info = json.loads(buffer.decode())
        recieved_tree = info['tree']
        
        #cuando se sincroniza con el lider hereda su hash
        self.hash = info['hash']

        #como se esta coordinando con el lider nos interesa que tome exactamente lo que tiene el lider, luego se limpia el tree de este coordinador y se replica exactamente igual al del lider. En caso que se tenga informacion relevante, se controla a nivel de secronizar desde el lider.
        self.coordinator.ftp_tree = {}
        for dir in recieved_tree.keys():
            self.coordinator.ftp_tree[dir] = recieved_tree.value()    