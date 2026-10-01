#!/usr/bin/env bash
# Per-account resource usage, aggregated by numeric UID.
#
# CPU and I/O are measured over a sampling window (not lifetime averages):
# per-process deltas keyed by (pid, start time), summed by UID. CPU is in
# percent of ONE logical CPU, so 400 means four cores busy. I/O counters are
# readable only for the caller's own processes unless run as root; when none of
# an account's processes is readable its I/O fields are empty (unknown), not 0.
#
# Accounts reported: login-shell accounts, every UID owning a process, and
# logged-in users.
#
# Options:
#   --no-headers        machine output: "#format=2 ..." line, then one TSV row per account
#   --collect-disk      scan home + /eda_work directories (slow; low priority, time limited)
#   --sample-seconds N  sampling window (default 2)
#   --disk-timeout N    per-account disk scan limit in seconds (default 900)
#
# Columns: uid username cpu mem_pct rss_kb disk_gib procs top_process last_login
#          full_name io_read_bytes io_write_bytes io_read_bps io_write_bps
# disk_gib: number = measured allocated size, empty = not collected/timed out,
#           "none" = account has no home or /eda_work directory to scan.

export LC_ALL=C

headers=true
collect_disk=false
SAMPLE_SECONDS=2
DISK_TIMEOUT=900
while [ $# -ne 0 ]; do
	case "$1" in
		--no-headers) headers=false ;;
		--collect-disk) collect_disk=true ;;
		--sample-seconds) SAMPLE_SECONDS="$2"; shift ;;
		--disk-timeout) DISK_TIMEOUT="$2"; shift ;;
	esac
	shift
done

WORK=$(mktemp -d) || exit 1
trap 'rm -rf "$WORK"' EXIT

# One line per process: pid start_time cpu_ticks (utime+stime).
# The command name may contain spaces or ')', so fields are read after the last ") ".
proc_snapshot() {
	cat /proc/[0-9]*/stat 2>/dev/null | awk '{
		pid = $1; rest = $0; sub(/^.*\) /, "", rest); split(rest, f, " ")
		print pid, f[20], f[12] + f[13]
	}'
}
# One line per readable process: pid read_bytes write_bytes
io_snapshot() {
	grep -s -H -E '^(read|write)_bytes:' /proc/[0-9]*/io | awk -F'[/:]+' '
		{ pid = $3; v = $6 + 0; if ($5 == "read_bytes") r[pid] = v; else w[pid] = v }
		END { for (p in r) print p, r[p], w[p] }'
}

HZ=$(getconf CLK_TCK)
T1=$(date +%s.%N)
proc_snapshot > "$WORK/stat1"
io_snapshot > "$WORK/io1"
sleep "$SAMPLE_SECONDS"
T2=$(date +%s.%N)
proc_snapshot > "$WORK/stat2"
io_snapshot > "$WORK/io2"
# Separate -o options: old procps (RHEL 6) treats "pid=,uid=" as one header label
ps -e -o pid= -o uid= -o rss= -o pmem= -o comm= > "$WORK/ps"

# Aggregate by UID: uid cpu mem_pct rss_kb procs top_process io_r io_w io_r_bps io_w_bps
# Fields are separated by \x1f: with tab, bash `read` would merge empty fields.
awk -v hz="$HZ" -v elapsed="$(awk -v a="$T1" -v b="$T2" 'BEGIN {print b - a}')" '
	FILENAME ~ /stat1$/ { start1[$1] = $2; ticks1[$1] = $3; next }
	FILENAME ~ /stat2$/ { start2[$1] = $2; ticks2[$1] = $3; next }
	FILENAME ~ /io1$/   { r1[$1] = $2; w1[$1] = $3; next }
	FILENAME ~ /io2$/   { r2[$1] = $2; w2[$1] = $3; next }
	{
		pid = $1; uid = $2
		if (!(pid in start2)) next          # exited before the second sample
		comm = $0; sub(/^ *[0-9]+ +[0-9]+ +[0-9]+ +[0-9.]+ /, "", comm)
		# Same pid but a different start time is a new process: count all of its ticks
		same = (pid in start1) && start1[pid] == start2[pid]
		d = same ? ticks2[pid] - ticks1[pid] : ticks2[pid]
		seen[uid] = 1
		procs[uid]++; rss[uid] += $3; mem[uid] += $4; ticks[uid] += d
		if (!(uid in top_d) || d > top_d[uid] || (d == top_d[uid] && $3 > top_rss[uid])) {
			top_d[uid] = d; top_rss[uid] = $3; top[uid] = comm
		}
		if (pid in r2) {
			io_ok[uid] = 1
			ior[uid] += r2[pid]; iow[uid] += w2[pid]
			dr[uid] += (same && pid in r1) ? r2[pid] - r1[pid] : 0
			dw[uid] += (same && pid in w1) ? w2[pid] - w1[pid] : 0
		}
	}
	END {
		for (u in seen) {
			cpu = elapsed > 0 ? ticks[u] / hz / elapsed * 100 : 0
			if (u in io_ok)
				io = sprintf("%d\037%d\037%d\037%d", ior[u], iow[u], dr[u] / elapsed, dw[u] / elapsed)
			else
				io = "\037\037\037"
			gsub(/[\t\037]/, " ", top[u])
			printf "%s\037%.2f\037%.2f\037%d\037%d\037%s\037%s\n", u, cpu, mem[u], rss[u], procs[u], top[u], io
		}
	}' "$WORK/stat1" "$WORK/stat2" "$WORK/io1" "$WORK/io2" "$WORK/ps" > "$WORK/usage"

