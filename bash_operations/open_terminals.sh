total_ftps=0
total_coords=0
root_places=~/distributed-ftp-testing


IP_ADDRS=$(ip addr show wlo1 | grep 'inet\b' | awk '{print $2}' | cut -d '/' -f1)

while getopts ":f:c:r:h:" opt; do
  case $opt in
    f) total_ftps="$OPTARG"
    ;;
    c) total_coords="$OPTARG"
    ;;
    r) root_places="$OPTARG"
    ;;
    #h) echo "Available args are: -f TOTAL_FTP | -c TOTAL_COORDS | -r ROOT-DIR"
    #exit 0
    #;;
    \?) echo "Invalid option -$OPTARG" >&2
    exit 1
    ;;
  esac

  case $OPTARG in
    -*) echo "Option $opt needs a valid argument"
    exit 1
    ;;
  esac
done

printf "opening total ftps : %s\n" "$total_ftps"
printf "opening total coordinators : %s\n" "$total_coords"
printf "opening total root_places : %s\n" "$root_places"

source ../env/bin/activate

#kitty sh -c "pyro5-ns" &
#pids[0]=$!


for i in $(seq $total_coords);
do
    kitty sh -c "python3 main.py coordinator --id coord-$IP_ADDRS-$i --host $IP_ADDRS --port 1$((i+1))001"  &
    pids[(($total_ftps+1+$i))]=$!
    sleep 2
done

# open ftps
for i in $(seq $total_ftps);
do
    mkdir $root_places/$i 2>/dev/null
    kitty sh -c "python3 main.py ftp --id ftp-$IP_ADDRS-$i --host $IP_ADDRS  --port $((i+1))001 --root-dir $root_places/$i" &
    pids[$i]=$!
    sleep 2
done


read -p "Press Enter to kill all the executed processes..."

for p in ${pids[@]}; do
  echo ">> Killing ${p}"
  kill -KILL $p
done


