total_ftps=3
total_coords=1
root_places=~/distributed-ftp-testing

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

printf "opening a pyro-ns instance\n"
printf "opening total ftps : %s\n" "$total_ftps"
printf "opening total coordinators : %s\n" "$total_coords"
printf "opening total root_places : %s\n" "$root_places"

source ../env/bin/activate

kitty sh -c "pyro5-ns" &
pids[0]=$!

# open ftps
for i in $(seq $total_ftps);
do
    mkdir $root_places/$i 2>/dev/null
    kitty sh -c "python3 main.py ftp --id $i --port $((i+1))001 --root-dir $root_places/$i" &
    pids[$i]=$!
done

for i in $(seq $total_coords);
do
    kitty sh -c "python3 main.py coordinator --id $i"  &
    pids[(($total_ftps+1+$i))]=$!
done

read -p "Press Enter to kill all the executed processes..."

for p in ${pids[@]}; do
  echo ">> Killing ${p}"
  kill -KILL $p
done


