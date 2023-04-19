import socket
import threading
import random
import ns_utils
import time
import json

TIME_OUT = 60 

class Proxy:
    def __init__(self, host, port) -> None:
        self.host=host
        self.port=port
        self.available_ftps: dict = {}

    def get_available_ftp(self):
        """TODO obtener los servidores FTP disponibles"""
       # por ahora que el mismo le pregunte al ns
       #return ns_utils.ns_lookup_prefix(prefix='ftp')
       
        analizer_list=ns_utils.ns_lookup_prefix(prefix='analizer')
        print(analizer_list)
        for name,a in analizer_list.items():
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    first_analizer= a 
                    print(first_analizer)
                    s.connect(first_analizer) 
                    s.send(b'ftp')
                    self.available_ftps= json.loads(s.recv(2048))
                    break
            except:
                continue


    def get_best_ftp_server(self):
        """TODO retornar el mejor servidor FTP basado en un criterio"""
        # actualmente el criterio es que sea random :D
        return tuple(
            list(self.available_ftps.values())[random.randint(0,len(self.available_ftps)-1)]
            )

    @staticmethod
    def read_from_socket_and_send(from_: socket.socket,to_: socket.socket):
        from_addr = from_.getpeername()
        to_addr = to_.getpeername()
        try: 
            while data:=from_.recv(2048):
                to_.send(data)
        except (TimeoutError, OSError):
            print('Time Out for',from_addr,'->', to_addr)
        finally:
            from_.close()
            to_.close() 
    
    def handle_conn(self,conn: socket.socket,addr):
        remote_server=self.get_best_ftp_server()


        print('connecting',addr,'with',remote_server)

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as ftp_soc:
                ftp_soc.settimeout(TIME_OUT)
                ftp_soc.connect(remote_server)

                t1 = threading.Thread(target=Proxy.read_from_socket_and_send,
                                args=(conn,ftp_soc))

                t2= threading.Thread(target=Proxy.read_from_socket_and_send,
                                args=(ftp_soc,conn))
                
                t1.start()
                t2.start()

                while t1.is_alive() and t2.is_alive():
                    t1.join(1)
                    t2.join(1)

                ftp_soc.close()
                    
                time.sleep(5)
                print(t1.is_alive(), t2.is_alive())
        finally: 
            print('Connection closed with', addr)
            conn.close()

    def run(self):
        #TODO ver cuando pedir actualizacion por parte del analizer
        self.get_available_ftp()

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.listen()

            while True:

                conn,addr = s.accept()
                conn.settimeout(TIME_OUT)
                print('connected to',addr)

                threading.Thread(target=self.handle_conn, args=(conn, addr)).start()