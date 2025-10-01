#!/bin/bash

ARCH=$(uname -srvmo)
OS_NAME=$(lsb_release -i | awk '{print $3}')
OS_VER=$(lsb_release -r | awk '{print $2}')
OS="$OS_NAME $OS_VER"

PCPU=$(cat /proc/cpuinfo | grep 'physical id' | sort -u | wc -l)
VCPU=$(cat /proc/cpuinfo | grep processor | sort -u | wc -l)

RAM_DATA=$(free -m | grep Mem)
RAM_TOTAL=$(echo "$RAM_DATA" | awk '{printf("%.2fG"), $2/1024.0}')
RAM_USED=$(echo "$RAM_DATA" | awk '{printf("%.2fG"), $3/1024.0}')
RAM_PERC=$(echo "$RAM_DATA" | awk '{printf("%.0f"), $3 / $2 * 100}')

DISK_DATA=$(df -h -l --total | grep total)
DISK_TOTAL=$(echo "$DISK_DATA" | awk '{print $2}')
DISK_USED=$(echo "$DISK_DATA" | awk '{print $3}')
DISK_PERC=$(echo "$DISK_DATA" | awk '{printf("%s%%"), $5}')

CPU_LOAD=$(cat /proc/loadavg | awk '{print $1 "," $2 "," $3}')
#CPU_LOAD=$(uptime | awk '{print $(NF-2) $(NF-1) $NF}')
LAST_BOOT=$(who -b | awk '{print($3 " " $4)}')
TCP=$(awk '/TCP:/ {print $3}' /proc/net/sockstat)
USER_LOG=$(who | awk '{print $1}' | sort -u | wc -l)

Active_CONNECTIONS=$(lsof -n -iTCP -sTCP:ESTABLISHED | grep -E 'sshd|Xvnc')
ACTIVE_VNC=$(echo "$Active_CONNECTIONS" | grep '^Xvnc' | wc -l)
ACTIVE_SSH=$(echo "$Active_CONNECTIONS" | grep '^sshd' | wc -l)

# Active_virtuoso=$(pgrep -c virtuoso | wc -l)
#top_process_users=$(ps -eo user:20,etime,pcpu,pmem,cmd --sort=-pcpu | head -n 5)
#top_process_mem=$(ps -eo user:20,etime,pcpu,pmem,cmd --sort=-pmem | head -n 5)
#ps -eo pid,user:20,%cpu,%mem,cmd | sort -k4,4nr | head -n 5
#ps -eo pid,user:20,%cpu,%mem,cmd | sort -k3,3nr | head -n 5
line_format=false
while [ $# -ne 0 ]; do
	if [ "$1" = "--line-format" ]; then
		line_format=true
	fi
	shift
done

if $line_format; then
	printf "$ARCH,$OS,$PCPU,$VCPU,$RAM_USED/$RAM_TOTAL,$RAM_PERC,\
$DISK_USED/$DISK_TOTAL,$DISK_PERC,$CPU_LOAD,$LAST_BOOT,\
$TCP,$USER_LOG,$ACTIVE_VNC,$ACTIVE_SSH\n"
else
	printf "%-25s: %s\n" "Architecture" "$ARCH"
	printf "%-25s: %s\n" "OS" "$OS"
	printf "%-25s: %d\n" "Physical CPUs" "$PCPU"
	printf "%-25s: %d\n" "Virtual CPUs" "$VCPU"
	printf "%-25s: %s/%s (%.0f%%)\n" "RAM" "$RAM_USED" "$RAM_TOTAL" "$RAM_PERC"
	printf "%-25s: %s/%s (%s)\n" "Disk" "$DISK_USED" "$DISK_TOTAL" "$DISK_PERC"
	printf "%-25s: %s\n" "CPU Load (1, 5, 15 min)" "$CPU_LOAD"
	printf "%-25s: %s\n" "Last Boot" "$LAST_BOOT"
	printf "%-25s: %d\n" "TCP Connections" "$TCP"
	printf "%-25s: %d\n" "User Logins" "$USER_LOG"
	printf "%-25s: %d\n" "Active VNC Sessions" "$ACTIVE_VNC"
	printf "%-25s: %d\n" "Active SSH Sessions" "$ACTIVE_SSH"
fi


