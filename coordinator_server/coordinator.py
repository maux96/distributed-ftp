import socket
import time
import threading
from queue import Queue
import logging

import ns_utils
import remote_operations

from typing import Literal, Callable

class Coordinator:
    def __init__(self, host, port, refresh_time) -> None:
        self.host = host
        self.port = port
        self.available_ftp={} 
        self.available_coordinator={}
        self.refresh_time = refresh_time
        self.ftp_tree= {}
        self.write_operations = Queue() 
        pass


    def _get_avalible_nodes(self,
                                type: Literal['ftp', 'coordinator']
                                ):
        return ns_utils.ns_lookup_prefix(type)

    def _refresh_ftp_nodes(self):
        """
        Toma todos los servidores ftp en el servidor de nombres y comprueba conectividad
        ,filtra los validos y los guarda y manda a elminar los invalidos en el ns. 
        """

        ftp_nodes_in_name_server: dict[str, tuple[str,int]]= self._get_avalible_nodes('ftp')
        valid_ftp: dict[str, tuple[str,int]] = {} 
        exist_changes= False 
        for name,ftp_addr in ftp_nodes_in_name_server.items():  
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(5) 
                    s.connect(ftp_addr)
                    #se comprueba que el servidor ftp este aceptando conexiones

                    if s.recv(2048).decode('ascii').split(' ')[0] == '220':
                        s.send(f"SETCOORD {self.port}".encode('ascii'))

                        resp =s.recv(2048).decode('ascii').split(' ')[0]

                        if resp == '200':
                            valid_ftp[name] = ftp_addr
                            if name not in self.available_ftp:
                                exist_changes = True 
                                logging.info(f'New ftp server {name}::{ftp_addr}')
                        else:
                            raise ConnectionError('Bad Connection')
                    else:
                        raise ConnectionError('Bad Connection')
                    s.send(b'QUIT')
            except (TimeoutError, OSError, ConnectionError) as e:
                # en caso de que no se logre conectark
                ns_utils.ns_remove_name(f"ftp_{name}")
                exist_changes = True 
                logging.info(f'{e}::Removing ftp server {name}.')
                pass

        if exist_changes:
            logging.info(f"Total current FTPs: {len(valid_ftp)}")
        self.available_ftp = valid_ftp 

    def _refresh_loop(self,func: Callable):
        while True:
            func()
            time.sleep(self.refresh_time)

    def _replicate_write_operation(self,*, emiter_node_name: str, f: Callable, **args):
        for name, (host,port) in self.available_ftp.items():
            if emiter_node_name!=name:
                try:
                    f(**args, replication_addr=(host,port))
                except:
                    # TODO Hacer algo cuando falle la replicacion !
                    logging.info(f'Failed command replication\
from f{emiter_node_name} to f{name}.')
                    pass


    def handle_conn(self, conn: socket.socket, addr):
        """ Repetir la orden a cada uno de los ftps"""
        conn.settimeout(10)
        try:
            request=conn.recv(1024).decode('ascii')
            request=request.split()

            ftp_id = request.pop(0)
            request[0]=request[0].upper()

            logging.info(f'Replicating command from {ftp_id}::{" ".join(request)}')

            match request:
                case ['STOR', *path]:
                    path = ' '.join(path)
                    self._replicate_write_operation(emiter_node_name=ftp_id,
                                                    f=remote_operations.ftp_to_ftp_copy,
                                                    emiter_addr=self.available_ftp[ftp_id],
                                                    file_path1=path,
                                                    file_path2=path,)

                case ['MKD', *path]:
                    path = ' '.join(path)
                    self._replicate_write_operation(
                        f=remote_operations.create_folder,
                        emiter_node_name=ftp_id,
                        path=path,
                    )

                case ['DELE', *path]:
                    path = ' '.join(path)
                    self._replicate_write_operation(
                        f=remote_operations.delete_file,
                        emiter_node_name=ftp_id,
                        path=path,
                    )

                case ['RMD', *path]:
                    path = ' '.join(path)
                    self._replicate_write_operation(
                        f=remote_operations.delete_folder,
                        emiter_node_name=ftp_id,
                        path=path,
                    )

        except TimeoutError:
            #print('Timeout')
            logging.error(f"Connection Timeout {addr}")
        finally:
            conn.close()



    def run(self):
        # TODO verificar primero que no haya ningun otro coordinador activo
        threading.Thread(target=self._refresh_loop,args=(self._refresh_ftp_nodes,)).start()

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.listen() 

            logging.info("Server Starting")
            while True:
                conn, addr = s.accept()
                #print(addr, 'with writing operation.')
                logging.info(f"{addr} with write operation.")

                threading.Thread(target=self.handle_conn, args=(conn,addr)).start()


        pass


if __name__ == '__main__':
    pass