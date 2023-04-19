import socket
import json
from typing import Literal
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
        
        while True:  
            print(f"searching for {type}")

            setattr(self,f'available_{type}',ns_utils.ns_lookup_prefix(type))

            #TODO verificar si las direcciones son accesibles todavia
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
        threading.Thread(target=self._refresh_avalible_nodes, args=('ftp',)).start()
        
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