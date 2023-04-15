import socket
import threading


from . import utils
from .commands import AVAILABLE_COMMANDS
from .commands.response import send_control_response
from .commands.context import Context

HOST='0.0.0.0'
PORT=7890

WELCOME_MESSAGE = "Welcome to our FTP :)"
#START_PATH = '/home/maux96/Images' 
START_PATH = './test_storage'


def start_connection(conn: socket.socket, addrs):
    try:
        send_control_response(conn, 220, WELCOME_MESSAGE)

        current_context = Context(
            control_connection=conn,
            data_connection=socket.socket(-1),
            root_path=START_PATH,
            host=HOST,
            port=PORT
        )

        while not current_context.is_die_requested and\
            (message:=conn.recv(2048)):

            #print(addrs,'>   ', message.decode('ascii'))

            args=utils.prepare_command_args(message)
            command_type= args[0]

            exist_command=False
            for command in AVAILABLE_COMMANDS:
                if command.name() == command_type:
                    exist_command=True
                    command._resolve(current_context,args[1:]) 
                    break
            if not exist_command:
                send_control_response(conn, 502, 'Command not implemented!')
            pass

    finally:
        conn.close()
        print('Data Connection Closed:', addrs)

def main():
    print('Starting server...', end='')
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen() 

        print('DONE!')
        while True:
            conn, addr = s.accept()
            print("New Connection:", addr)

            threading.Thread(target=start_connection,args=(conn, addr)).start()

if __name__ =='__main__':
    main()
