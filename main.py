from ftp_server.server import FTP, FTPConfiguration 
from ftp_server import commands
from proxy import Proxy
from analizer import Analizer
import ns_utils

import random
import argparse




if __name__ == '__main__':


    parser = argparse.ArgumentParser(description='FTP Distribuido')
    parser.add_argument('service',
                        choices=['ftp', 'proxy', 'analizer'],
                        help='Tipo de servicio a ejecutar')

    parser.add_argument('--id',default='DEFAULT_ID', help='El id del servidor')
    parser.add_argument('--host',default='0.0.0.0',
                        help='El host donde se va a ejecutar.')
    parser.add_argument('--port',default=str(random.randint(5000, 20000)),
                        help='El puerto donde se va a ejecutar.')
    parser.add_argument('--root-dir', default='.',
                        help='En el caso de ser un FTP, la raiz del almacenamiento.')
    parser.add_argument('--welcome-msg', default='Connection Success!',
                        help='El Mensaje de bienvenida')
    args = parser.parse_args()

    ID = args.id
    HOST = args.host 
    PORT = int(args.port)
    ROOT_DIR = args.root_dir
    WELCOME_MSG = args.welcome_msg

    ns_utils.ns_register(f"{args.service}_{ID}",HOST,PORT)
    print(f"Server {ID} ejecutandose en {HOST}:{PORT}.")
    if args.service == 'ftp':
        FTP(FTPConfiguration(
            id=ID,
            host=HOST,
            port= PORT, 
            root_path=ROOT_DIR,
            welcome_message=WELCOME_MSG,
            commands=commands.ALL
        )).run()

    elif args.service == 'proxy':
        Proxy(HOST,PORT).run()

    elif args.service == 'analizer':
        Analizer(HOST,PORT,10).run()
