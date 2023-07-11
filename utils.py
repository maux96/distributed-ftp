import socket


def create_tcp_socket() -> socket.socket:
    return socket.socket(socket.AF_INET, socket.SOCK_STREAM)


def connect_socket_to(host, port, timeout=5) -> socket.socket | None:
    try:
        sock = create_tcp_socket()
        sock.settimeout(timeout)
        sock.connect((host, port))
    except (ConnectionError, TimeoutError, OSError):
        return None

    return sock


def create_socket_and_listen(host, port):
    try:
        sock = create_tcp_socket()
        sock.bind((host, port))
        sock.listen()
        return sock
    except (ConnectionError, OSError, TimeoutError):
        return None


def commands_logs(logs_dict: dict):
    result = "\n"
    for hash, logs in logs_dict.items():
        result += str(hash) + ": \n"
        for index, log in enumerate(logs):
            # index, opertation,  
            route = ' '.join(log[1][1:])
            result += f"{index} - {log[1][0]} - {route[: min(len(route), 20)]} ...\n"
    return result

def last_ftp_operations(ftps: dict):
    result = "\n"
    for ftp_name, ftp_value in ftps.items():
        result+=f"+{ftp_name} ({ftp_value['host']}:{ftp_value['port']}):\n" 
        for hash, last_operation in ftp_value['last_operations_id'].items():
            result+=f"  - {hash}: {last_operation}\n"
    return result
     
