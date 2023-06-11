import socket
import re
from pathlib import Path 
from os import environ
import logging

import utils

def login(user_name, socket: socket.socket):
    socket.send(b'USER admin')
    socket.recv(2048)

def ftp_to_ftp_copy(emiter_addr, replication_addr, file_path1: str | Path, file_path2: str | Path):
    s1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    s1.connect(emiter_addr)
    s2.connect(replication_addr)

    #welcome message
    s1.recv(2048).decode('ascii')
    s2.recv(2048).decode('ascii')

    #login
    login('admin',s1)
    login('admin',s2)

    # open data port (PASV) with 1
    s1.send(b'PASV')
    control_response1=s1.recv(2048).decode('ascii')

    direction= re.search(r'\(.*\)',control_response1)
    if direction is None:
        raise Exception("Problem with call to PASV")
    direction = direction.group()[1:-1]


    # open data port (PORT) with 2 using PASV port for 1
    s2.send(f'PORT {direction}'.encode('ascii'))
    control_response2=s2.recv(2048).decode('ascii')


    # sending the file
    s1.send(f'RETR {file_path1}'.encode('ascii'))
    control_response1=s1.recv(2048).decode('ascii')
    if control_response1.split()[0] != '125':
        #el archivo no existe por lo que se debe haber borrado en una operacion futura.

        #logging.debug('FTPxFTPcopy | RETR operation not posible. Ignoring.')
        s1.close()
        s2.close()
        return

    s2.send(f'STOR {file_path2}'.encode('ascii'))
    control_response2=s2.recv(2048).decode('ascii')
    
    control_response1=s1.recv(2048).decode('ascii')
    control_response2=s2.recv(2048).decode('ascii')

    s1.close()
    s2.close()

def increse_last_command(addr, hash: str):
    if (s1:= utils.connect_socket_to(*addr)) and s1 is not None:
        with s1:
            s1.recv(2048).decode('ascii')
            login('admin', s1)

            s1.send(f"INCRESE {hash}".encode('ascii'))
            control_response =  s1.recv(1024).decode('ascii')

            #logging.debug(f'{addr} INCRESSING | Response:{control_response} ')
    else:    
        logging.debug(f'failed increse_last_command in hash {hash}')



def create_folder(replication_addr, path: str | Path):
    path = Path(path)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
        s1.settimeout(10)
        s1.connect(replication_addr)

        #welcome message
        s1.recv(2048).decode('ascii')

        login('admin', s1)

        s1.send(f"MKD {path}".encode('ascii'))

        # TODO comprobar que haya sido valida la creacion de la carpeta
        s1.recv(2048)

def delete_file(replication_addr, path: str | Path):
    path = Path(path)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
        s1.settimeout(10)
        s1.connect(replication_addr)

        #welcome message
        s1.recv(2048).decode('ascii')

        login('admin', s1)

        s1.send(f"DELE {path}".encode('ascii'))

        # TODO comprobar que haya sido valida la creacion de la carpeta
        s1.recv(2048)
    pass

def delete_folder(replication_addr, path: str | Path):
    path = Path(path)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
        s1.settimeout(10)
        s1.connect(replication_addr)

        #welcome message
        s1.recv(2048).decode('ascii')

        login('admin', s1)

        s1.send(f"RMD {path}".encode('ascii'))

        # TODO comprobar que haya sido valida la creacion de la carpeta
        s1.recv(2048)
    pass
    pass

if __name__ == '__main__':
    if 'PORT1' not in environ and 'PORT2' not in environ:
        raise Exception("PORT1 and PORT2 needed in environ!")

    addr1 = ('0.0.0.0',int(environ['PORT1']))
    addr2 = ('0.0.0.0',int(environ['PORT2']))