from ..context import Context


class BaseCommand:

    require_auth = False 

    @classmethod
    def resolve(cls, context: Context, args: list[str]):
        if cls.require_auth and context.user_name != 'admin':
            context.send_control_response(530, 'Not logued in as admin')
            return

        cls._resolve(context, args)

    @classmethod
    def _resolve(cls,context: Context, args: list[str]):
       """
            Process the command
       """

    @classmethod
    def name(cls):
        return cls.__name__[:-7]