import socket
import threading
import random

HOST,PORT = ('0.0.0.0', 10000)

REMOTE_SERVER = ('0.0.0.0', 4000)

class Proxy:
    def __init__(self, host, port) -> None:
        self.host=host
        self.port=port
        self.available_ftps = []

    def get_available_ftp(self):
        """TODO obtener los servidores FTP disponibles"""
        return [
            ('127.0.0.1', 2050),
            ('127.0.0.1', 2060),
        ]

    def get_best_ftp_server(self):
        """TODO retornar el mejor servidor FTP basado en un criterio"""
        return self.available_ftps[random.randint(0,len(self.available_ftps)-1)]

    @staticmethod
    def read_from_socket_and_send(from_: socket.socket,to_: socket.socket):
        while data:=from_.recv(2048):
            to_.send(data)
     
    
    def handle_conn(self,conn: socket.socket,addr):
        remote_server=self.get_best_ftp_server()


        print('connecting',addr,'with',remote_server)

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as ftp_soc:
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
                    
        finally: 
            print('Connection closed with', addr)
            conn.close()

    def run(self):
        self.available_ftps = self.get_available_ftp()

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.listen()

            while True:

                conn,addr = s.accept()
                print('connected to',addr)

                threading.Thread(target=self.handle_conn, args=(conn, addr)).start()