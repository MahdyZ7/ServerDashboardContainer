#!/usr/bin/env bash
# Host metrics for one server.
#   --kv               machine output: one key=value per line (format_version=2);
#                      an empty value means "not measured", never zero
#   --sample-seconds N CPU sampling window (default 1)
# Diagnostics go to stderr; stdout carries only the report.

export LC_ALL=C

kv=false
SAMPLE_SECONDS=1
while [ $# -ne 0 ]; do
	case "$1" in
		--kv) kv=true ;;
		--sample-seconds) SAMPLE_SECONDS="$2"; shift ;;
	esac
	shift
done

# Strip characters that would break a key=value line
clean() { printf '%s' "$1" | tr -d '\r\n'; }

ARCH=$(uname -srvmo 2>/dev/null)
OS=""
if [ -r /etc/os-release ]; then
	OS=$(. /etc/os-release && echo "${NAME:-} ${VERSION_ID:-}")
elif [ -r /etc/redhat-release ]; then
	OS=$(sed 's/ release / /; s/ (.*//' /etc/redhat-release)
elif command -v lsb_release >/dev/null 2>&1; then
	OS="$(lsb_release -si 2>/dev/null) $(lsb_release -sr 2>/dev/null)"
fi

PCPU=$(grep 'physical id' /proc/cpuinfo | sort -u | wc -l)
VCPU=$(getconf _NPROCESSORS_ONLN 2>/dev/null || grep -c '^processor' /proc/cpuinfo)

