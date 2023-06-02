import socket
import threading
from typing import TypedDict
from queue import Queue
from time import sleep
import logging


from .utils import prepare_command_args 
from .commands import BaseCommand 
from .response import send_control_response
from .context import Context

import utils

class FTPConfiguration(TypedDict):
    id: str
    host: str
    port: int
    welcome_message: str
    root_path: str
    commands: list[BaseCommand]

class FTP:
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
        self.co_coordinators = [] 
        self.last_write_command_id = 0

    def set_coordinator(self, coordinator_dir):
        self.current_coordinator = coordinator_dir 

    def coordinator_communication(self):
        while True:
            logging.debug(f'Operations: {self.write_operations.queue}')
            while self.write_operations.empty():
                sleep(1)
            #operation=self.write_operations.get()
            operation=self.write_operations.queue[0]
            if self.current_coordinator is None: 
                logging.warning("No coordinator available!")
                #self.write_operations.put(operation)
                sleep(10)
                continue
           
            logging.info(f"Sending write-operation to coordinator {operation}")
            if (soc:=utils.connect_socket_to(*self.current_coordinator)) and\
                  soc is not None:

                with soc:
                # TODO ver si vale la pena esperar a una respuesta que confirme que al 
                # menos se duplico una vez la operacion en otro nodo ftp
                    soc.settimeout(10)
                    try:
                        soc.send(operation.encode('ascii'))
                        if soc.recv(1024).decode() == 'OK':
                            logging.debug('COMUNICATION WITH COORDINATOR DONE')
                            self.write_operations.get()


                            # ademas, mandamos a los co-coordinadores el comando
                            for addr in self.co_coordinators:
                                if (c_soc:=utils.connect_socket_to(*addr)) and\
                                    c_soc is not None:
                                    c_soc.settimeout(3)
                                    with c_soc:
                                        try:
                                            c_soc.send(operation.encode('ascii'))
                                            c_soc.recv(1024)
                                        except TimeoutError:
                                            logging.debug("Failed to send to co-coordinator the operation!")
                                            pass

                        else:
                            logging.debug('COMUNICATION WITH COORDINATOR FAILED')
                            self.current_coordinator = None
                    except TimeoutError:
                        logging.debug('COMUNICATION WITH COORDINATOR FAILED')
                        self.current_coordinator = None
            else: 
               #self.write_operations.put(operation)
                logging.debug(f'COMUNICATION WITH COORDINATOR FAILED (TRYING TO CONNECT TO {self.current_coordinator}) ')
                self.current_coordinator = None

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

                        logging.info(f'{addr}::{" ".join(args)}')
                        break
                if not exist_command:
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
        threading.Thread(target=self.coordinator_communication,args=()).start()

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.listen() 
            logging.info("Server Started!")

            while True:
                conn, addr = s.accept()
                logging.info(f'Connected with {addr}')
                threading.Thread(target=self.start_connection,args=(conn, addr)).start()

if __name__ =='__main__':
    pass