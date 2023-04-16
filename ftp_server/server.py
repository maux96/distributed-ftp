import socket
import threading
from typing import TypedDict

from . import utils
from .commands import BaseCommand 
from .response import send_control_response
from .context import Context

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

    def start_connection(self,conn: socket.socket, addr):
        try:
            send_control_response(conn, 220, self.welcome_message)

            current_context = Context(
                control_connection=conn,
                root_path=self.root_path,
                host=self.host,
                port=self.port
            )

            while not current_context.is_die_requested and\
                (message:=conn.recv(2048)):


                args=utils.prepare_command_args(message)
                command_type= args[0]

                exist_command=False
                for command in self.available_commands:
                    if command.name() == command_type:
                        exist_command=True
                        command._resolve(current_context,args[1:]) 
                        break
                if not exist_command:
                    send_control_response(conn, 502, 'Command not implemented!')
                pass

        finally:
            conn.close()
            print('Connection Closed', addr)

    def run(self):
        print('Starting server...', end='')
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.listen() 
            print('DONE!')

            while True:
                conn, addr = s.accept()
                print('Connected with', addr)
                threading.Thread(target=self.start_connection,args=(conn, addr)).start()

if __name__ =='__main__':
    pass