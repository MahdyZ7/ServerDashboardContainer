#!/usr/bin/env bash

ARCH=$(uname -srvmo 2>/dev/null || echo "Unknown")
OS_NAME=$(lsb_release -i 2>/dev/null | awk '{print $3}' || echo "Unknown OS")
OS_VER=$(lsb_release -r 2>/dev/null | awk '{print $2}' || echo "Unknown Version")
OS="$OS_NAME $OS_VER"

PCPU=$(grep 'physical id' /proc/cpuinfo | sort -u | wc -l)
VCPU=$(grep 'processor' /proc/cpuinfo | sort -u | wc -l)

RAM_DATA=$(free -m | grep Mem)
RAM_TOTAL=$(echo "$RAM_DATA" | awk '{printf("%.2fG"), $2/1024.0}')
RAM_USED=$(echo "$RAM_DATA" | awk '{printf("%.2fG"), $3/1024.0}')
RAM_PERC=$(echo "$RAM_DATA" | awk '{printf("%.0f"), $3 / $2 * 100}')

# Swap usage
SWAP_DATA=$(free -m | grep Swap)
SWAP_TOTAL_MB=$(echo "$SWAP_DATA" | awk '{print $2}')
SWAP_USED_MB=$(echo "$SWAP_DATA" | awk '{print $3}')
SWAP_PERC=$(echo "$SWAP_DATA" | awk '{if ($2 > 0) printf("%.0f", $3/$2*100); else print "0"}')

DISK_DATA=$(df -h -l --total | grep total)
DISK_TOTAL=$(echo "$DISK_DATA" | awk '{print $2}')
DISK_USED=$(echo "$DISK_DATA" | awk '{print $3}')
DISK_PERC=$(echo "$DISK_DATA" | awk '{printf("%s%%"), $5}')

# CPU load averages (1, 5, 15 min)
CPU_LOAD=$(awk '{print $1 "," $2 "," $3}' /proc/loadavg)

# Actual CPU utilization % (sampled from /proc/stat - two reads 0.5s apart for accuracy)
CPU_USAGE=$(awk '/^cpu / {idle1=$5; total1=$2+$3+$4+$5+$6+$7+$8}' /proc/stat; \
	sleep 0.5; \
	awk -v idle1="$idle1" -v total1="$total1" \
		'/^cpu / {idle2=$5; total2=$2+$3+$4+$5+$6+$7+$8; \
		dtotal=total2-total1; didle=idle2-idle1; \
		if (dtotal>0) printf("%.1f", (dtotal-didle)/dtotal*100); else print "0.0"}' \
		/proc/stat 2>/dev/null || echo "0.0")
# Fallback: single-read estimate if two-read approach fails
if [ -z "$CPU_USAGE" ] || [ "$CPU_USAGE" = "0.0" ]; then
	CPU_USAGE=$(grep '^cpu ' /proc/stat | awk '{usage=($2+$4)*100/($2+$3+$4+$5+$6+$7+$8); printf("%.1f", usage)}')
fi

LAST_BOOT=$(who -b | awk '{print($3 " " $4)}')
TCP=$(awk '/TCP:/ {print $3}' /proc/net/sockstat)
USER_LOG=$(who | awk '{print $1}' | sort -u | wc -l)

Active_CONNECTIONS=$(lsof -n -iTCP -sTCP:ESTABLISHED | grep -E 'sshd|Xvnc')
ACTIVE_VNC=$(echo "$Active_CONNECTIONS" | grep '^Xvnc' | wc -l)
ACTIVE_SSH=$(echo "$Active_CONNECTIONS" | grep '^sshd' | wc -l)

# Network throughput: find the primary non-loopback interface and read RX/TX bytes
NET_IFACE=$(ip route get 8.8.8.8 2>/dev/null | awk '/dev/ {for(i=1;i<=NF;i++) if($i=="dev") print $(i+1)}' | head -1)
if [ -z "$NET_IFACE" ]; then
	NET_IFACE=$(ip link show | awk '/^[0-9]+:/ && !/lo:/ {gsub(":","",$2); print $2; exit}')
fi
NET_RX_BYTES=0
NET_TX_BYTES=0
if [ -n "$NET_IFACE" ] && [ -f "/sys/class/net/${NET_IFACE}/statistics/rx_bytes" ]; then
	NET_RX_BYTES=$(cat "/sys/class/net/${NET_IFACE}/statistics/rx_bytes" 2>/dev/null || echo 0)
	NET_TX_BYTES=$(cat "/sys/class/net/${NET_IFACE}/statistics/tx_bytes" 2>/dev/null || echo 0)
fi

line_format=false
while [ $# -ne 0 ]; do
	if [ "$1" = "--line-format" ]; then
		line_format=true
	fi
	shift
done

if $line_format; then
	printf "${ARCH},${OS},${PCPU},${VCPU},${RAM_USED}/${RAM_TOTAL},${RAM_PERC},\
${DISK_USED}/${DISK_TOTAL},${DISK_PERC},${CPU_LOAD},${LAST_BOOT},\
${TCP},${USER_LOG},${ACTIVE_VNC},${ACTIVE_SSH},\
${CPU_USAGE},${SWAP_USED_MB},${SWAP_TOTAL_MB},${SWAP_PERC},\
${NET_RX_BYTES},${NET_TX_BYTES}\n"
else
	printf "%-25s: %s\n" "Architecture" "${ARCH}"
	printf "%-25s: %s\n" "OS" "${OS}"
	printf "%-25s: %d\n" "Physical CPUs" "${PCPU}"
	printf "%-25s: %d\n" "Virtual CPUs" "${VCPU}"
	printf "%-25s: %s/%s (%.0f%%)\n" "RAM" "${RAM_USED}" "${RAM_TOTAL}" "${RAM_PERC}"
	printf "%-25s: %s/%s (%s)\n" "Disk" "${DISK_USED}" "${DISK_TOTAL}" "${DISK_PERC}"
	printf "%-25s: %s\n" "CPU Load (1, 5, 15 min)" "${CPU_LOAD}"
	printf "%-25s: %s%%\n" "CPU Utilization" "${CPU_USAGE}"
	printf "%-25s: %dMB/%dMB (%s%%)\n" "Swap" "${SWAP_USED_MB}" "${SWAP_TOTAL_MB}" "${SWAP_PERC}"
	printf "%-25s: %s\n" "Last Boot" "${LAST_BOOT}"
	printf "%-25s: %d\n" "TCP Connections" "${TCP}"
	printf "%-25s: %d\n" "User Logins" "${USER_LOG}"
	printf "%-25s: %d\n" "Active VNC Sessions" "${ACTIVE_VNC}"
	printf "%-25s: %d\n" "Active SSH Sessions" "${ACTIVE_SSH}"
	printf "%-25s: %s (RX: %d bytes, TX: %d bytes)\n" "Network" "${NET_IFACE}" "${NET_RX_BYTES}" "${NET_TX_BYTES}"
fi