# Candidate UIDs: process owners, login-shell accounts, logged-in users
{
	cut -d $'\037' -f1 "$WORK/usage"
	getent passwd | awk -F: '$7 ~ /\/bin\/.*sh$/ {print $3}'
	who | awk '{print $1}' | sort -u | while read -r name; do id -u "$name" 2>/dev/null; done
} | grep -E '^[0-9]+$' | sort -un > "$WORK/uids"

# Allocated size in GiB of an account's home and /eda_work directories
get_disk_usage() {
	local uid="$1" user="$2" home="$3" path
	local -a paths=()
	if [ -n "$home" ] && [ "$home" != "/" ] && [ -d "$home" ] && [ "$(stat -c %u "$home")" = "$uid" ]; then
		paths+=("$home")
	fi
	if [ -d /eda_work ]; then
		while IFS= read -r -d '' path; do
			paths+=("$path")
		done < <(find /eda_work/ -mindepth 1 -maxdepth 1 -uid "$uid" -print0 2>/dev/null)
		if [ -d "/eda_work/$user" ] && [[ ! " ${paths[*]} " == *" /eda_work/$user "* ]]; then
			paths+=("/eda_work/$user")
		fi
	fi
	if [ ${#paths[@]} -eq 0 ]; then
		echo none
		return
	fi
	# An unreadable top-level directory would be counted as ~0: report unknown instead
	for path in "${paths[@]}"; do
		if [ ! -r "$path" ] || [ ! -x "$path" ]; then
			echo ""
			return
		fi
	done
	local -a lowprio=(nice -n 19)
	command -v ionice >/dev/null 2>&1 && lowprio+=(ionice -c 3)
	local total
	# Exit 124 = timed out; the partial total is discarded (reported as not collected)
	total=$(timeout "$DISK_TIMEOUT" "${lowprio[@]}" du -sck -- "${paths[@]}" 2>/dev/null </dev/null)
	if [ $? -eq 124 ] || [ -z "$total" ]; then
		echo ""
		return
	fi
	echo "$total" | tail -1 | awk '{printf "%.2f", $1 / 1048576}'
}

# Most recent login as "YYYY-MM-DD HH:MM:SS", empty if never/unknown
get_last_login() {
	local stamp
	stamp=$(last -F -w -n 1 "$1" 2>/dev/null </dev/null | head -n 1 |
		grep -oE '[A-Z][a-z]{2} [A-Z][a-z]{2} +[0-9]+ [0-9]{2}:[0-9]{2}:[0-9]{2} [0-9]{4}' | head -n 1)
	[ -n "$stamp" ] && date -d "$stamp" '+%Y-%m-%d %H:%M:%S' 2>/dev/null
}

if $headers; then
	printf "UID\tUSERNAME\tCPU%%(1 CPU=100)\tMEM%%\tRSS_KB\tDISK_GIB\tPROCS\tTOP_PROCESS\tLAST_LOGIN\tFULL_NAME\tIO_READ_B\tIO_WRITE_B\tIO_READ_B/S\tIO_WRITE_B/S\n"
else
	printf "#format=2 sample_seconds=%s cpu_unit=percent_of_one_cpu\n" \
		"$(awk -v a="$T1" -v b="$T2" 'BEGIN {printf "%.3f", b - a}')"
fi

while read -r uid; do
	user="" gecos="" home=""
	IFS=: read -r user _ _ _ gecos home _ < <(getent passwd "$uid")
	user=${user:-$uid}
	usage=$(awk -F'\037' -v u="$uid" '$1 == u {print; exit}' "$WORK/usage")
	if [ -n "$usage" ]; then
		IFS=$'\037' read -r _ cpu mem rss procs top_process io_r io_w io_rbps io_wbps <<< "$usage"
	else
		cpu=0.00 mem=0.00 rss=0 procs=0 top_process="" io_r="" io_w="" io_rbps="" io_wbps=""
	fi
	disk=""
	$collect_disk && disk=$(get_disk_usage "$uid" "$user" "$home")
	full_name=${gecos%%,*}
	printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" \
		"$uid" "$user" "$cpu" "$mem" "$rss" "$disk" "$procs" "$top_process" \
		"$(get_last_login "$user")" "${full_name//$'\t'/ }" "$io_r" "$io_w" "$io_rbps" "$io_wbps"
done < "$WORK/uids" | sort -t$'\t' -k3,3gr -k4,4gr
