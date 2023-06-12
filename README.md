
# Proyecto de Computación Distribuida

### Integrantes:
- Mauricio Salim Mahmud Sánchez C412
- Raúl Beltrán Gómez C412

----
## FTP Node

Ejecutar el servidor:

```bash
python3 main.py ftp --id <ID>\
                    --host <HOST>\
                    --port <PORT>\
                    --root-dir <PATH>
```
Siendo `<ID>` el identificador del ftp, `<HOST>` el host donde se ejecuta, `<PORT>` el puerto donde el ftp abre conexiones con el cliente y `<PATH>` la dirección donde estará la raiz de almacenamiento expuesta al cliente. De no darse el  `<PORT>` este será dado aleatoriamente.

Los nodos FTP almacenana los datos a la vez que brindan el servicio de FTP (respetando los comandos básicos del rfc959). Están comunicandose continuamente con el Nodo coordinador que haya sido seleccionado como lider en un momento dado, así como con los k co-lideres.

El coordinador lider $C_L$ se comunica con el servidor FTP en cuestión y le informa que este es el lider, así como le informa quienes son los k co-lideres $C_{ki}$. Luego en todo momento que se haga una operación de escritura, el FTP informa al lider $C_L$ y a los $C_{ki}$ de esta operación. De no existir un lider disponible el FTP retiene la operación y espera a que haya un coordinador lider disponible.

### Comandos disponibles:

- NOOP
- TYPE
- USER
- PWD 
- QUIT
- PASV
- PORT
- LIST
- RETR
- STOR
- MKD
- DELE
- RMD
- CWD
- CDUP

---
## Coordinator Node
Ejecutar el servidor:
```bash
python3 main.py coordinator --id <ID>\
                            --host <HOST>\
                            --port <PORT>\
```
Siendo `<ID>` el identificador del coordinador, `<HOST>` el host donde se ejecuta, `<PORT>` el puerto donde el coordinador abre conexiones con otros nodos y `<PATH>` la dirección donde estará la raiz de almacenamiento expuesta al cliente. De no darse el  `<PORT>` este será dado aleatoriamente.

El coordinador será responsable de la replicación entre los FTPs así como tener la información para que esto se lleve a cabo.

Va a existir siempre un coordinador que será el lider, el cual va a estar manejando las replicaciones entre FTPs, también van a haber k co-lideres que estarán de respeldando por si se cae el lider principal. 

---
## Discoverer

Inicialmente para el descubrimento de los nodos en la red se usó el servidor de nombres de Pyro5, pero este daba muchos problemas cuando se subdividía la red, por lo que se decidió hacer descubrimiento basado en broadcast usando puertos fijos en cada nodo.