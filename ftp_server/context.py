from pathlib import Path
import socket
from queue import Queue

from typing import Literal

from . import response 


class Context:
    def __init__(
            self,*,
            ftp_server,
            control_connection: socket.socket,
        ) -> None:
        self._ftp_server = ftp_server
        self.control_connection = control_connection
        self.data_connection = socket.socket(-1)
        self.client_path= Path('/')
        self.root_path= Path(ftp_server.root_path)
        self.HOST = ftp_server.host
        self.PORT = ftp_server.port 
        self.write_log = ftp_server.write_operations 
        self._is_die_requested = False
        self.user = 'anonymous' 
        self.reneme_from: None | Path = None


    @property
    def is_die_requested(self):
        return self._is_die_requested

    @property
    def current_absolute_os_path(self):
        return self.root_path / self.client_path.relative_to('/')

    def die(self):
        self._is_die_requested = True 

    def save_write_operation(self, value):
        self.write_log.put(self._ftp_server.id+" "+value)

    def save_write_op(self,
                      type_: Literal['STOR', 'MKD', 'DELE', 'RMD'],
                      path: str ):

        path=self.get_absolute_path(path)
        self.save_write_operation(f"{type_} {path}")


    def set_coordinator(self, port: int):
        addr_peer_name,_=self.control_connection.getpeername()
        self._ftp_server.set_coordinator((addr_peer_name, port))

    def set_coord_hash(self, hash: str):
        self._ftp_server.current_coord_hash = hash
        pass


    def login(self, user_name: str):
        self.user = user_name

    def verify_and_get_absolute_os_path(self,path: Path | str, is_dir=True):
        """
        verifica una ruta y retorna su ruta absoluta (OS) 
        """
        if not self.is_valid_path(path,is_dir=is_dir) :
            return None 
        return self.get_os_absolute_path(path)

    def is_valid_path(self, path: Path | str, is_dir=True):
        """
        verifica que exista un directorio (o un archivo)
        """
        path = Path(path)

        if is_dir:
            return ( path.is_absolute() and\
                        (self.root_path / path.relative_to('/')).is_dir() ) or\
                    (self.current_absolute_os_path / path).is_dir()

        return ( path.is_absolute() and\
                     (self.root_path / path.relative_to('/')).is_file() ) or\
                (self.current_absolute_os_path / path).is_file()

    def get_last_write_operation_id(self,hash :str) -> int | None:
        return self._ftp_server.last_write_command_id.setdefault(hash, 0)

    def increse_last_operation(self, hash: str):
        self._ftp_server.last_write_command_id.setdefault(hash,0)
        self._ftp_server.last_write_command_id[hash]+=1

    def get_absolute_path(self, path):
        return str(self.get_os_absolute_path(path))[len(str(self.root_path)):]

    def get_os_absolute_path(self, client_path: Path | str):
        """
            Retorna la ruta global en el sistema operativo.
            Si `client_path` es relativa la trata como en el actual directorio
        """
        client_path = Path(client_path)
                   
        if client_path.is_absolute():
            return self.root_path / client_path.relative_to('/')
        return self.current_absolute_os_path / client_path 

    def set_path(self,path: Path | str):
        """
            Se cambia el directorio actual del servidor 
        """
        path = Path(path)

        if path.is_absolute() and (self.root_path / path.relative_to('/')).is_dir():
            self.client_path = path
            return True
        elif (self.current_absolute_os_path / path).is_dir():
            self.client_path /= path
            return True
        return False

    def send_control_response(self, code: int, message: str, encoding='ascii'):
        """
        Envia un mensaje por el canal de control
        """
        response.send_control_response(self.control_connection,
                                        code,
                                        message,
                                        encoding=encoding)