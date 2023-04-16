from .base_command import BaseCommand
from .basic_commands import * 
from .data_commands import * 
from .data_openers_commands import * 
from .navigation_commands import * 

BASICS = [
   NOOPCommand,
   TYPECommand,
   USERCommand,
   PWDCommand,
   QUITCommand,
]
DATA_OPENERS=[
   PASVCommand,
   PORTCommand,
]

DATA = [
   LISTCommand,
   RETRCommand,
   STORCommand,
   MKDCommand,
   DELECommand,
   RMDCommand,
]

NAVIGATION = [
   CWDCommand,
   CDUPCommand,
]

ALL = [
   *BASICS,
   *DATA_OPENERS,
   *DATA,
   *NAVIGATION,
]
