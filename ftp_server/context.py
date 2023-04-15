from pathlib import Path
import socket

from . import response 


class Context:
    def __init__(
            self,*,
            control_connection: socket.socket,
            root_path:Path | str,
            host: str,
            port: int
        ) -> None:

        self.control_connection = control_connection
        self.data_connection = socket.socket(-1)
        self.client_path= Path('/')
        self.root_path= Path(root_path)
        self.HOST = host
        self.PORT = port
        self._is_die_requested = False


    @property
    def is_die_requested(self):
        return self._is_die_requested

    @property
    def current_absolute_os_path(self):
        return self.root_path / self.client_path.relative_to('/')

    def die(self):
        self._is_die_requested = True 

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