from ftp_server.server import FTP, FTPConfiguration 
from ftp_server import commands
from coordinator_server.coordinator import Coordinator  
from name_server.name_server import NameServer

import random
import argparse

import logging


if __name__ == '__main__':


    parser = argparse.ArgumentParser(description='FTP Distribuido')
    parser.add_argument('service',
                        choices=['ftp', 'coordinator', 'nameserver'],
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
    parser.add_argument('--logging-lvl', default=logging.DEBUG,
                        help='El nivel de loggeo del nodo')
    args = parser.parse_args()

    ID = args.id
    HOST = args.host 
    PORT = int(args.port)
    ROOT_DIR = args.root_dir
    WELCOME_MSG = args.welcome_msg

    logging.basicConfig(level=int(args.logging_lvl))

    #ns_utils.ns_register(f"{args.service}_{ID}",HOST,PORT)
    #print(f"Server {ID} ejecutandose en {HOST}:{PORT}.")
    logging.info(f"Server {ID} ejecutandose en {HOST}:{PORT}.")
    if args.service == 'ftp':
        FTP(FTPConfiguration(
            id=ID,
            host=HOST,
            port= PORT, 
            root_path=ROOT_DIR,
            welcome_message=WELCOME_MSG,
            commands=commands.ALL
        )).run()

    elif args.service == 'coordinator':
        Coordinator(ID, HOST, PORT, refresh_time=10).run()

    elif args.service == 'nameserver':
        NameServer(ID, HOST, PORT).run()
        pass
