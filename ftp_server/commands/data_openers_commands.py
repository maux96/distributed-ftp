from .base_command import BaseCommand
from ..context import Context
from ..response import send_control_response
from .. import utils

import random
import socket

class PASVCommand(BaseCommand):
    @classmethod
    def _resolve(cls,context: Context, args: list[str]):

        data_socket,pasive_port = PASVCommand._get_pasive_data_socket(context)
        address=utils.transform_addrs_into_string(context.HOST, pasive_port)
        
        send_control_response(context.control_connection,
                              227,f"Entering Passive Mode ({address})")

        context.data_connection=data_socket.accept()[0]


    @staticmethod
    def _get_pasive_data_socket(context: Context, port=None):
        if port is None:
            port = random.randint(1500,9000)
        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        soc.bind((context.HOST, port))
        soc.listen() 
        return soc, port

class PORTCommand(BaseCommand):
    @classmethod
    def _resolve(cls,context: Context, args: list[str]):
        data_addr, data_port = utils.transform_string_into_addrs(args[0])
        data_socket=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        data_socket.connect((data_addr,data_port))
        send_control_response(context.control_connection,
                              200,"Entering in Active Mode")

        context.data_connection=data_socket

