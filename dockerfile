
FROM docker.uclv.cu/python:3.10-alpine3.18

WORKDIR /app 

COPY . .

#RUN pip3 install -r requirements.txt  --index-url http://nexus.prod.uci.cu/repository/pypi-proxy/simple/ --trusted-host nexus.prod.uci.cu

RUN mkdir /storage/\ 
    && cp bash_operations/init_server.sh /usr/bin/init_server.sh\
    && cp bash_operations/create_coord.sh /usr/bin/create_coord\
    && cp bash_operations/create_ftp.sh /usr/bin/create_ftp\
    && cp bash_operations/create_ns.sh /usr/bin/create_ns
    
EXPOSE 21

