
import socket
import threading 
import time
import logging

from typing import  Literal

class Discoverer:
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
                logging.debug(f"Recibed Broadcast message '{command}' from '{host}'")
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.connect((host, int(port)))
                    sock.send(f'{self.id} {self.type} {self.port}'.encode())


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
                if type_ == 'ftp':
                    table_to_use = self.ftp_table
                elif type_ == 'coordinator':
                    table_to_use = self.coordinator_table

                else:
                    logging.warning(f"Wrong type recived by discover ({type_})")
                    continue

                table_to_use[id] = (addr[0],int(port))

                logging.debug(f"Registered addr {table_to_use[id]} as {id}")

    def start_discovering(self):
        threading.Thread(target=self.udp_listener).start()
        threading.Thread(target=self.register_listener).start()
        logging.info("Starting Discoverer!") 

#  print("Listening ports") 
#  id, host, port = input('id:'), input('host:'), int(input('port:'))

#  threading.Thread(target=udp_listener, args=(id, host, port)).start()
#  threading.Thread(target=register_listener, args=(host, port)).start()
#  broadcast_sender(host, port)




