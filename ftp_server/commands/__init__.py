from .base_command import BaseCommand
from . import basic_commands

AVAILABLE_COMMANDS: list[BaseCommand]= [
   basic_commands.NOOPCommand,
   basic_commands.TYPECommand,
   basic_commands.USERCommand,
   basic_commands.PWDCommand
]