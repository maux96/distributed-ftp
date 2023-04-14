import socket

def send_control_response(
        conn: socket.socket,
        code: int,
        message: str,
        encoding='ascii'):
    conn.send(bytes(f"{code} {message}\r\n", encoding=encoding))