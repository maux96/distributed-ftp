import socket
import re
from pathlib import Path 
from os import environ



def ftp_to_ftp_copy(addr1, addr2, file_path1: str | Path, file_path2: str | Path):
    s1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    s1.connect(addr1)
    s2.connect(addr2)
    print(s1.recv(2048).decode('ascii'))
    print(s2.recv(2048).decode('ascii'))

    # open data port (PASV) with 1
    s1.send(b'PASV')
    control_response1=s1.recv(2048).decode('ascii')
    print(control_response1)
    direction= re.search(r'\(.*\)',control_response1)
    if direction is None:
        raise Exception("Problem with call to PASV")
    direction = direction.group()[1:-1]


    # open data port (PORT) with 2 using PASV port for 1
    s2.send(f'PORT {direction}'.encode('ascii'))
    control_response2=s2.recv(2048).decode('ascii')
    print(control_response2)

    # sending the file
    s1.send(f'RETR {file_path1}'.encode('ascii'))
    control_response1=s1.recv(2048).decode('ascii')
    print(control_response1)

    s2.send(f'STOR {file_path2}'.encode('ascii'))
    control_response2=s2.recv(2048).decode('ascii')
    print(control_response2)

    control_response1=s1.recv(2048).decode('ascii')
    print(control_response1)
    control_response2=s2.recv(2048).decode('ascii')
    print(control_response2)


def create_folder(addr, path: str | Path):
    path = Path(path)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
        s1.settimeout(10)
        s1.connect(addr)
        print(s1.recv(2048).decode('ascii'))

        s1.send(f"MKD {path}".encode('ascii'))

        # TODO comprobar que haya sido valida la creacion de la carpeta
        s1.recv(2048)

if __name__ == '__main__':
    if 'PORT1' not in environ and 'PORT2' not in environ:
        raise Exception("PORT1 and PORT2 needed in environ!")

    addr1 = ('0.0.0.0',int(environ['PORT1']))
    addr2 = ('0.0.0.0',int(environ['PORT2']))