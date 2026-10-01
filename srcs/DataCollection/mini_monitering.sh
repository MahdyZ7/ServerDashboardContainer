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

# Distinct people, not sockets: VNC = owners of Xvnc servers (visible without
# root); SSH = users with a login session from a remote host in utmp.
ACTIVE_VNC=$(ps -C Xvnc -o user= 2>/dev/null | sort -u | grep -c .)
ACTIVE_SSH=$(who | awk '$NF ~ /^\(/ && $NF !~ /^\(:/ {print $1}' | sort -u | grep -c .)
read -r PROCS_RUNNING PROCS_BLOCKED < <(awk '/^procs_running/ {r=$2} /^procs_blocked/ {b=$2} END {print r, b}' /proc/stat)

# Pressure stall information: share of the last 60 s that tasks waited on a
# resource. Empty when the kernel lacks PSI (before 4.20, or booted without psi=1).
psi() { awk -v kind="$2" '$1 == kind {sub("avg60=", "", $3); print $3}' "/proc/pressure/$1" 2>/dev/null; }
PSI_CPU_SOME=$(psi cpu some)
PSI_MEM_SOME=$(psi memory some)
PSI_MEM_FULL=$(psi memory full)
PSI_IO_SOME=$(psi io some)
PSI_IO_FULL=$(psi io full)

# Per-mount capacity and inodes (local and network; network mounts may hang, so
# fall back to local-only on timeout). Line: mount fstype source size used avail inodes inodes_used
SKIP_FS='^(tmpfs|devtmpfs|squashfs|overlay|efivarfs|iso9660|udf|proc|sysfs|autofs)$'
df_all() {
	local out
	out=$(timeout 15 df -P "$@" 2>/dev/null)
	[ $? -eq 124 ] && out=$(timeout 15 df -P -l "$@" 2>/dev/null)
	printf '%s\n' "$out"
}
# The mount point is everything after the 6th (-T) or 5th (-i) column and may contain spaces
FILESYSTEMS=$(awk -v skip="$SKIP_FS" '
	FNR == 1 { next }
	FILENAME == "-" || NR == FNR {
		m = $0; for (i = 1; i <= 6; i++) sub(/^[^ ]+ +/, "", m)
		if ($2 ~ skip || $1 ~ /^\/dev\/loop/) next
		order[++n] = m; src[m] = $1; type[m] = $2; size[m] = $3; used[m] = $4; avail[m] = $5
		next
	}
	{ m = $0; for (i = 1; i <= 5; i++) sub(/^[^ ]+ +/, "", m); itot[m] = $2; iused[m] = $3 }
	END {
		for (k = 1; k <= n; k++) {
			m = order[k]
			printf "fs=%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n", m, type[m], src[m], size[m], used[m], avail[m], itot[m], iused[m]
		}
	}' <(df_all -T -B1) <(df_all -i))

# Per-device I/O counters for whole block devices. Line: device name reads
# sectors_read ms_reading writes sectors_written ms_writing ms_doing_io (sectors are 512 B)
BLOCK_DEVICES=$(awk '
	$3 ~ /^(loop|ram|sr|fd|zram)/ { next }
	{
		dev = $3; sysdir = "/sys/block/" dev
		if (system("test -d " sysdir) != 0) next    # partitions are not under /sys/block
		name = dev
		if ((getline line < (sysdir "/dm/name")) > 0) name = line
		close(sysdir "/dm/name")
		printf "blk=%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n", dev, name, $4, $6, $7, $8, $10, $11, $13
	}' /proc/diskstats)

# Per-interface counters for physical NICs and bonds (no lo, veth, bridges, docker)
NETWORK=$(for dir in /sys/class/net/*; do
	iface=${dir##*/}
	[ -e "$dir/device" ] || [[ $iface == bond* || $iface == team* ]] || continue
	st="$dir/statistics"
	printf 'net=%s' "$iface"
	for c in rx_bytes tx_bytes rx_packets tx_packets rx_errors tx_errors rx_dropped tx_dropped; do
		printf '\t%s' "$(cat "$st/$c" 2>/dev/null)"
	done
	printf '\n'
done)

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
		echo "procs_running=$PROCS_RUNNING"
		echo "procs_blocked=$PROCS_BLOCKED"
		echo "psi_cpu_some_avg60=$PSI_CPU_SOME"
		echo "psi_memory_some_avg60=$PSI_MEM_SOME"
		echo "psi_memory_full_avg60=$PSI_MEM_FULL"
		echo "psi_io_some_avg60=$PSI_IO_SOME"
		echo "psi_io_full_avg60=$PSI_IO_FULL"
		[ -n "$FILESYSTEMS" ] && echo "$FILESYSTEMS"
		[ -n "$BLOCK_DEVICES" ] && echo "$BLOCK_DEVICES"
		[ -n "$NETWORK" ] && echo "$NETWORK"
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
	printf "%-25s: %s\n" "VNC Users" "${ACTIVE_VNC}"
	printf "%-25s: %s\n" "SSH Users" "${ACTIVE_SSH}"
	printf "%-25s: %s running, %s blocked\n" "Tasks" "${PROCS_RUNNING}" "${PROCS_BLOCKED}"
	printf "%-25s: cpu %s, memory %s/%s, io %s/%s (some/full, %% of 60 s)\n" "Pressure" \
		"${PSI_CPU_SOME:-n/a}" "${PSI_MEM_SOME:-n/a}" "${PSI_MEM_FULL:-n/a}" "${PSI_IO_SOME:-n/a}" "${PSI_IO_FULL:-n/a}"
	printf "%s\n" "${FILESYSTEMS}" | awk -F'\t' 'NF {sub("fs=", "", $1); printf "%-25s: %s %s, %.0f%% used\n", "Filesystem " $1, $2, $3, ($4 > 0 ? $5 / $4 * 100 : 0)}'
	printf "%-25s: %s (RX: %s bytes, TX: %s bytes)\n" "Network" "${NET_IFACE}" "${NET_RX_BYTES}" "${NET_TX_BYTES}"
fi
