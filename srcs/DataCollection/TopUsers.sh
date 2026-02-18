#!/usr/bin/env bash

# Function to get disk space usage for a user
get_disk_usage() {
	if [ -d  /home/$1 ] ; then
		files=$(find /eda_work/ -maxdepth 1 -user "$1" 2> /dev/null)
    	if [[ ! $files == *"/eda_work/$1"* ]]; then
			files="$files /eda_work/$1"
		fi
		du -scb /home/$1 $files 2> /dev/null | tail -1 | awk '{printf("%.2f"), $1/1024/1024/1024}'
	else
		echo nan
	fi
}

# Function to get cumulative I/O bytes for all processes owned by a user
get_user_io() {
	local user="$1"
	local total_read=0
	local total_write=0
	for pid in $(pgrep -u "$user" 2>/dev/null); do
		local io_file="/proc/$pid/io"
		if [ -r "$io_file" ]; then
			read_bytes=$(awk '/^read_bytes:/ {print $2}' "$io_file" 2>/dev/null)
			write_bytes=$(awk '/^write_bytes:/ {print $2}' "$io_file" 2>/dev/null)
			total_read=$((total_read + ${read_bytes:-0}))
			total_write=$((total_write + ${write_bytes:-0}))
		fi
	done
	echo "$total_read $total_write"
}

# Function to get all memory and CPU usage stats for all users
get_all_usage_stats() {
	ps -eo user:20,%cpu,%mem,comm | awk '{ 
		user=$1;
		cpu=$2;
		mem=$3;
		if (!users[user]) {
			users[user]=1;
			user_cpu[user]=0;
			user_mem[user]=0;
			process_count[user]=0;
		}
		user_cpu[user] += cpu;
		user_mem[user] += mem;
		process_count[user] += 1;
		if (cpu >= top_cpu[user]) {
			top_cpu[user] = cpu;
			top_process[user] = $NF;
		}
	}
	END {
		for (user in users) {
			printf("%s %s %s %s %s\n", user, user_cpu[user], user_mem[user], process_count[user], top_process[user]);
		}
	}'
}

# get_usage_stats() {
# 	ps -u $1 -o %cpu,%mem 2> /dev/null | awk '{sum_cpu+=$1;sum_mem+=$2} END {print sum_cpu " " sum_mem}'
# }

# Function to get user stats from the collected data
get_user_stats() {
	echo "$2" | grep "^$1 " | awk '{printf("%.2f %.2f %d %s %s"), $2, $3, $4, $5, $6}'
}

get_last_login() {
	last -n 1 -F  $1 | head -n 1 | awk '{printf("%s-%s-%s", $6, $5, $8) }'
}

get_no_of_processes() {
	ps -u $1 | wc -l | awk '{print $1-1}'
}

get_full_name() {
	gecos=$(getent passwd $1 | awk -F: '{print $5}' | sed 's/ /_/g')
	if [ -z "$gecos" ]; then
		echo "N/A"
	else
		echo $gecos
	fi
}

# killall -o 12h ping

# Get all users
users=$(getent passwd | grep "/bin/.*sh" | awk -F: '{print $1}' | sort -u)
headers=true
collect_disk=false
disk_usage="OFF"
users_stats=$(get_all_usage_stats)
while [ $# -ne 0 ]; do
	if [ "$1" = "--no-headers" ]; then
		headers=false
	elif [ "$1" = "--collect-disk" ]; then
		collect_disk=true
	fi
	shift
done
if $headers; then
	printf "%-20s %-8s %-8s %-8s %-8s %-15s %-15s %-20s %-15s %-15s\n" "USERNAME" "CPU%" "MEM%" "DISK(GB)" "PROCS" "TOP_PROCESS" "LAST_LOGIN" "FULLNAME" "IO_READ(B)" "IO_WRITE(B)"
	printf "%20s %8s %8s %8s %8s %15s %15s %20s %15s %15s\n" "--------------------" "--------" "--------" "--------" "--------" "---------------" "---------------" "--------------------" "---------------" "---------------"
fi
for user in $users
do
	full_name=$(get_full_name $user)
	last_login=$(get_last_login $user)
	cpu_mem_usage=$(get_user_stats $user "$users_stats")
	if [ -z "$cpu_mem_usage" ]; then
		cpu_mem_usage="0.00 0.00 0 N/A"
	fi
	cpu=$(echo $cpu_mem_usage | awk '{print $1}')
	mem=$(echo $cpu_mem_usage | awk '{print $2}')
	procs=$(echo $cpu_mem_usage | awk '{print $3}')
	top_process=$(echo $cpu_mem_usage | awk '{print $4}')
	if $collect_disk; then
		disk_usage=$(get_disk_usage $user)
	fi
	io_data=$(get_user_io $user)
	io_read=$(echo $io_data | awk '{print $1}')
	io_write=$(echo $io_data | awk '{print $2}')
	printf "%-20s %-8s %-8s %-8s %-8s %-15s %-15s %-20s %-15s %-15s\n" "$user" "$cpu" "$mem" "$disk_usage" "$procs" "$top_process" "$last_login" "$full_name" "${io_read:-0}" "${io_write:-0}"
done | sort -k3,3rn -k2,2rn -k4,4rn

