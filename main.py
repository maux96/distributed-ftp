from ftp_server.server import FTP, FTPConfiguration 
from ftp_server import commands

config = FTPConfiguration(
    id='FTP0',
    host='0.0.0.0',
    port=7890,
    root_path='.',
    welcome_message='Hello World!',
    commands=commands.ALL
)

FTP(config).run()
