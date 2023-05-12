from .base_command import BaseCommand
from ..context import Context

""" 
    Commandos que van a cambiar variables internas del FTP,
    estos comandos no pertenecen al protocolo ftp, estan destinados a ser usados solo
    por un coordinador y idealmente requeririan autenticacion.
"""

class SETCOORDCommand(BaseCommand):
    @classmethod
    def _resolve(cls,context: Context, args: list[str]):
        context.set_coordinator(int(args[0]))
        context.send_control_response(200,"Coordinator Changed!")