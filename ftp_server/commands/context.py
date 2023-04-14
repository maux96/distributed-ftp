from pathlib import Path
import socket


class Context:
    def __init__(
            self,*,
            control_connection: socket.socket,
            data_connection: socket.socket,
            current_path:Path | str,
            host: str,
            port: int
        ) -> None:

        self.control_connection = control_connection
        self.data_connection = data_connection
        self.current_path= Path(current_path)
        self.HOST = host
        self.PORT = port