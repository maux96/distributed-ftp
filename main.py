from ftp_server.server import FTP, FTPConfiguration 
from ftp_server import commands

from os import environ
import random


def start_ftp_server(config: FTPConfiguration):
    print(f"Server {config['id']} ejecutandose en {config['host']}:{config['port']}.")
    FTP(config).run()


if __name__ == '__main__':

    ftp_id = environ['ID'] if 'ID' in environ else 'FTP_DEFAULT_ID'
    start_ftp_server(FTPConfiguration(
        id=ftp_id,
        host='0.0.0.0',
        port= int(environ['PORT']) if 'PORT' in environ else random.randint(5000, 20000),
        root_path=environ['ROOT_PATH'] if 'ROOT_PATH' in environ else '.',
        welcome_message=f'Welcome to FTP {ftp_id}!!',
        commands=commands.ALL
    ))
