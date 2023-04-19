from ftp_server.server import FTP, FTPConfiguration 
from ftp_server import commands
from proxy import Proxy
from analizer import Analizer
import ns_utils

import random
import argparse


def start_ftp_server(config: FTPConfiguration):
    print(f"Server {config['id']} ejecutandose en {config['host']}:{config['port']}.")
    FTP(config).run()


if __name__ == '__main__':


    parser = argparse.ArgumentParser(description='FTP Distribuido')
    parser.add_argument('service',
                        choices=['ftp', 'proxy', 'analizer'],
                        help='Tipo de servicio a ejecutar')

    parser.add_argument('--id',default='DEFAULT_ID')
    parser.add_argument('--host',default='0.0.0.0')
    parser.add_argument('--port',default=str(random.randint(5000, 20000)))
    parser.add_argument('--root-dir', default='.')
    parser.add_argument('--welcome-msg', default='Connection Success!')
    args = parser.parse_args()

    ID = args.id
    HOST = args.host 
    PORT = int(args.port)
    ROOT_DIR = args.root_dir
    WELCOME_MSG = args.welcome_msg

    if args.service == 'ftp':
        ns_utils.ns_register(f"ftp_{ID}",HOST,PORT)
        start_ftp_server(FTPConfiguration(
            id=ID,
            host=HOST,
            port= int(PORT), 
            root_path=ROOT_DIR,
            welcome_message=WELCOME_MSG,
            commands=commands.ALL
        ))

    elif args.service == 'proxy':
        ns_utils.ns_register(f"proxy_{ID}",HOST,PORT)
        print(f"Server {ID} ejecutandose en {HOST}:{PORT}.")
        Proxy(HOST,PORT).run()

    elif args.service == 'analizer':
        ns_utils.ns_register(f'analizer_{ID}',HOST,PORT)
        Analizer(HOST,PORT,10).run()
