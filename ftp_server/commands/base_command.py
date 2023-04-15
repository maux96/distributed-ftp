from ..context import Context


class BaseCommand:

    @classmethod
    def _resolve(cls,context: Context, args: list[str]):
       """
            Process the command
       """

    @classmethod
    def name(cls):
        return cls.__name__[:-7]