import socket
import time
import random
import threading
from multiprocessing.pool import ThreadPool
import json

from queue import Queue

import logging


from . import remote_operations 
from . import bully

import utils
import discoverer

from typing import Literal, Callable, TypedDict

class FTPDescriptor(TypedDict):
    host: str 
    port: int 
    last_operations_id: dict[int,int]

class Coordinator:
    TOTAL_THREADS = 10
    def __init__(self,id , host, port, refresh_time) -> None:
        self.discoverer = discoverer.Discoverer(
            id,
            'coordinator',
            (host, port))

        self.id = id
        self.host = host
        self.port = port

        self.available_ftp: dict[str, FTPDescriptor]={} 
        self.available_coordinator={}

        self.refresh_time = refresh_time
        self.ftp_tree= {}# 'hash': 'ftps': 'type': 'deleted':
            
        self.new_operations = Queue() 
        self.operations_to_do = Queue()
        self.accepting_connections = False 

        # protocolo de seleccion de lider bully
        self.bully_protocol = bully.Bully(self) 
        self.sync = self.bully_protocol.sinc 

    def _get_avalible_nodes(self,
                                type_: Literal['ftp', 'coordinator']
                                ):

        return self.discoverer.get_registered_nodes(type_)


    def _refresh_nodes(self):
        self.discoverer.send_identify_broadcast()
        time.sleep(2)
        self._refresh_coordinator_nodes()
        self._refresh_ftp_nodes()

    def _refresh_coordinator_nodes(self):
        """Toma todos los servidores coordinadores y filtra los validos"""

        coordinator_nodes_in_name_server: dict[str, tuple[str,int]]= self.\
                                                                _get_avalible_nodes('coordinator')

        valid_coords = {}
        for name,coord_addr in coordinator_nodes_in_name_server.items():  
            if name == self.id:
                continue
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(5) 
                    s.connect(coord_addr)
                    #loggin.debug(f"sending ping to {name}")
                    s.send(bytes(f"{self.id} PING", encoding='ascii'))
                    
                    if s.recv(256).decode().upper() == 'OK':
                        valid_coords[name] = coord_addr
                    else: 
                        # esto nunca deberia de pasar :D
                        pass
                    
            except (ConnectionError, TimeoutError, OSError):
                pass
            pass

        self.available_coordinator = valid_coords

    def _refresh_ftp_nodes(self):
        """
        Toma todos los servidores ftp en el servidor de nombres y comprueba conectividad
        ,filtra los validos y los guarda y manda a elminar los invalidos en el ns. 
        """

        #logging.debug("Current Hash: " + str(self.bully_protocol.sinc.hash))
        #logging.debug(f"Hash Table Operations: { { key:len(value) for key, value in  self.bully_protocol.sinc.logs_dict.items()} }")


        if not self.accepting_connections:
            return

        #loggin.debug("refreshing ftp")
        ftp_nodes_in_name_server: dict[str, tuple[str,int]]= self._get_avalible_nodes('ftp')
        valid_ftp: dict[str, FTPDescriptor] = {} 
        exist_changes= False 
        try:
            for name,ftp_addr in ftp_nodes_in_name_server.items():  
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.settimeout(5) 
                        s.connect(ftp_addr)
                        #se comprueba que el servidor ftp este aceptando conexiones

                        if s.recv(2048).decode('ascii').split(' ')[0] == '220':

                            remote_operations.login('admin', s)

                            s.send(f"SETCOORD {self.port}".encode('ascii'))
                            resp_code, *_ =s.recv(2048).decode('ascii').split(' ')


                            if resp_code == '200':
                                # ademas mandamos los IPs de los co_coordinadores

                                s.send('CLEARCOCOORD'.encode('ascii'))
                                s.recv(126)
                                for co_host, co_port in self.bully_protocol.leaders_group:
                                    s.send(f'ADDCOCOORD {co_host} {co_port}'.encode('ascii'))
                                    s.recv(126)
                                
                                
                                current_ftp = FTPDescriptor(
                                    host=ftp_addr[0],
                                    port=ftp_addr[1],
                                    last_operations_id={})
                                """ for hash in self.bully_protocol.sinc.logs_dict:
                                    s.send(f"LASTFROMHASH {hash}".encode('ascii'))
                                    response=s.recv(512).decode().split()
                                    _resp_code,last_operation,*_=response

                                    last_operation = int(last_operation)
                                    current_ftp['last_operations_id'][hash] = last_operation
                                    self._add_operations_to_do(last_operation_in_ftp=last_operation,
                                                            hash=hash,
                                                            ftp_name=name) """

                                valid_ftp[name] =  current_ftp

                                if name not in self.available_ftp:
                                    exist_changes = True 
                            else:
                                raise ConnectionError('Bad Connection')
                        else:
                            raise ConnectionError('Bad Connection')
                        s.send(b'QUIT')
                except (TimeoutError, OSError, ConnectionError) as e:
                    exist_changes = True 
                    logging.info(f'{e}::Removing ftp server {name}.')
                    pass
                
            if exist_changes:
                logging.info(f"Total current FTPs: {len(valid_ftp)}")
                pass
        except:
            logging.error("Error aleatorio mientras se actualizaban los ftps")
            return 
        self.available_ftp = valid_ftp 
        logging.debug(f"Current available FTPs:{utils.last_ftp_operations(valid_ftp)}")

    # def _add_operations_to_do(self, last_operation_in_ftp: int, hash: int ,ftp_name: str):
    #     for index in range(last_operation_in_ftp,
    #                        len(self.bully_protocol.sinc.logs_dict.setdefault(hash,[]))):
    #         self.operations_to_do.put((index, hash, ftp_name))
        
    def _refresh_loop(self,func: Callable, wait_time: int):
        while True:
            func()
            time.sleep(wait_time)


    def _get_ftp_with_data(self, hash: int, operation_id: int):
        posibles= [ key for key, ftp in self.available_ftp.items()
                    if ftp['last_operations_id'].setdefault(hash,0) > operation_id ] 
        if len(posibles) > 0 :
            return posibles[random.randint(0,len(posibles)-1)]
        return None

    def _handle_conn(self, conn: socket.socket, addr):

        conn.settimeout(10)
        try:
            request=conn.recv(1024).decode('ascii')
            request=request.split()
            print(request)
            node_id = request.pop(0)
            request[0]=request[0].upper()
            match request:
                case ["PING", *args]:
                    conn.send(b'ok')
                case ["GET_TREE"]:
                    tree_serialized=json.dumps(self.ftp_tree)
                    conn.send(tree_serialized.encode())
                case ["ADD_TO_TREE",port,type_, *path]:
                    path_value=self.ftp_tree[" ".join(path)]={
                        "type":type_,
                        "ftps":[(addr[0], int(port))],
                        "hash": self.sync.hash,
                        "deleted":False
                    }
                case ["ADD_FTP_TO_PATH", port, *path]:
                    self.ftp_tree[" ".join(path)]['ftps'].append((addr[0], int(port)))

                case ["REMOVE_FROM_TREE", *path]:
                    try:
                        path = " ".join(path)
                        print(">>>>>>",path)
                        self.ftp_tree[path]['deleted'] = True
                        self.ftp_tree[path]['ftps'] = []
                    except (KeyError) as e:
                        # no problemo :D
                        logging.error(f"ERROR refreshing the tree (REMOVE_FROM_TREE) {e}")
                        pass
                    except:
                        logging.error("Error in Remove")
                        

            #self.new_operations.put((node_id, request))
            #logging.info(f'new_operations:{self.new_operations.queue}')

        except TimeoutError:
            logging.error(f"Connection Timeout {addr}")
        except Exception as e: 
            logging.error(f"OTRO ERROR:{e}" )
        finally:
            conn.close()

    def run(self):
        
        if not self.discoverer.is_remote:
            self.discoverer.start_discovering()

        threading.Thread(target=self._refresh_loop,args=(self._refresh_nodes, self.refresh_time)).start()

        threading.Thread(target=self.bully_protocol.receive_message,args=()).start()
        threading.Thread(target=self.bully_protocol.loop_ping,args=()).start()


        if  (s:=utils.create_socket_and_listen(self.host, self.port)) and s is not None:
            with s: 
                logging.info("Server Starting")
                with ThreadPool(processes=Coordinator.TOTAL_THREADS) as thread_pool:
                    while True:
                        conn, addr = s.accept()
                        thread_pool.apply_async(self._handle_conn, args=(conn,addr))
        else: 
            logging.error(f"error creating the socket in port {self.port}.")
            exit(1)

    
if __name__ == '__main__':
    pass
