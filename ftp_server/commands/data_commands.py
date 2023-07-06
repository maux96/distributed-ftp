
from .base_command import BaseCommand
from ..context import Context

import pathlib
import subprocess


class LISTCommand(BaseCommand):
    @classmethod
    def _resolve(cls,context: Context, args: list[str]):
        if '-a' in args: 
            """para un tipo especifico de ftp (no rfc959)"""
            args.remove('-a')

        if args:
            path = ' '.join(args)
            if not context.is_valid_path(path, is_dir=True):
                context.send_control_response(451,
                    'Requested action aborted: local error in processing.')
                return 
            path = context.get_os_absolute_path(path)
        else: 
            path= context.current_absolute_os_path 


        # TODO verificar que haya conexion de datos...
        context.send_control_response(
            125,'Data connection already open; transfer starting.')

        data_conn = context.data_connection
        data_conn.send(cls.list_dir(path ))

        data_conn.close()

        context.send_control_response(
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
        client_path =' '.join(args) 

        if absolute_file_path:=context.verify_and_get_absolute_os_path(client_path,
                                                                       is_dir=False) :
            # TODO verificar que haya conexion de datos como pasv

            context.send_control_response(125,
                    'Data connection already open; transfer starting.')

            data_conn= context.data_connection

            #TODO verificar que no halla errores al crear el archivo
            with open(absolute_file_path, 'rb') as fd:
                total_send=data_conn.sendfile(fd)
            data_conn.close() 

            context.send_control_response(226,
                    f'Colosing data connection. Sended {total_send}')
        else:
            context.send_control_response(501,
                    'Invalid Directory.')


class STORCommand(BaseCommand):
    @classmethod
    def _resolve(cls,context: Context, args: list[str]):
        path_name =pathlib.Path(' '.join(args))
        parent_dir = path_name.parent
        file_name = path_name.name
                    


        #TODO verificar ademas si el archivo file_name existe, de ser asi responder
        # con el codigo asociado

        if absolute_dir_path:=context.verify_and_get_absolute_os_path(parent_dir,
                                                                       is_dir=True) :
            context.send_control_response(125,
                'Data connection already open; transfer starting.')

            data_conn= context.data_connection
            with open(absolute_dir_path/file_name, 'wb') as fd:
                while chunk:=data_conn.recv(2048):
                    fd.write(chunk)

            data_conn.close() 
            context.send_control_response(226,
                'Closing data connection.')

            ### TODO escribirle al coordinador que esciribio un archivo
            if context.user != 'admin' :
                context.save_write_op('STOR'," ".join(args)) 
           #else: 
           #    context.increse_last_operation()
        else:
            context.send_control_response(501,
                'Invalid Directory.')

class MKDCommand(BaseCommand):
    @classmethod
    def _resolve(cls,context: Context, args: list[str]):
        path_name =pathlib.Path(' '.join(args))
        parent_dir = path_name.parent
        dir_name = path_name.name   

        parent_dir_abs_route = context.verify_and_get_absolute_os_path(parent_dir)
        
        # TODO verificar si existe una carpeta con el mismo nombre
        if parent_dir_abs_route is not None:
            (parent_dir_abs_route/dir_name).mkdir()
            context.send_control_response(257,
                'Directory Created.')

            # TODO: poner un usuario modificable
            if context.user != 'admin':
                context.save_write_op('MKD'," ".join(args)) 
           #else: 
           #    context.increse_last_operation()

        else:
            context.send_control_response(501,
                'Invalid Directory.')

class DELECommand(BaseCommand):
    @classmethod
    def _resolve(cls,context: Context, args: list[str]):
        path_name =pathlib.Path(' '.join(args))

        absolute_path = context.verify_and_get_absolute_os_path(path_name, is_dir=False)

        if absolute_path:
            absolute_path.unlink()
            context.send_control_response(250,
                'File removed')


        if context.user != 'admin':
            context.save_write_op('DELE'," ".join(args)) 
        else:
            #context.increse_last_operation()
            context.send_control_response(550,
                'Requested action not taken.\
File unavailable (e.g., file not found, no access)')

class RMDCommand(BaseCommand):
    @classmethod
    def _resolve(cls,context: Context, args: list[str]):
        path_name =pathlib.Path(' '.join(args))

        absolute_path = context.verify_and_get_absolute_os_path(path_name, is_dir=True)

        if absolute_path:
            try:
                absolute_path.rmdir()
                context.send_control_response(250,
                    'Dir removed.')

                if context.user != 'admin':
                    context.save_write_op('RMD'," ".join(args)) 
               #else:
               #    context.increse_last_operation()
            except: 
                context.send_control_response(550,
                    'Dir contains files.')
        else:
            context.send_control_response(550,
                'Requested action not taken.\
File unavailable (e.g., file not found, no access)')

class RNFRCommand(BaseCommand):

    @classmethod
    def _resolve(cls, context: Context, args: list[str]):
        path_name =pathlib.Path(' '.join(args))
        

        if (absolute_path:=context.verify_and_get_absolute_os_path(path_name, is_dir=False)) or\
           (absolute_path:=context.verify_and_get_absolute_os_path(path_name, is_dir=True)):
            context.reneme_from = absolute_path
            context.send_control_response(350,
                'Requested file action pending further information.')
        else:
            context.send_control_response(450,
                'File not found!')
        

class RNTOCommand(BaseCommand):
    @classmethod
    def _resolve(cls, context: Context, args: list[str]):
        #TODO ver si puede ser un path
        new_name =' '.join(args)
        if context.reneme_from is not None:
            try: 
                context.reneme_from.rename(context.get_os_absolute_path(new_name)) 
                context.send_control_response(250, 'Requested file action okay, completed.')

                if context.user != 'admin':
                    context.save_write_op('RENAME',
                        f"'{context.get_absolute_path_from_os_path(context.reneme_from)}' '{context.get_absolute_path(new_name)}'") 
            except:
                context.send_control_response(553, 'Requested action not taken.')
            finally:
                context.reneme_from = None
        else:
            context.send_control_response(503, 'Bad sequence of commands.')