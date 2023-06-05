
from .base_command import BaseCommand
from ..response import send_control_response
from ..context import Context



class MODECommand(BaseCommand):
    @classmethod
    def _resolve(cls,context: Context, args: list[str]):
        send_control_response(context.control_connection, 200, 'Stream')
class STRUCommand(BaseCommand):
    @classmethod
    def _resolve(cls,context: Context, args: list[str]):
        send_control_response(context.control_connection, 200, 'File')
        pass
class TYPECommand(BaseCommand):
    @classmethod
    def _resolve(cls,context: Context, args: list[str]):
        send_control_response(context.control_connection,200,'ASCII Non-print')
class USERCommand(BaseCommand):
    @classmethod
    def _resolve(cls,context: Context, args: list[str]):
        context.login(args[0])
        send_control_response(context.control_connection, 230, f'User {args[0]}')


class PWDCommand(BaseCommand):
    @classmethod
    def _resolve(cls,context: Context, args: list[str]):
        send_control_response(context.control_connection,
                               257, '"'+str(context.client_path)+'"')

class NOOPCommand(BaseCommand):
    @classmethod
    def _resolve(cls,context: Context, args: list[str]):
        send_control_response(context.control_connection, 200, 'OK!')
        pass

class QUITCommand(BaseCommand):
    @classmethod
    def _resolve(cls,context: Context, args: list[str]):
        send_control_response(context.control_connection, 221, 'Good Bye :)')
        context.die()
