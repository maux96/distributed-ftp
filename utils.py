import socket

def create_tcp_socket() -> socket.socket:
    return socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def connect_socket_to(host, port) -> socket.socket:
    sock = create_tcp_socket()
    sock.connect((host, port))
    return sock

def create_socket_and_listen(host, port):
    sock = create_tcp_socket()
    sock.bind((host, port))
    sock.listen()
    return sock