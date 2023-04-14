import socket
import threading


from . import utils
from .commands import AVAILABLE_COMMANDS
from .commands.response import send_control_response
from .commands.context import Context

HOST='0.0.0.0'
PORT=7890

WELCOME_MESSAGE = "Welcome to our FTP :)"
START_PATH = '/home/maux96/Images' 


def start_connection(conn: socket.socket, addrs):
    send_control_response(conn, 220, WELCOME_MESSAGE)

    current_path =  START_PATH 
    data_conn = socket.socket(-1)

    while message:=conn.recv(2048):
        args=utils.prepare_command_args(message)
        command_type= args[0]
        exist_command=False
        for command in AVAILABLE_COMMANDS:
            if command.name() == command_type:
                exist_command=True
                command._resolve(
                    Context(
                        control_connection=conn,
                        data_connection=data_conn,
                        current_path=current_path
                    )
                    ,args[1:]) 
                break
        if not exist_command:
            send_control_response(conn, 502, 'Command not implemented!')
        pass

    conn.close()

def main():
    print('Starting server...', end='')
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen() 

        print('DONE!')
        while True:
            conn, addr = s.accept()

            threading.Thread(target=start_connection,args=(conn, addr)).start()

if __name__ =='__main__':
    main()
