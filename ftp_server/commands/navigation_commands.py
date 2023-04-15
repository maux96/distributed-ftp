from .base_command import BaseCommand
from ..context import Context

class CWDCommand(BaseCommand):
    @classmethod
    def _resolve(cls,context: Context, args: list[str]):
        new_path =' '.join(args) 
        if context.set_path(new_path):
            context.send_control_response(250, 'Directory changed.')
        else:
            context.send_control_response(501, 'Invalid Directory.')

class CDUPCommand(BaseCommand):
    @classmethod
    def _resolve(cls,context: Context, args: list[str]):
        context.set_path(context.client_path.parent)
        context.send_control_response(200, 'Directory changed.')