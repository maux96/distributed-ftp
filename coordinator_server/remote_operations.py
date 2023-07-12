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
        print("#### VALUE OF PASV MESSAGE:", control_response1,"||",direction,"||",file_path1,"||",file_path2)
        #raise Exception("Problem with call to PASV")
        return False, -1, 'PASV'
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
        return False, 501, 'RETR' 

    s2.send(f'STOR {file_path2}'.encode('ascii'))
    control_response2=s2.recv(2048).decode('ascii')
    if control_response2.split()[0] == '501':
        return False, 501, 'STOR'
    
    control_response1=s1.recv(2048).decode('ascii')
    control_response2=s2.recv(2048).decode('ascii')

    s1.close()
    s2.close()

    return True, 0, None


def rename_file(addr: tuple[str, int], path: str | Path, new_name: str):
    path = Path(path)

    if (s1:= utils.connect_socket_to(*addr)) and s1 is not None:
        with s1:
            s1.recv(2048).decode('ascii')
            login('admin', s1)

            s1.send(f'RNFR {path}'.encode())
            s1.recv(256)

            s1.send(f'RNTO {new_name}'.encode())
            if s1.recv(256).decode().split()[0] == '553':
                return False,553,'RNTO'

            return True, 0, None
    else: 
        logging.warning(f"Connection not established renaming a file to '{new_name}' in {addr}. Aborting.")
        return False, -1, None

def increse_last_command(addr, hash: str):
    if (s1:= utils.connect_socket_to(*addr)) and s1 is not None:
        with s1:
            s1.recv(2048).decode('ascii')
            login('admin', s1)

            s1.send(f"INCRESE {hash}".encode('ascii'))
            control_response =  s1.recv(1024).decode('ascii')
            
            return True
            #logging.debug(f'{addr} INCRESSING | Response:{control_response} ')
    else:    
        logging.debug(f'failed increse_last_command in hash {hash}')
        return False



def create_folder(replication_addr, path: str | Path):
    path = Path(path)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
        s1.settimeout(10)
        s1.connect(replication_addr)

        #welcome message
        s1.recv(2048).decode('ascii')

        login('admin', s1)

        s1.send(f"MKD {path}".encode('ascii'))

        if s1.recv(2048).decode().split()[0] != '257':
            return False, 501, 'MKD'

    return True,0, None

def delete_file(replication_addr, path: str | Path):
    path = Path(path)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
        s1.settimeout(10)
        s1.connect(replication_addr)

        #welcome message
        s1.recv(2048).decode('ascii')

        login('admin', s1)

        s1.send(f"DELE {path}".encode('ascii'))

        
        if s1.recv(2048).decode().split()[0] != '250':
            return False, 501, 'DELE'

    return True, 0, None

def delete_folder(replication_addr, path: str | Path):
    path = Path(path)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
        s1.settimeout(10)
        s1.connect(replication_addr)

        #welcome message
        s1.recv(2048).decode('ascii')

        login('admin', s1)

        s1.send(f"RMD {path}".encode('ascii'))

        if s1.recv(2048).decode().split()[0] != '250':
            return False, 501, 'RMD'


    return True, 0, None



### auxiliares:

def create_route_in_addr(addr: tuple[str, int],route: str):
    route_segments=route.strip('/').split('/')

    if (s1:= utils.connect_socket_to(*addr)) and s1 is not None:
        with s1:
            s1.recv(256)
            login('admin',s1)

            for i in range(0,len(route_segments)):
                print(route_segments[:i+1])
                s1.send(f"MKD /{'/'.join(route_segments[:i+1])}/".encode('ascii'))
                s1.recv(512)
                
    return True, 0, None


def create_path_and_replicate(emiter_addr, replication_addr, file_path1: str | Path, file_path2: str | Path):
    create_route_in_addr(replication_addr,'/'.join(str(file_path2).split('/')[:-1]))
    return ftp_to_ftp_copy(emiter_addr,replication_addr,file_path1, file_path2)