import socket
import json
from typing import Literal, Callable
import threading
import time

import ns_utils

class Analizer:
    def __init__(self,host, port, refresh_time=10) -> None:
        self.host = host
        self.port = port
        self.available_ftp={} 
        self.available_proxy={}
        self.available_analizer={}
        self.refresh_time = refresh_time
        pass


    def _refresh_avalible_nodes(self,
                                type: Literal['ftp', 'proxy', 'analizer']
                                ):
        #TODO verificar que hacer cuando no encuentra el servidor de nombres,
        setattr(self,f'available_{type}',ns_utils.ns_lookup_prefix(type))

    def _refresh_ftp_nodes(self):
        """
        Toma todos los servidores ftp en el servidor de nombres y comprueba conectividad
        ,filtra los validos y los guarda y manda a elminar los invalidos en el ns. 
        """
        self._refresh_avalible_nodes('ftp')
        valid_ftp: dict[str, tuple[str,int]] = {} 
        for name,ftp_addr in self.available_ftp.items():  
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(5) 
                    s.connect(ftp_addr)
                    #se comprueba que el servidor ftp este aceptando conexiones
                    if s.recv(2048).decode('ascii').split(' ')[0] == '220':
                        valid_ftp[name] = ftp_addr
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
    
    def handle_conn(self, conn: socket.socket):
        conn.settimeout(10)
        try:
            request=conn.recv(1024).decode('ascii')

            if request in ['ftp', 'proxy', 'analizer']:
                conn.send(
                    json.dumps(getattr(self,f'available_{request}')).encode('ascii')
                )
            else:
                conn.send(('{"error":"'+request+'"}').encode('ascii'))
        except TimeoutError:
            print('Timeout')
        finally:
            conn.close()



    def run(self):
        #threading.Thread(target=self._refresh_ftp_nodes).start()
        threading.Thread(target=self.refresh_loop,args=(self._refresh_ftp_nodes,)).start()
        
        print('Starting!')
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.listen() 
            while True:
                conn, addr = s.accept()
                print(addr, 'asking for directions')

                threading.Thread(target=self.handle_conn, args=(conn,)).start()


if __name__ == '__main__':
    Analizer('127.0.0.1', 3000,10).run()
    pass