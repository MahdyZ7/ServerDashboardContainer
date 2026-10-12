#!/usr/bin/env bash
# Host metrics for one server.
#   --kv               machine output: one key=value per line (format_version=2);
#                      an empty value means "not measured", never zero
#   --sample-seconds N CPU sampling window (default 1)
#   --services "a b"   services to report (default "sshd crond"); state is active,
#                      inactive, failed or missing (not installed). Other failed
#                      systemd units are reported too, flagged as not monitored.
#   --mounts "a b"     filesystems that must be mounted, matched by name against the
#                      mount point or source (default "KSRC_lab_share"); state is
#                      mounted, unresponsive (stat timed out) or missing
# Diagnostics go to stderr; stdout carries only the report.

export LC_ALL=C

kv=false
SAMPLE_SECONDS=1
SERVICES="sshd crond"
MOUNTS="KSRC_lab_share"
while [ $# -ne 0 ]; do
	case "$1" in
		--kv) kv=true ;;
		--sample-seconds) SAMPLE_SECONDS="$2"; shift ;;
		--services) SERVICES="$2"; shift ;;
		--mounts) MOUNTS="$2"; shift ;;
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
# Zombies: exited children their parent has not reaped
PROCS_ZOMBIE=$(ps -e -o stat= 2>/dev/null | grep -c '^Z')

# Service health. systemd hosts use systemctl; RHEL 6 uses init scripts
# (service status: 0 running, 1-2 dead with pid/lock file, 3 stopped).
service_state() {
	local name="$1" out load active
	if [ -d /run/systemd/system ]; then
		out=$(systemctl show -p LoadState -p ActiveState "$name.service" 2>/dev/null)
		load=$(echo "$out" | sed -n 's/^LoadState=//p')
		active=$(echo "$out" | sed -n 's/^ActiveState=//p')
		if [ "$load" = "not-found" ] || [ -z "$load" ]; then echo missing
		elif [ "$active" = "active" ] || [ "$active" = "reloading" ] || [ "$active" = "activating" ]; then echo active
		elif [ "$active" = "failed" ]; then echo failed
		else echo inactive
		fi
	elif [ -x "/etc/init.d/$name" ]; then
		"/etc/init.d/$name" status >/dev/null 2>&1 </dev/null
		case $? in
			0) echo active ;;
			1|2) echo failed ;;
			*) echo inactive ;;
		esac
	else
		echo missing
	fi
}
SERVICE_LINES=$(for name in $SERVICES; do printf 'svc=%s\t%s\t1\n' "$name" "$(service_state "$name")"; done
	# Any other failed systemd unit is worth knowing about too
	if [ -d /run/systemd/system ]; then
		systemctl list-units --state=failed --no-legend --plain 2>/dev/null </dev/null | awk '{print $1}' |
			sed 's/\.service$//' | while read -r unit; do
				case " $SERVICES " in *" $unit "*) ;; *) printf 'svc=%s\tfailed\t0\n' "$unit" ;; esac
			done
	fi)

# Login sessions, one line each: kind user session from started_epoch idle_seconds viewers
BTIME=$(awk '/^btime/ {print $2}' /proc/stat)
HZ=$(getconf CLK_TCK)
NOW=$(date +%s)
proc_start() {
	awk -v b="$BTIME" -v hz="$HZ" '{rest = $0; sub(/^.*\) /, "", rest); split(rest, f, " "); printf "%d", b + f[20] / hz}' \
		"/proc/$1/stat" 2>/dev/null
}
# The sshd process serving this collector, so its own connection is not reported
SELF_SSHD=""
p=$$
while [ -n "$p" ] && [ "$p" -gt 1 ]; do
	case "$(tr '\0' ' ' < "/proc/$p/cmdline" 2>/dev/null)" in sshd*) SELF_SSHD=$p; break ;; esac
	p=$(awk '/^PPid:/ {print $2}' "/proc/$p/status" 2>/dev/null)
