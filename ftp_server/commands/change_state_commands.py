from ftp_server.context import Context
from .base_command import BaseCommand
from ..context import Context

import logging

""" 
    Commandos que van a cambiar variables internas del FTP,
    estos comandos no pertenecen al protocolo ftp, estan destinados a ser usados solo
    por un coordinador y idealmente requeririan autenticacion.
"""

class SETCOORDCommand(BaseCommand):
    require_auth = True

    @classmethod
    def _resolve(cls,context: Context, args: list[str]):
        context.set_coordinator(int(args[0]))
        context.send_control_response(200, "Coordinator Changed!")

class SETCURRENTHASHCommand(BaseCommand):
    require_auth = True

    @classmethod
    def _resolve(cls,context: Context, args: list[str]):
        context.set_coord_hash(args[0])
        context.send_control_response(200, "OK")
        pass

class ADDCOCOORDCommand(BaseCommand):
    require_auth = True

    @classmethod
    def _resolve(cls,context: Context, args: list[str]):
        addr, port=args[0],int(args[1])

        context._ftp_server.co_coordinators.append((addr,port))
        context.send_control_response(200, "Cocoordinator Added!")

class CLEARCOCOORDCommand(BaseCommand):
    require_auth= True

    @classmethod
    def _resolve(cls,context: Context, args: list[str]):
        context._ftp_server.co_coordinators = [] 
        context.send_control_response(200, "CoCoordinators clear")


class INCRESECommand(BaseCommand):
    require_auth = True

    @classmethod
    def _resolve(cls, context: Context, args: list[str]):
        context.increse_last_operation(args[0])
        context.send_control_response(200, "OK")


# get

class LASTFROMHASHCommand(BaseCommand):
    require_auth= True

    @classmethod
    def _resolve(cls, context: Context, args: list[str]):

        last=context.get_last_write_operation_id(args[0])
        context.send_control_response(200, f"{last} Cocoordinator Added!")
