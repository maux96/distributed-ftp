import socket
import threading
from multiprocessing.pool import ThreadPool

from typing import TypedDict
from queue import Queue
from time import sleep
import json
import logging
import random
import re
import os
import pathlib 

from coordinator_server import coordinator
from coordinator_server import remote_operations


from .utils import prepare_command_args 
from .commands import BaseCommand 
from .response import send_control_response
from .context import Context

import utils
import discoverer

class FTPConfiguration(TypedDict):
    id: str
    host: str
    port: int
    welcome_message: str
    root_path: str
    commands: list[BaseCommand]

class FTP:
    TOTAL_THREADS = 10
    TREE_REFRESH_TIME= 10
    def __init__(self, config: FTPConfiguration) -> None:
        self.id = config['id']
        self.host = config['host']
        self.port = config['port']
        self.welcome_message = config['welcome_message']
        self.root_path = config['root_path']
        self.available_commands= config['commands']
        self.write_operations = Queue()
        self.write_operations_done = set() 

        self.current_coordinator = None
        self.current_coord_hash: str | None = None

        self.co_coordinators = [] 
        #self.last_write_command_id = 0
        self.last_write_command_id: dict[str, int] = {} 

        self.file_tree: dict[str, str] = {}
        self.coordinator_tree: dict[str, list[tuple[str, int]]] = {}

        self.discoverer = discoverer.Discoverer(
            self.id,
            'ftp',
            (self.host, self.port))

    def set_coordinator(self, coordinator_dir):
        self.current_coordinator = coordinator_dir 

    def get_file_system(self):
        sol = []
        for route, files, folders in os.walk(self.root_path):
            sol+=['/'+f for f in files]+ ['/'+ f for f in folders]
        # print("#"*20,sol)
        return sol


    def send_to_coords(self, message: str):

        # principal lider
        if self.current_coordinator is not None:
            soc=utils.connect_socket_to(*self.current_coordinator)
            if soc is not None:
                with soc:
                    if soc is not None:
                        soc.send(f"{self.id} {message}".encode())
                        pass
            else:
                logging.error("Error opening a socket to send info to liders")
                return
        else: 
            logging.error("No coordinator available!")
            return


        # co-liders
        for addr in self.co_coordinators:
            if  self.current_coordinator != addr and\
                (c_soc:=utils.connect_socket_to(*addr)) and\
                c_soc is not None:
                c_soc.settimeout(3)
                with c_soc:
                    try:
                        soc.send(f"{self.id} {message}".encode())
                    except TimeoutError:
                        logging.debug("Failed to send to co-coordinator the operation!")
                        pass



    def is_folder(self, route: str):
        p=pathlib.Path(self.root_path,route.strip('/'))
        print("ANALISIS FILE_FOLDER---", p)
        return p.is_dir()
    
    def operation_saver(self):
        while True:
            while self.write_operations.empty():
                sleep(1)
            operation=self.write_operations.queue[0]
            
            if self.current_coordinator is None: 
                logging.warning("No coordinator available!")
                sleep(10)
                continue             
            match operation:
                case ['STOR' | 'MKD' as type_, *path]:
                    type_ ='folder' if type_=='MKD' else 'file'
                    self.send_to_coords(f"ADD_TO_TREE {self.port} {type_} {' '.join(path)}")
                    
                case ['DELE' | 'RMD',*path]:
                    self.send_to_coords(f"REMOVE_FROM_TREE {' '.join(path)}")

                case ['RENAME', *args]:
                    from_path, to_path = re.findall(r"\'(.*?)\'",' '.join(args))

                    self.send_to_coords(f"REMOVE_FROM_TREE {' '.join(from_path)}")
                    self.send_to_coords(f"ADD_TO_TREE {' '.join(to_path)}")

            self.write_operations.get()
              

    def tree_refresh(self):

        while True:
            if self.current_coordinator is None: 
                logging.warning("No coordinator available!")
                sleep(FTP.TREE_REFRESH_TIME//2)
                continue  
               
            if (soc:=utils.connect_socket_to(*self.current_coordinator)):
                soc.send(f"{self.id} GET_TREE".encode())
                serialized_json=soc.recv(4096).decode()
                tree=json.loads(serialized_json)

                
                for path, ftps in tree.items():
                    print(path,"||||||", self.get_file_system())
                    if path not in self.get_file_system():
                        # TODO verificar que el ftp seleccionado esta disponible
                        ftp_to_copy_from = ftps[random.randint(0,len(ftps)-1)]
                        
                        is_folder = ftp_to_copy_from['type'] == 'folder'
                        print(f"{path}: Is Folder ????????????????????????? ", is_folder)

                        if not is_folder:
                            remote_operations.ftp_to_ftp_copy(
                                tuple(ftp_to_copy_from['addr']),
                                (self.host, self.port),
                                path,
                                path)

                        else:
                            remote_operations.create_folder((self.host, self.port),path)
                            print('ENTROOO CARPETAAAAA!!!')

                for path in self.get_file_system():
                    if path not in tree.keys():
                        print(tree.keys())

                        if self.is_folder(path):
                            remote_operations.delete_folder((self.host, self.port),path)
                        else:
                            remote_operations.delete_file((self.host, self.port),path)




            sleep(FTP.TREE_REFRESH_TIME)



    def start_connection(self,conn: socket.socket, addr):
        try:
            send_control_response(conn, 220, self.welcome_message)

            current_context = Context(
                ftp_server = self,
                control_connection=conn,
            )

            while not current_context.is_die_requested and\
                (message:=conn.recv(2048)):

                args= prepare_command_args(message)
                command_type= args[0]

                exist_command=False
                for command in self.available_commands:
                    if command.name() == command_type:
                        exist_command=True
                        command.resolve(current_context,args[1:]) 

                        #logging.info(f'{addr}::{" ".join(args)}')
                        break
                if not exist_command:
                    logging.debug(f"Not implemented command {message}")
                    send_control_response(conn, 502, 'Command not implemented!')
                pass
        except (ConnectionResetError, TimeoutError) as e:
            logging.error(f'ERROR:{e}')
            pass
        finally:
            conn.close()
            #print('Connection Closed', addr)
            logging.info(f'Connection Closed {addr}')

    def run(self):
        if not self.discoverer.is_remote:
            self.discoverer.start_discovering()

        threading.Thread(target=self.tree_refresh,args=()).start()
        threading.Thread(target=self.operation_saver,args=()).start()

        if  (s:=utils.create_socket_and_listen(self.host, self.port)) and s is not None:
            with s: 
                logging.info("Server Started!")
                with ThreadPool(processes=FTP.TOTAL_THREADS) as threat_pool:
                    while True:
                        conn, addr = s.accept()
                        logging.info(f'Connected with {addr}')
                        threat_pool.apply_async(self.start_connection,args=(conn, addr))
        else: 
            logging.error(f"error creating the socket in port {self.port}.")
            exit(1)

if __name__ =='__main__':
    pass