done
# SSH with a terminal: utmp entries from a remote host (":0"/":1" are X displays,
# tmux registers its panes too). Idle = time since the terminal last saw input.
# `who -u` ends with "idle pid (host)"; the date in between has 2 or 3 words.
SSH_TTY_LINES=$(who -u 2>/dev/null | while read -r -a f; do
	n=${#f[@]}
	[ "$n" -ge 4 ] || continue
	last=${f[n-1]}
	[[ $last == \(*\) ]] || continue
	host=${last:1:${#last}-2} pid=${f[n-2]} tty=${f[1]}
	[[ -z $host || $host == :* || $host == tmux* ]] && continue
	atime=$(stat -c %X "/dev/$tty" 2>/dev/null)
	idle=""
	[ -n "$atime" ] && idle=$((NOW > atime ? NOW - atime : 0))
	printf 'sess=ssh\t%s\t%s\t%s\t%s\t%s\t\n' "${f[0]}" "$tty" "$host" "$(proc_start "$pid")" "$idle"
done)
# SSH without a terminal (VS Code, sftp, scp, port forwards): "sshd: user@notty"
SSH_NOTTY_LINES=$(ps -e -o pid= -o args= 2>/dev/null | awk -v self="$SELF_SSHD" '
	$1 != self && $2 ~ /^sshd(-session)?:$/ && $3 ~ /@notty$/ { sub(/@notty$/, "", $3); print $1, $3 }' |
	while read -r pid user; do
		printf 'sess=ssh\t%s\tnotty\t\t%s\t\t\n' "$user" "$(proc_start "$pid")"
	done)
# Established TCP connections as "local_port remote_addr" (IPv4 and v4-mapped IPv6)
ESTABLISHED=$(awk '
	function hex(s,   i, n) { n = 0; s = toupper(s); for (i = 1; i <= length(s); i++) n = n * 16 + index("0123456789ABCDEF", substr(s, i, 1)) - 1; return n }
	function ip4(h) { return hex(substr(h, 7, 2)) "." hex(substr(h, 5, 2)) "." hex(substr(h, 3, 2)) "." hex(substr(h, 1, 2)) }
	FNR > 1 && $4 == "01" {
		split($2, l, ":"); split($3, r, ":"); a = r[1]
		if (length(a) == 8) addr = ip4(a)
		else if (substr(a, 1, 24) == "0000000000000000FFFF0000") addr = ip4(substr(a, 25))
		else if (a == "00000000000000000000000001000000") addr = "::1"
		else addr = "ipv6"
		print hex(l[2]), addr
	}' /proc/net/tcp /proc/net/tcp6 2>/dev/null)
# VNC: one Xvnc per desktop. Its port is -rfbport, else 5900 + display number;
# viewers = clients connected to that port now (127.0.0.1 = through an SSH tunnel).
VNC_LINES=$(ps -C Xvnc,Xtigervnc,Xvnc-core -o pid= -o uid= -o args= 2>/dev/null | while read -r pid uid args; do
	user=$(getent passwd "$uid" | cut -d: -f1)
	read -r display port < <(awk '{
		d = ""; p = ""
		for (i = 1; i <= NF; i++) {
			if (d == "" && $i ~ /^:[0-9]+$/) d = $i
			if ($i == "-rfbport" && i < NF) p = $(i + 1)
			else if ($i ~ /^-?rfbport=/) { p = $i; sub(/^-?rfbport=/, "", p) }
		}
		if (p == "" && d != "") p = 5900 + substr(d, 2)
		print (d == "" ? "-" : d), (p ~ /^[0-9]+$/ && p > 0 ? p : "-")
	}' <<< "$args")
	viewers="" from=""
	if [ "$port" != "-" ]; then
		viewers=$(printf '%s\n' "$ESTABLISHED" | awk -v p="$port" '$1 == p' | grep -c .)
		from=$(printf '%s\n' "$ESTABLISHED" | awk -v p="$port" '$1 == p {print $2}' | sort -u | paste -sd, -)
	fi
	[ "$display" = "-" ] && display=""
	printf 'sess=vnc\t%s\t%s\t%s\t%s\t\t%s\n' "${user:-$uid}" "$display" "$from" "$(proc_start "$pid")" "$viewers"
done)
SESSION_LINES=$(printf '%s\n' "$VNC_LINES" "$SSH_TTY_LINES" "$SSH_NOTTY_LINES" | grep .)

# Required mounts, read from /proc/mounts (never hangs). A name matches a mount
# point or export path exactly or as its last component ("lab" matches /x/lab and
# nfs:/x/lab). An automount point is touched once to mount it; a mount that does
# not answer statfs within 10 s is unresponsive (SIGKILL: coreutils 8.4 on RHEL 6
# has no timeout -k).
find_mount() {
	awk -v n="$1" -v want="$2" '
		function ends(s, t) { return length(s) >= length(t) && substr(s, length(s) - length(t) + 1) == t }
		($3 == "autofs") == want && ($2 == n || ends($2, "/" n) || ends($1, ":" n) || ends($1, "/" n)) {
			print $2 "\t" $1 "\t" $3; exit
		}' /proc/mounts
}
MOUNT_LINES=$(for name in $MOUNTS; do
	found=$(find_mount "$name" 0)
	if [ -z "$found" ]; then
		auto=$(find_mount "$name" 1 | cut -f1)
		if [ -n "$auto" ]; then
			timeout -s KILL 10 stat -f -- "$auto/." >/dev/null 2>&1
			found=$(find_mount "$name" 0)
		fi
	fi
	if [ -z "$found" ]; then
		printf 'mnt=%s\tmissing\t\t\t\n' "$name"
		continue
	fi
	IFS=$'\t' read -r mp src fstype <<< "$found"
	state=unresponsive
	timeout -s KILL 10 stat -f -- "$mp" >/dev/null 2>&1 && state=mounted
	printf 'mnt=%s\t%s\t%s\t%s\t%s\n' "$name" "$state" "$mp" "$src" "$fstype"
done)

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
		echo "procs_zombie=$PROCS_ZOMBIE"
		echo "psi_cpu_some_avg60=$PSI_CPU_SOME"
		echo "psi_memory_some_avg60=$PSI_MEM_SOME"
		echo "psi_memory_full_avg60=$PSI_MEM_FULL"
		echo "psi_io_some_avg60=$PSI_IO_SOME"
		echo "psi_io_full_avg60=$PSI_IO_FULL"
		[ -n "$FILESYSTEMS" ] && echo "$FILESYSTEMS"
		[ -n "$BLOCK_DEVICES" ] && echo "$BLOCK_DEVICES"
		[ -n "$NETWORK" ] && echo "$NETWORK"
		[ -n "$SERVICE_LINES" ] && echo "$SERVICE_LINES"
		[ -n "$SESSION_LINES" ] && echo "$SESSION_LINES"
		[ -n "$MOUNT_LINES" ] && echo "$MOUNT_LINES"
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
	printf "%-25s: %s running, %s blocked, %s zombie\n" "Tasks" "${PROCS_RUNNING}" "${PROCS_BLOCKED}" "${PROCS_ZOMBIE}"
	printf "%s\n" "${MOUNT_LINES}" | awk -F'\t' 'NF {sub("mnt=", "", $1); printf "%-25s: %s %s\n", "Mount " $1, $2, $3}'
	printf "%s\n" "${SESSION_LINES}" | awk -F'\t' 'NF {sub("sess=", "", $1); printf "%-25s: %s %s %s viewers=%s idle=%ss\n", "Session " $1, $2, $3, $4, $7, $6}'
	printf "%s\n" "${SERVICE_LINES}" | awk -F'\t' 'NF {sub("svc=", "", $1); printf "%-25s: %s\n", "Service " $1, $2}'
	printf "%-25s: cpu %s, memory %s/%s, io %s/%s (some/full, %% of 60 s)\n" "Pressure" \
		"${PSI_CPU_SOME:-n/a}" "${PSI_MEM_SOME:-n/a}" "${PSI_MEM_FULL:-n/a}" "${PSI_IO_SOME:-n/a}" "${PSI_IO_FULL:-n/a}"
	printf "%s\n" "${FILESYSTEMS}" | awk -F'\t' 'NF {sub("fs=", "", $1); printf "%-25s: %s %s, %.0f%% used\n", "Filesystem " $1, $2, $3, ($4 > 0 ? $5 / $4 * 100 : 0)}'
	printf "%-25s: %s (RX: %s bytes, TX: %s bytes)\n" "Network" "${NET_IFACE}" "${NET_RX_BYTES}" "${NET_TX_BYTES}"
fi
