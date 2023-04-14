from .base_command import BaseCommand
from .context import Context
from .response import send_control_response
from .. import utils

class CWDCommand(BaseCommand):
    @classmethod
    def _resolve(cls,context: Context, args: list[str]):
        new_path =' '.join(args) 
        is_valid, new_path = utils.verify_and_get_valid_path(context.current_path,
                                                             new_path) 
        if is_valid:
            context.current_path = new_path 
            send_control_response(context.control_connection,250, 'Directory changed.')
        else:
            send_control_response(context.control_connection,501, 'Invalid Directory.')

class CDUPCommand(BaseCommand):
    @classmethod
    def _resolve(cls,context: Context, args: list[str]):
        context.current_path = context.current_path.parent 
        send_control_response(context.control_connection,200, 'Directory changed.')