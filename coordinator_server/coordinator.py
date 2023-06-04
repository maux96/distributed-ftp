import socket
import time
import random
import threading
from multiprocessing.pool import ThreadPool

from queue import Queue

import logging

import ns_utils

from . import remote_operations 
from . import bully
import utils

from typing import Literal, Callable, TypedDict

class FTPDescriptor(TypedDict):
    host: str 
    port: int 
    last_operations_id: dict[str,int]

class Coordinator:
    TOTAL_THREADS = 10
    def __init__(self,id , host, port, refresh_time) -> None:
        self.id = id
        self.host = host
        self.port = port

        self.available_ftp: dict[str, FTPDescriptor]={} 
        self.available_coordinator={}

        self.refresh_time = refresh_time
        self.ftp_tree= {}

        self.new_operations = Queue() 
        self.operations_to_do = Queue()
        self.accepting_connections = False 

        # operaciones realizadas
        #self.operations_log: list[tuple[str, list]] = []
        #self.base_last_opertation = 0
        #self.last_operation = 0

        # protocolo de seleccion de lider bully
        self.bully_protocol = bully.Bully(self) 

    def _get_avalible_nodes(self,
                                type: Literal['ftp', 'coordinator']
                                ):
        return ns_utils.ns_lookup_prefix(type)

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
        if not self.accepting_connections:
            return

        #loggin.debug("refreshing ftp")
        ftp_nodes_in_name_server: dict[str, tuple[str,int]]= self._get_avalible_nodes('ftp')
        valid_ftp: dict[str, FTPDescriptor] = {} 
        exist_changes= False 
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
                        #loggin.debug(f"name:{name} | rs:{resp_code} | last_id:{last_operation} | last_global:{self.last_operation}")


                        if resp_code == '200':
                            # mandamos el hash asociado al liderazgo actual
                            #s.send(f"SETCURRENTHASH {self.bully_protocol.sinc.hash}".encode('ascii'))
                            #resp_code,_ =s.recv(2048).decode('ascii').split(' ')
                             
                            current_ftp = FTPDescriptor(
                                host=ftp_addr[0],
                                port=ftp_addr[1],
                                last_operations_id={})
                            for hash in self.bully_protocol.sinc.logs_dict:
                                logging.debug(f">>>>> {hash}")
                                s.send(f"LASTFROMHASH {hash}".encode('ascii'))
                                response=s.recv(512).decode().split()
                                logging.debug(f">>>>> {response}")
                                _resp_code,last_operation,*_=response

                                last_operation = int(last_operation)
                                current_ftp['last_operations_id'][hash] = last_operation
                                self._add_operations_to_do(last_operation_in_ftp=last_operation,
                                                           hash=hash,
                                                           ftp_name=name)

                            valid_ftp[name] =  current_ftp


                            #last_operation = int(last_operation)

                           #valid_ftp[name] =  FTPDescriptor(
                           #    host=ftp_addr[0],
                           #    port=ftp_addr[1],
                           #    last_operation_id=last_operation) 

                            # registramos las operaciones que se van a replicar
                            # basados en la ultima operacion del ftp
                            #self._add_operations_to_do(last_operation, ftp_name=name)

                            if name not in self.available_ftp:
                                exist_changes = True 
                                #logging.info(f'New ftp server {name}::{ftp_addr}')
                            #else:
                                # toma el maximo entre el valor que tiene el coordinador
                                # y el que tiene el propio ftp
                               #valid_ftp[name]['last_operation_id']=max(
                               #    last_operation,
                               #    self.available_ftp[name]['last_operation_id'])

                        else:
                            raise ConnectionError('Bad Connection')
                    else:
                        raise ConnectionError('Bad Connection')
                    s.send(b'QUIT')
            except (TimeoutError, OSError, ConnectionError) as e:
                # en caso de que no se logre conectark
                #ns_utils.ns_remove_name(f"ftp_{name}")
                exist_changes = True 
                #logging.info(f'{e}::Removing ftp server {name}.')
                pass
            
        #loggin.debug("end refreshing with count = " +str(len(valid_ftp)))            
        if exist_changes:
            #logging.info(f"Total current FTPs: {len(valid_ftp)}")
            pass
        self.available_ftp = valid_ftp 

    def _add_operations_to_do(self, last_operation_in_ftp: int, hash: str ,ftp_name: str):
        for index in range(last_operation_in_ftp,
                           len(self.bully_protocol.sinc.logs_dict.setdefault(hash,[]))):
            self.operations_to_do.put((index, hash, ftp_name))
        
    def _refresh_loop(self,func: Callable, wait_time: int):
        while True:
            func()
            time.sleep(wait_time)

    def _save_command_to_replicate(self):

        ftp_id, request =self.new_operations.get()

        #self.last_operation+=1        
        #self.operations_log.append((ftp_id, request))
        
        self.bully_protocol\
            .sinc\
            .logs_dict\
            .setdefault(self.bully_protocol.sinc.hash,[])\
            .append((ftp_id, request))


    def _get_ftp_with_data(self, hash: str, operation_id: int):
        # TODO EL PROBLEMA DE QUE NO PUEDA COPIAR DEBE ESTAR AQUI!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! 
        posibles= [ key for key, ftp in self.available_ftp.items()
                    if ftp['last_operations_id'].setdefault(hash,0) > operation_id ] 
        if len(posibles) > 0 :
            return posibles[random.randint(0,len(posibles)-1)]
        return None

    def _consume_command_to_replicate(self,):
        log_index, hash, ftp_id = self.operations_to_do.get()


        if ftp_id not in self.available_ftp:
            #loggin.debug("The ftp is not available, thats why you cant send it the new data")
            return

        ftp_addr=self.available_ftp[ftp_id]['host'],self.available_ftp[ftp_id]['port']
        original_ftp_with_data,request=self.bully_protocol.sinc.logs_dict[hash][log_index]


        if ftp_id == original_ftp_with_data:
            #si es el mismo ftp que mando la operacion,
            #simplemente mandamos a incrementar su contador interno
            remote_operations.increse_last_command(ftp_addr, hash)
            self.available_ftp[ftp_id]['last_operations_id'].setdefault(hash,0)
            self.available_ftp[ftp_id]['last_operations_id'][hash]+=1
            return

        #loggin.debug(f'replicating {request} to {ftp_id}')
        try:
            match request:
                case ['STOR', *path]:
                    path = ' '.join(path)

                    ftp_with_data_name = self._get_ftp_with_data(hash,log_index)
                    if ftp_with_data_name is None:
                        logging.debug("There is no ftp available to replicate the data")
                        return

                    remote_operations.ftp_to_ftp_copy(
                        emiter_addr=(
                            self.available_ftp[ftp_with_data_name]['host'],
                            self.available_ftp[ftp_with_data_name]['port'],
                        ),
                        replication_addr=ftp_addr,
                        file_path1=path,
                        file_path2=path
                    )

                    #loggin.debug(f'Replication ended in {ftp_id} from {ftp_with_data_name}')  

                case ['MKD', *path]:
                    path = ' '.join(path)
                    remote_operations.create_folder(ftp_addr,path=path)

                case ['DELE', *path]:
                    path = ' '.join(path)
                    remote_operations.delete_file(ftp_addr,path=path)

                case ['RMD', *path]:
                    path = ' '.join(path)
                    remote_operations.delete_folder(ftp_addr,path=path)

        except Exception as e:
            logging.warning(f"Failed to replicate the data from {ftp_addr} to {ftp_id}!")
            print("*"*10)
            logging.debug(e)
            print("*"*10)


        self.available_ftp[ftp_id]['last_operations_id'].setdefault(hash,0)
        self.available_ftp[ftp_id]['last_operations_id'][hash]+=1
        remote_operations.increse_last_command(ftp_addr, hash)

    def _handle_conn(self, conn: socket.socket, addr):
        """ Repetir la orden a cada uno de los ftps"""
        conn.settimeout(10)
        try:
            request=conn.recv(1024).decode('ascii')
            request=request.split()

            node_id = request.pop(0)
            request[0]=request[0].upper()
            if request[0] == "PING":
                conn.send(b'ok')
                #loggin.debug(f"reciving ping from {node_id}")
                return 

            if not self.accepting_connections:
                conn.send(b'CLOSED')
                return 


            #logging.info(f'Saving to replicate command from {node_id}::{" ".join(request)}')
            self.new_operations.put((node_id, request))
            #logging.info(f'new_operations:{self.new_operations.queue}')

        except TimeoutError:
            logging.error(f"Connection Timeout {addr}")
        else: 
            conn.send(b'OK')
        finally:
            conn.close()

    def run(self):
        threading.Thread(target=self._refresh_loop,args=(self._refresh_ftp_nodes,self.refresh_time)).start()
        threading.Thread(target=self._refresh_loop,args=(self._refresh_coordinator_nodes,self.refresh_time)).start()

        threading.Thread(target=self._refresh_loop,args=(self._save_command_to_replicate,0)).start()
        threading.Thread(target=self._refresh_loop,args=(self._consume_command_to_replicate,0)).start()

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
