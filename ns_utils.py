import Pyro5.api
from Pyro5.nameserver import NameServer
from Pyro5.errors import NamingError
from Pyro5.api import URI

import logging

def ns_register(name: str ,host: str, port: int, ns: NameServer | None = None):
    if ns is None:
        ns=Pyro5.api.locate_ns()

    ns: NameServer
    ns.register(name,f'PYRO:{name}@{host}:{port}')

    logging.info(f"{name} register in the nameserver!")


def ns_lookup(name, ns: NameServer | None = None ) -> None | tuple[str, int]:
    if ns is None:
        ns=Pyro5.api.locate_ns()

    try:
        ns: NameServer
        uri: URI = ns.lookup(name)
    except NamingError:
        # si no encuentra
        return None
    
    return uri.host, uri.port

def ns_lookup_prefix(prefix, ns: NameServer | None = None ):
    """
    Retorna un diccionario con los nombres (sin los prefijos) como claves
    y las (direccion, puerto) como valor.
    """

    if ns is None:
        ns=Pyro5.api.locate_ns()
    sol = {} 
    for k,v in ns.list(prefix=prefix).items():
        _,addr=v.split('@')
        host,port=addr.split(':')
        sol[k[len(prefix)+1:]] = (host, int(port))
    return sol

def ns_remove_name(name , ns: NameServer | None = None ): 
    if ns is None:
        ns=Pyro5.api.locate_ns()

    return ns.remove(name)

        