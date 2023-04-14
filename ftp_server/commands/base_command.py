from .context import Context


class BaseCommand:

    @classmethod
    def _resolve(cls,context: Context, args: list[str]):
       """
           Asumiendo que se puede mandar el comando, intentar resolverlo         
       """

    @classmethod
    def name(cls):
        return cls.__name__[:-7]