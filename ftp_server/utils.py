import os
import pathlib

def transform_string_into_addrs(repr: str):
    tokens=repr.split(',')
    return (
        '.'.join(tokens[:4]),
        int(tokens[-2])*256 + int(tokens[-1])
    )

def transform_addrs_into_string(host: str, port: int):
    ip_addr = ','.join(host.split('.'))
    p1,p2 = port//256, port%256
    return f'{ip_addr},{p1},{p2}'


def prepare_command_args(line: bytes, encoding='ascii') :
    val=str(line, encoding=encoding)
    tokens = val.split()
    tokens[0] = tokens[0].upper()
    return tokens 

def verify_and_get_valid_path(actual_path: pathlib.Path | str,
                              route: pathlib.Path | str,
                              is_directory: bool = True):

    f =  os.path.isdir if is_directory else os.path.isfile 

    actual_path = pathlib.Path(actual_path)
    route = pathlib.Path(route)

    return (f(route), route)\
                if route.is_absolute()\
                else (f(actual_path / route), actual_path/route)
