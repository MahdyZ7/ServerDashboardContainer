#!/bin/bash

# Function to get disk space usage for a user
get_disk_usage() {
	if [ $(id -u) = 0 ] && [ -d  /home/$1 ] ; then
    	du -sb /home/$1 2> /dev/null | awk '{printf("%.2f"), $1/1000000000}'
	else
		echo nan
	fi
}

get_usage_stats() {
	ps -u $1 -o %cpu,%mem 2> /dev/null | awk '{sum_cpu+=$1;sum_mem+=$2} END {print sum_cpu " " sum_mem}'
}

# Get all users
users=$(getent passwd | grep "/bin/.*sh" | awk -F: '{print $1}')
# passwd_users=$(getent passwd | awk -F: '{print $1}')
# ps -eo %cpu,%mem,cmd --sort=-%cpu | awk 'NR==2 {print $3}' | xargs -n1 basename

for user in $users
do
    # cpu_usage=$(get_cpu_usage $user)
    # memory_usage=$(get_memory_usage $user)
	cpu_mem_usage=$(get_usage_stats $user)
    disk_usage=$(get_disk_usage $user)

    printf  "%s %s %s\n" "$user" "$cpu_mem_usage" "$disk_usage"
done | sort -k2,2rn -k3,3rn -k4,4rn

