from typing import Literal

import logging
import socket
import threading
import json
import random

import utils

REGISTER_STR='REGISTER'
GET_STR='GET'
GET_TYPES_STR='GET_TYPES'
LOCATE_STR='LOCATE'

class NameServer:

    @staticmethod
    def locate_name_server(port_for_broadcast: int, timeout_time=1.0):
        wait_for_response_port=random.randint(20_000, 30_000)


        if (soc:=utils.create_socket_and_listen('',wait_for_response_port))\
                and soc is not None:

            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
                udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

                udp_socket.settimeout(timeout_time)
                
                message = f"{LOCATE_STR} {wait_for_response_port}"
                udp_socket.sendto(message.encode(),
                                  ('<broadcast>', port_for_broadcast))
                pass


            conn,(addr, _)=soc.accept()
            _,name_server_port=conn.recv(512).decode().split()

            return (addr, name_server_port) 

        return NameServer.locate_name_server(port_for_broadcast, timeout_time)

    @staticmethod
    def get_nodes(addr: tuple[str, int], type_: Literal['ftp', 'coordinator']):
        if (soc:=utils.connect_socket_to(*addr)) and soc is not None:
            soc.send(f'{GET_TYPES_STR} {type_}'.encode())

            # ver si es necesario estar leyendo hasta que se cierre el socket
            data=json.loads(soc.recv(2048))

            return data 

    def __init__(self, 
                 id: str,
                 addr: str,
                 port: int,
                 udp_reciever_port=16000,
    ) -> None:

        self.id = id
        self.host=addr
        self.port=port
        self.udp_port_reciever=udp_reciever_port

        self.ftp_table: dict[str,tuple[str,int]] = {}
        self.coordinator_table: dict[str,tuple[str,int]] = {}

    def udp_listener(self):

        logging.info("Starting NameServer Broadcast Listener")
        
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
            udp_socket.bind(('',self.udp_port_reciever))
            while True:
                try:
                    message, (addr,_) = udp_socket.recvfrom(512)
                    message, node_port = message.split()
                    if message == LOCATE_STR and\
                      (soc := utils.connect_socket_to(addr, int(node_port)))\
                      and soc is not None:
                            with soc:
                                soc.send(f'NSPORT {self.port}'.encode())   
                except (TimeoutError):
                    logging.warning('Timeout telling the address')
                            

    def handle_conn(self, conn, addr: tuple[str, int]):
        message = conn.recv(512)  

        try:
            match message.decode().split():
                case [REGISTER_STR , 'ftp' | 'coordinator' as type_, id, port]:
                    getattr(self,type_+'_table')[id]=(addr[0], port)

                case [GET_TYPES_STR, 'ftp' | 'coordinator' as type_]:
                    to_send = json.dumps(getattr(self,type_+'_table'))
                    conn.send(to_send.encode())
                
                case [GET_STR, id]:
                    if id in self.ftp_table:
                        conn.send(json.dumps(self.ftp_table[id]).encode())  
                    elif id in self.coordinator_table:
                        conn.send(
                            json.dumps(self.coordinator_table[id]).encode())  
                    else:
                        logging.warning(f"Name {id} not founded in NameServer!")
                case _:
                    logging.warning(f"Not valid command recived from {addr}")

        except:
            logging.error("EXCEPTION IN NAMESERVER")

        finally:
            conn.close()

    def run(self):
        threading.Thread(target=self.udp_listener).start()

        if (soc := utils.create_socket_and_listen(self.host, self.port))\
                and soc is not None:
            while True:
                conn, addr =soc.accept()
                self.handle_conn(conn, addr)    
