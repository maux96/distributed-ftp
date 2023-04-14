
from .base_command import BaseCommand
from .context import Context
from .response import send_control_response

import pathlib
import subprocess


class LISTCommand(BaseCommand):
    @classmethod
    def _resolve(cls,context: Context, args: list[str]):
        path_ = pathlib.Path(*args) if args else context.current_path 

        # TODO verificar que haya conexion de datos...
        send_control_response(context.control_connection,
                             125,'Data connection already open; transfer starting.')

        data_conn, data_addr= context.data_connection.accept()
        data_conn.send(cls.list_dir(path_ ))

        data_conn.close()

        send_control_response(context.control_connection,
                             226,'Closing data connection.')

    @staticmethod
    def list_dir(route):
        result = subprocess.run(['ls','-l', route],
                  stdout=subprocess.PIPE,
                  stderr=subprocess.PIPE).stdout
        return result 
