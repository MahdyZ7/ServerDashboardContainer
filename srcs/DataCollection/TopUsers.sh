#!/bin/bash

# Function to get disk space usage for a user
get_disk_usage() {
	if [ -d  /home/$1 ] ; then
		files=$(find /eda_work/ -user $1 -maxdepth 1 2> /dev/null)
    	if [[ ! $files == *"/eda_work/$1"* ]]; then
			files="$files /eda_work/$1"
		fi
		du -scb /home/$1 $(find /eda_work/ -user $1 -maxdepth 1 2> /dev/null) 2> /dev/null | tail -1 | awk '{printf("%.2f"), $1/1024/1024/1024}'
	else
		echo nan
	fi
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
	printf "%-20s %-8s %-8s %-8s %-8s %-15s %-15s %-20s\n" "USERNAME" "CPU%" "MEM%" "DISK(GB)" "PROCS" "TOP_PROCESS" "LAST_LOGIN" "FULLNAME"
	printf "%20s %8s %8s %8s %8s %15s %15s %20s\n" "--------------------" "--------" "--------" "--------" "--------" "---------------" "---------------" "--------------------"
fi 
for user in $users
do
	full_name=$(get_full_name $user)
	# no_of_processes=$(get_no_of_processes $user)
	last_login=$(get_last_login $user)
	# cpu_mem_usage=$(get_usage_stats $user $users_stats)
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
	printf "%-20s %-8s %-8s %-8s %-8s %-15s %-15s %-20s\n" "$user" "$cpu" "$mem" "$disk_usage" "$procs" "$top_process" "$last_login" "$full_name"
done | sort -k3,3rn -k2,2rn -k4,4rn

