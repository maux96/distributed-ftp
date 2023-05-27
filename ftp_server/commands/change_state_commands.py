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
        context.send_control_response(200, f"{context.get_last_write_operation_id()} \
Coordinator Changed!")

class INCRESECommand(BaseCommand):
    require_auth = True

    @classmethod
    def _resolve(cls, context: Context, args: list[str]):
        context.increse_last_operation()
        context.send_control_response(200, "OK")

