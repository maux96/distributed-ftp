

function _get_ip(){
  ip addr show eth0 | grep 'inet\b' | awk '{print $2}' | cut -d '/' -f1
}

function _get_id_from_ip(){
  _get_ip | awk -F "." '{print $3"-"$4}'
}


function create_server_ftp(){
  python3 main.py ftp --host $(_get_ip) --port 21 --id ftp_$(_get_id_from_ip) --root-dir /storage/
}

function create_coordinator(){
  python3 main.py coordinator --host $(_get_ip) --port 5000 --id coord_$(_get_id_from_ip)
}

function create_ns(){
  #pyro5-ns -n $(_get_ip)
  python3 main.py nameserver --host $(_get_ip) --port 7000 --id ns_$(_get_id_from_ip)
}


