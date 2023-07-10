
import socket
import threading 
import time
import logging
import json

from typing import  Literal

import utils

class Discoverer:

    def is_discoverer_created(self):
        if (soc:=utils.connect_socket_to(self.host, self.reciving_port)) and soc is not None: 
            soc.send(f'{self.id} registerlocal_{self.type} {self.port}'.encode())
            return True
        return False 

    def get_registered_nodes(self, type_: Literal['ftp', 'coordinator']):
        if self.is_remote:
            if (soc:=utils.connect_socket_to('localhost', self.reciving_port)) and soc is not None: 
                soc.send(f'{self.id} get_{type_} {-1}'.encode())
                recived_obj: dict[str, tuple[str, int]]=json.loads(soc.recv(2048))

                return recived_obj
            else: 
                logging.error("Error in Discoverer asking for registered nodes.")

        return getattr(self, f'{type_}_table')

    def __init__(self, 
                 id: str,
                 type_: Literal['ftp', 'coordinator'],
                 addr: tuple[str,int],
                 udp_broadcast_port=16000,
                 reciving_port=16001) -> None:

        # node properties
        self.id = id
        self.host=addr[0]
        self.port=addr[1]
        self.type=type_

        # discoverer ports
        self.udp_port=udp_broadcast_port
        self.reciving_port= reciving_port

        # discovered nodes info
        self.ftp_table: dict[str,tuple[str,int]] = {}
        self.coordinator_table: dict[str,tuple[str,int]] = {}
        

        self.is_remote=self.is_discoverer_created()
        self.others: list[tuple[str, str, int]] = []

    def udp_listener(self):
        # broadcast messages reciver
        logging.info("Starting Discoverer Broadcast Listener")
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
            udp_socket.bind(('',self.udp_port))
            while True: 
                message, addr=udp_socket.recvfrom(1024)
                if addr[0] == self.host:
                    continue
                command, host, port= message.decode().split()
                #logging.debug(f"Recibed Broadcast message '{command}' from '{host}'")
                for registered_id,registered_type,registered_port in [(self.id,self.type,self.port), *self.others]:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                        sock.connect((host, int(port)))
                        sock.send(f'{registered_id} {registered_type} {registered_port}'.encode())


    def send_identify_broadcast(self):
        logging.debug("Broadcasting discover message!")
        message = f"IDENTIFY {self.host} {self.reciving_port}"
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
            udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

            udp_socket.settimeout(1.0)
            udp_socket.sendto(message.encode(), ('<broadcast>', self.udp_port))
            #udp_socket.sendto(message.encode(), ('255.255.255.0', self.udp_port))



    def register_listener(self):
        logging.info("Starting Discoverer Listener")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind((self.host, self.reciving_port))
            sock.listen()
            while True: 
                conn, addr=sock.accept()
                id,type_,port =conn.recv(1024).decode().split()
                match type_.split('_'):
                    case ['ftp']:
                        self.ftp_table[id]=(addr[0],int(port))
                    case ['coordinator']:
                        self.coordinator_table[id]=(addr[0],int(port))
                    case ['get', 'ftp']:
                        conn.send(json.dumps(self.ftp_table).encode()) 
                    case ['get', 'coordinator']:
                        conn.send(json.dumps(self.coordinator_table).encode()) 
                    case ['registerlocal','ftp']:
                        self.ftp_table[id] = (self.host, int(port))
                        self.others.append((id,'ftp',int(port)))
                    case ['registerlocal','coordinator']:
                        self.coordinator_table[id] = (self.host, int(port))
                        self.others.append((id,'coordinator',int(port)))
                    case _:
                        logging.warning(f"Wrong instruction recived by discover ({type_})")
                        continue

                #logging.debug(f"Registered addr {table_to_use[id]} as {id}")

    def start_discovering(self):
        threading.Thread(target=self.udp_listener).start()
        threading.Thread(target=self.register_listener).start()

        getattr(self, f'{self.type}_table')[self.id]= (self.host, self.port)
        logging.info("Starting Discoverer!") 

#  print("Listening ports") 
#  id, host, port = input('id:'), input('host:'), int(input('port:'))

#  threading.Thread(target=udp_listener, args=(id, host, port)).start()
#  threading.Thread(target=register_listener, args=(host, port)).start()
#  broadcast_sender(host, port)