# Memory from /proc/meminfo; "used" means not available to new work (MemTotal - MemAvailable)
read -r MEM_TOTAL_KB MEM_AVAIL_KB SWAP_TOTAL_KB SWAP_FREE_KB < <(awk '
	/^MemTotal:/ {t=$2} /^MemAvailable:/ {a=$2} /^MemFree:/ {f=$2}
	/^Buffers:/ {b=$2} /^Cached:/ {c=$2} /^SwapTotal:/ {st=$2} /^SwapFree:/ {sf=$2}
	END { if (a == "") a = f + b + c; print t, a, st, sf }' /proc/meminfo)
RAM_TOTAL=$(awk -v t="$MEM_TOTAL_KB" 'BEGIN {printf "%.2fG", t/1048576}')
RAM_USED=$(awk -v t="$MEM_TOTAL_KB" -v a="$MEM_AVAIL_KB" 'BEGIN {printf "%.2fG", (t-a)/1048576}')
RAM_PERC=$(awk -v t="$MEM_TOTAL_KB" -v a="$MEM_AVAIL_KB" 'BEGIN {if (t > 0) printf "%.0f", (t-a)/t*100}')
RAM_AVAIL_MB=$((MEM_AVAIL_KB / 1024))
SWAP_TOTAL_MB=$((SWAP_TOTAL_KB / 1024))
SWAP_USED_MB=$(((SWAP_TOTAL_KB - SWAP_FREE_KB) / 1024))
SWAP_PERC=$(awk -v t="$SWAP_TOTAL_KB" -v f="$SWAP_FREE_KB" 'BEGIN {if (t > 0) printf "%.0f", (t-f)/t*100; else print 0}')

# Local disk capacity, excluding memory-backed and image filesystems.
# Totals hide individual full mounts; per-mount data is a planned addition.
DISK_DATA=$(timeout 20 df -h -l --total -x tmpfs -x devtmpfs -x squashfs -x overlay 2>/dev/null | awk '$1 == "total"')
DISK_TOTAL=$(echo "$DISK_DATA" | awk '{print $2}')
DISK_USED=$(echo "$DISK_DATA" | awk '{print $3}')
DISK_PERC=$(echo "$DISK_DATA" | awk '{gsub("%", "", $5); print $5}')

read -r LOAD_1 LOAD_5 LOAD_15 _ < /proc/loadavg

# CPU utilisation over a real sampling window. /proc/stat "cpu" columns:
# user nice system idle iowait irq softirq steal guest guest_nice.
# guest/guest_nice are already included in user/nice, so they are not added again.
cpu_sample() { awk '/^cpu / {print $2+$3+$4+$5+$6+$7+$8+$9, $5, $6, $9; exit}' /proc/stat; }
read -r TOTAL1 IDLE1 IOWAIT1 STEAL1 < <(cpu_sample)
sleep "$SAMPLE_SECONDS"
read -r TOTAL2 IDLE2 IOWAIT2 STEAL2 < <(cpu_sample)
read -r CPU_USAGE CPU_IOWAIT CPU_STEAL < <(awk \
	-v t1="$TOTAL1" -v t2="$TOTAL2" -v i1="$IDLE1" -v i2="$IDLE2" \
	-v w1="$IOWAIT1" -v w2="$IOWAIT2" -v s1="$STEAL1" -v s2="$STEAL2" 'BEGIN {
	dt = t2 - t1
	if (dt <= 0) { print "", "", ""; exit }   # no valid sample: unknown, not 0%
	# Busy excludes idle, iowait and steal; those are reported separately
	printf "%.1f %.1f %.1f\n", (dt-(i2-i1)-(w2-w1)-(s2-s1))/dt*100, (w2-w1)/dt*100, (s2-s1)/dt*100
}')

LAST_BOOT=$(uptime -s 2>/dev/null || who -b | awk '{print $3 " " $4}')
TCP=$(awk '/^TCP:/ {print $3}' /proc/net/sockstat)
USER_LOG=$(who | awk '{print $1}' | sort -u | wc -l)

# Established sshd/Xvnc sockets. Without root, lsof sees only the caller's own sockets.
ACTIVE_CONNECTIONS=$(timeout 20 lsof -n -iTCP -sTCP:ESTABLISHED 2>/dev/null | grep -E '^(sshd|Xvnc)')
ACTIVE_VNC=$(echo "$ACTIVE_CONNECTIONS" | grep -c '^Xvnc')
ACTIVE_SSH=$(echo "$ACTIVE_CONNECTIONS" | grep -c '^sshd')

# Cumulative RX/TX counters of the default-route interface
NET_IFACE=$(ip route get 8.8.8.8 2>/dev/null | awk '{for (i = 1; i <= NF; i++) if ($i == "dev") {print $(i+1); exit}}')
if [ -z "$NET_IFACE" ]; then
	NET_IFACE=$(ip -o link show 2>/dev/null | awk -F': ' '$2 != "lo" {print $2; exit}')
fi
NET_RX_BYTES=""
NET_TX_BYTES=""
if [ -n "$NET_IFACE" ] && [ -r "/sys/class/net/${NET_IFACE}/statistics/rx_bytes" ]; then
	NET_RX_BYTES=$(cat "/sys/class/net/${NET_IFACE}/statistics/rx_bytes")
	NET_TX_BYTES=$(cat "/sys/class/net/${NET_IFACE}/statistics/tx_bytes")
fi

if $kv; then
	{
		echo "format_version=2"
		echo "architecture=$(clean "$ARCH")"
		echo "operating_system=$(clean "$OS")"
		echo "physical_cpus=$PCPU"
		echo "virtual_cpus=$VCPU"
		echo "ram_used=$RAM_USED"
		echo "ram_total=$RAM_TOTAL"
		echo "ram_percentage=$RAM_PERC"
		echo "ram_available_mb=$RAM_AVAIL_MB"
		echo "swap_used_mb=$SWAP_USED_MB"
		echo "swap_total_mb=$SWAP_TOTAL_MB"
		echo "swap_percentage=$SWAP_PERC"
		echo "disk_used=$DISK_USED"
		echo "disk_total=$DISK_TOTAL"
		echo "disk_percentage=$DISK_PERC"
		echo "cpu_load_1min=$LOAD_1"
		echo "cpu_load_5min=$LOAD_5"
		echo "cpu_load_15min=$LOAD_15"
		echo "cpu_usage_percent=$CPU_USAGE"
		echo "cpu_iowait_percent=$CPU_IOWAIT"
		echo "cpu_steal_percent=$CPU_STEAL"
		echo "last_boot=$(clean "$LAST_BOOT")"
		echo "tcp_connections=$TCP"
		echo "logged_users=$USER_LOG"
		echo "active_vnc_users=$ACTIVE_VNC"
		echo "active_ssh_users=$ACTIVE_SSH"
		echo "net_interface=$NET_IFACE"
		echo "net_rx_bytes=$NET_RX_BYTES"
		echo "net_tx_bytes=$NET_TX_BYTES"
	}
else
	printf "%-25s: %s\n" "Architecture" "${ARCH}"
	printf "%-25s: %s\n" "OS" "${OS}"
	printf "%-25s: %s\n" "Physical CPUs" "${PCPU}"
	printf "%-25s: %s\n" "Virtual CPUs" "${VCPU}"
	printf "%-25s: %s/%s (%s%%), %s MB available\n" "RAM" "${RAM_USED}" "${RAM_TOTAL}" "${RAM_PERC}" "${RAM_AVAIL_MB}"
	printf "%-25s: %s/%s (%s%%)\n" "Disk" "${DISK_USED}" "${DISK_TOTAL}" "${DISK_PERC}"
	printf "%-25s: %s, %s, %s\n" "CPU Load (1, 5, 15 min)" "${LOAD_1}" "${LOAD_5}" "${LOAD_15}"
	printf "%-25s: %s%% busy, %s%% iowait, %s%% steal (%ss sample)\n" "CPU Utilization" "${CPU_USAGE}" "${CPU_IOWAIT}" "${CPU_STEAL}" "${SAMPLE_SECONDS}"
	printf "%-25s: %sMB/%sMB (%s%%)\n" "Swap" "${SWAP_USED_MB}" "${SWAP_TOTAL_MB}" "${SWAP_PERC}"
	printf "%-25s: %s\n" "Last Boot" "${LAST_BOOT}"
	printf "%-25s: %s\n" "TCP Connections" "${TCP}"
	printf "%-25s: %s\n" "User Logins" "${USER_LOG}"
	printf "%-25s: %s\n" "Active VNC Sessions" "${ACTIVE_VNC}"
	printf "%-25s: %s\n" "Active SSH Sessions" "${ACTIVE_SSH}"
	printf "%-25s: %s (RX: %s bytes, TX: %s bytes)\n" "Network" "${NET_IFACE}" "${NET_RX_BYTES}" "${NET_TX_BYTES}"
fi
