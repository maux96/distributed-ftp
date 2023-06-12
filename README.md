
# Proyecto de Computación Distribuida

### Integrantes:
- (@maux96) Mauricio Salim Mahmud Sánchez C412
- (@rb58853) Raúl Beltrán Gómez C412
- Víctor Manuel Amador Sosa C412

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

### Sincronización:

Para mantener la sincronización entre los coordinadores se aplican las siguientes estrategias:

- Se aplica el algoritmo de bully para la selección de líder: En todo momento, cada coordinador intenta hacer ping a su líder. En caso de no recibir respuesta, el nodo inicia el proceso de selección de líder, grita para arriba (es decir, pregunta a todos los coordinadores que considera mejores que él) y si aparece uno que es mejor, sale de la selección. Si nadie devuelve "OK", entonces todos los coordinadores mejores que él están desconectados y automáticamente pasa a ser líder. Al hacerse cambio de líder, el grupo de co-líderes se actualiza a solo el líder. El líder estará todo el tiempo pidiendo selección, esto tiene como objetivo que si entra un coordinador menor a la red, se le asigna el líder de la red como nuevo líder y, de ser necesario, se pide sincronización.
- Se mantienen co-líderes con la información completa necesaria para que, en caso de que se caiga el líder, estos líderes secundarios asuman el papel del líder sin perder información. Los FTP estarán escribiendo operaciones tanto en el líder como en los co-líderes. El número de co-líderes es variable, mientras más co-líderes, menos posible es que se pierda toda la información, pero a más cantidad, la red también está más congestionada.
- Los co-líderes son seleccionados con un proceso similar al algoritmo de bully, la diferencia es que para seleccionar un co-líder se pregunta cuántos hay mejores que yo. Si hay $k$, se para la ejecución y se deduce que este que llama al proceso de selección de co-líder no debe serlo. En caso contrario (no hay $k$ mejores que él), entonces debe pertenecer al grupo de co-líderes. El orden está establecido por un orden lexicográfico, A es mejor que B si el nombre de A es menor que B lexicográficamente.
- Las operaciones de los FTP se escriben sobre un hash. Tanto el líder como los co-líderes comparten el mismo hash. Si un líder se cae (se desconecta de la subred), el nuevo que ocupa la posición de líder tendrá que cambiar el hash y compartirlo con los nuevos co-líderes. Luego de esto, los FTP conectados en esta subred comenzarán a escribir en el nuevo hash. Esta estrategia de uso de hash permite que la red se subdivida, se continúe escribiendo por cada lado y luego se unan las operaciones. Si no se utilizara esto, al hacer merge en las operaciones de cada subred, se solaparían y no se sincronizaría bien. Cabe destacar que en un hash solo puede estar escribiendo una subred a la vez, de acuerdo con cómo se definió el mismo.
- Cuando entra un nuevo líder o co-líder de una subred a otra distinta, se pide sincronizar con este. El líder (de la subred en la que se entró) es el encargado de detectar estos nuevos integrantes con información para hacer merge. Lo detecta de la siguiente forma: pregunta a cada coordinador de la red si en su local es líder (si para sí mismo son líderes). Si esto pasa, entonces hay dos líderes, lo que significa que se unió un líder de otra red o un líder que fue líder de esta y se cayó. Además, también pregunta si es co-líder y no tiene como líder el mismo que está preguntando. En ese caso, puede ocurrir que pida una sincronización. De esta forma, se evita el caso donde se conectan dos redes y al mismo tiempo se cae un líder. Al no encontrar el líder, se pide sincronización al co-líder.
- El merge se hace de la siguiente manera: por cada hash en el diccionario, el líder resultante mantendrá asociado a ese hash el log de operaciones con mayor cardinalidad (más operaciones tenga asociadas a ese hash). Se garantiza que en un hash solo puede escribir una subred, por lo que si la cantidad de operaciones asociadas a un hash es menor en un coordinador que en otro, significa que en algún momento se dividió la red y continuó escribiendo el antiguo líder por otro lado en el hash que se mantuvo (el hash original se mantiene porque para sí mismo no se cae nadie de la red). En este caso,el hash más grande sustituye al primero sin solapar ninguna operación. El log de menor cantidad de operaciones será un subconjunto del log con más operaciones.
- Cuando entra un nuevo co-líder al grupo de liderazgo, este último le pide sincronización al líder de este grupo y se le asigna a este nuevo co-líder la información del líder. Cuando un líder se cae y uno de los co-líderes pasa a ser líder, en ese momento, el grupo de líderes será solo el nuevo líder, y se inicia el proceso de selección de co-líderes nuevamente. Nótese que se pueden caer $k-1$ líderes al mismo tiempo que el $k$-ésimo líder. Si tiene la información original, asumirá el liderazgo sin perder información relevante.

### Pérdida de información:

- Si todos los coordinadores del grupo de líderes se caen al mismo tiempo, se pierde la información actual. Mientras uno de estos no se vuelva a conectar, no se recuperará la información acumulada.

---
## Discoverer

Inicialmente para el descubrimento de los nodos en la red se usó el servidor de nombres de Pyro5, pero este daba muchos problemas cuando se subdividía la red, por lo que se decidió hacer descubrimiento basado en broadcast usando puertos fijos en cada nodo.
