
from .base_command import BaseCommand
from .context import Context
from .response import send_control_response
from ..utils import verify_and_get_valid_path

import pathlib
import subprocess


class LISTCommand(BaseCommand):
    @classmethod
    def _resolve(cls,context: Context, args: list[str]):
        path_ = pathlib.Path(*args) if args else context.current_path 

        # TODO verificar que haya conexion de datos...
        send_control_response(context.control_connection,
                             125,'Data connection already open; transfer starting.')

        data_conn, data_addr= context.data_connection.accept()
        data_conn.send(cls.list_dir(path_ ))

        data_conn.close()

        send_control_response(context.control_connection,
                             226,'Closing data connection.')

    @staticmethod
    def list_dir(route):
        result = subprocess.run(['ls','-l', route],
                  stdout=subprocess.PIPE,
                  stderr=subprocess.PIPE).stdout
        return result 


class RETRCommand(BaseCommand):
    @classmethod
    def _resolve(cls,context: Context, args: list[str]):
        path_name =' '.join(args) 
        is_valid,file_abs_route = verify_and_get_valid_path(
            context.current_path,
            path_name,
            is_directory=False)

        if is_valid:
            # TODO verificar que haya conexion de datos como pasv
            send_control_response(context.control_connection,
                             125,'Data connection already open; transfer starting.')

            data_conn, _= context.data_connection.accept()

            #TODO verificar que no halla errores al crear el archivo
            with open(file_abs_route, 'rb') as fd:
                total_send=data_conn.sendfile(fd)
                print('Total Send:',total_send)
            data_conn.close() 

            send_control_response(context.control_connection,
                             226,'Closing data connection.')
        else:
            send_control_response(context.control_connection,
                             501,'Invalid Directory.')


class STORCommand(BaseCommand):
    @classmethod
    def _resolve(cls,context: Context, args: list[str]):
        path_name =pathlib.Path(' '.join(args))
        parent_dir = path_name.parent
        file_name = path_name.name
                    

        is_valid,file_abs_route = verify_and_get_valid_path(
            context.current_path,
            parent_dir,
            is_directory=True)
        #TODO verificar ademas si el archivo file_name existe, de ser asi responder
        # con el codigo asociado

        if is_valid:
            send_control_response(context.control_connection,
                             125,'Data connection already open; transfer starting.')


            data_conn, data_addr= context.data_connection.accept()
            with open(file_abs_route/file_name, 'wb') as fd:
                while chunk:=data_conn.recv(2048):
                    fd.write(chunk)

            data_conn.close() 
            
            send_control_response(context.control_connection,
                             226,'Closing data connection.')


        else:
            send_control_response(context.control_connection,
                             501,'Invalid Directory.')


