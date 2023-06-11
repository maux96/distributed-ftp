
import socket
import threading 
import time
import logging

from typing import TypedDict, Literal




class NodeInfo(TypedDict):
    host: str
    port: int
    type: Literal['ftp', 'coordinator']

class Discoverer:
    def __init__(self, id: str, current_node_info: NodeInfo, udp_broadcast_port=16000, reciving_port=16001) -> None:

        # node properties
        self.id = id
        self.host=current_node_info['host']
        self.port=current_node_info['port']
        self.type=current_node_info['type']

        # discoverer ports
        self.udp_port=udp_broadcast_port
        self.reciving_port= reciving_port


        # discovered nodes info
        self.table: dict[str,NodeInfo] = {}

    def udp_listener(self):
        # broadcast messages reciver

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
            udp_socket.bind((self.host,self.udp_port))
            while True: 
                message, addr=udp_socket.recvfrom(1024)
                if addr[0] == self.host:
                    continue
                command, host, port= message.decode().split()
                print(f"Recibed Broadcast message '{command}' from '{host}'")
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.connect((host, int(port)))
                    sock.send(f'{self.id} {self.type} {self.port}'.encode())


    def send_identify_broadcast(self):

        message = f"IDENTIFY {self.host} {self.reciving_port}"
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
            udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

            udp_socket.settimeout(1.0)
            udp_socket.sendto(message.encode(), ('<broadcast>', self.udp_port))

            time.sleep(10) 


    def register_listener(self):

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind((self.host, self.reciving_port))
            sock.listen()
            while True: 
                conn, addr=sock.accept()
                id,type_,port =conn.recv(1024).decode().split()
                if type_ != 'ftp' or type_ != 'coordinator':
                    logging.warning(f"Wrong type recived by discover ({type_})")
                    continue

                self.table[id] = NodeInfo( 
                    host=addr[0],
                    port=int(port),
                    type=type_,
                )

                logging.debug(f"Registered addr {self.table[id]} as {id}")


#  print("Listening ports") 
#  id, host, port = input('id:'), input('host:'), int(input('port:'))

#  threading.Thread(target=udp_listener, args=(id, host, port)).start()
#  threading.Thread(target=register_listener, args=(host, port)).start()
#  broadcast_sender(host, port)




