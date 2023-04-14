from .base_command import BaseCommand
from . import basic_commands
from . import data_openers_commands
from . import data_commands
from . import navigation_commands 

AVAILABLE_COMMANDS: list[type[BaseCommand]]= [
   basic_commands.NOOPCommand,
   basic_commands.TYPECommand,
   basic_commands.USERCommand,
   basic_commands.PWDCommand,
   basic_commands.QUITCommand,

   data_openers_commands.PASVCommand,

   data_commands.LISTCommand,

   navigation_commands.CWDCommand,
   navigation_commands.CDUPCommand,
]