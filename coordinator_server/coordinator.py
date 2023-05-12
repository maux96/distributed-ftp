import socket
import time
import threading
from queue import Queue

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
        for name,ftp_addr in ftp_nodes_in_name_server.items():  
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(5) 
                    s.connect(ftp_addr)
                    #se comprueba que el servidor ftp este aceptando conexiones
                    if s.recv(2048).decode('ascii').split(' ')[0] == '220':
                        valid_ftp[name] = ftp_addr
                        s.send(f"SETCOORD {self.port}".encode('ascii'))
                    else:
                        raise ConnectionError('Bad Connection')
                    s.send(b'QUIT')
            except (TimeoutError, OSError, ConnectionError):
                # en caso de que no se logre conectar
                ns_utils.ns_remove_name(name)
                pass
        self.available_ftp = valid_ftp 

    def refresh_loop(self,func: Callable):
        while True:
            func()
            time.sleep(self.refresh_time)

    def handle_conn(self, conn: socket.socket, addr):
        """ Repetir la orden a cada uno de los ftps"""
        conn.settimeout(10)
        try:
            request=conn.recv(1024).decode('ascii')
            request=request.split()
            ftp_id = request.pop(0)
            request[0]=request[0].upper()
            match request:
                case ['STOR', path]:
                    
                    pass

                case ['MKD', path]:

                    for name, (host,port) in self.available_ftp:
                        if ftp_id!=name:
                            remote_operations.create_folder((host, port), path)

                case ['DELE', path]:
                    pass

                case ['RMD', path]:
                    pass

        except TimeoutError:
            print('Timeout')
        finally:
            conn.close()



    def run(self):
        # TODO verificar primero que no haya ningun otro coordinador activo
        threading.Thread(target=self.refresh_loop,args=(self._refresh_ftp_nodes,)).start()

        print('Starting!')
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.listen() 
            while True:
                conn, addr = s.accept()
                print(addr, 'with writing operation.')

                threading.Thread(target=self.handle_conn, args=(conn,addr)).start()


        pass


if __name__ == '__main__':
    pass