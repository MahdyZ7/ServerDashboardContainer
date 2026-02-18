# Data Collection Improvements

## Current Issues & Better Alternatives

### 1. CPU Utilization (Currently Missing)
**Current**: Only CPU load average (queue length)
**Better**: Actual CPU utilization percentage

```bash
# Better approach - actual CPU usage percentage
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)

# Or more detailed per-CPU breakdown
mpstat -P ALL 1 1 | awk '/Average:/ && $2 ~ /[0-9]/ {print $2,$3}'

# Or using /proc/stat for custom calculation
grep 'cpu ' /proc/stat | awk '{usage=($2+$4)*100/($2+$4+$5)} END {print usage}'
```

### 2. Memory Metrics - Add Swap & Cache Info
**Current**: Basic RAM used/total
**Enhancement**: Include swap, cache, available memory

```bash
# Better memory breakdown
free -m | awk '/Mem:/ {printf "RAM: %dM/%dM (%.1f%%) Available: %dM\n", $3, $2, $3/$2*100, $7}'
free -m | awk '/Swap:/ {printf "Swap: %dM/%dM (%.1f%%)\n", $3, $2, ($2>0 ? $3/$2*100 : 0)}'

# Memory pressure indicator
cat /proc/pressure/memory 2>/dev/null | grep "some avg10"
```

### 3. Disk I/O Performance (Missing)
**Current**: Only disk space usage
**Add**: Disk I/O stats, read/write speeds

```bash
# Disk I/O statistics
iostat -dx 1 2 | awk '/^[sv]d/ {print $1,$4,$5,$14}'  # device, read/s, write/s, %util

# Per-filesystem I/O
cat /proc/diskstats | awk '{print $3,$6,$10}'  # device, reads, writes
```

### 4. Network Statistics (Missing Critical Data)
**Current**: Only TCP connection count
**Add**: Network throughput, bandwidth usage, errors

```bash
# Network interface statistics
ip -s link show | awk '/^[0-9]+:/ {iface=$2} /RX:/ {getline; rx=$1} /TX:/ {getline; tx=$1; print iface, rx, tx}'

# Better: Use /sys for current bytes
for iface in /sys/class/net/*/statistics; do
    dev=$(echo $iface | cut -d'/' -f5)
    rx=$(cat $iface/rx_bytes)
    tx=$(cat $iface/tx_bytes)
    echo "$dev RX: $rx TX: $tx"
done

# Network errors and drops
netstat -i | awk 'NR>2 {print $1,$3,$6}'  # interface, RX-ERR, TX-ERR
```

### 5. Process/User Improvements
**Current**: Basic PID, CPU%, MEM%, command
**Enhancement**: Add I/O, threads, open files

```bash
# Better user process info with I/O
for pid in $(pgrep -u $USERNAME); do
    # CPU, MEM, I/O read, I/O write
    io=$(cat /proc/$pid/io 2>/dev/null)
    read_bytes=$(echo "$io" | awk '/^read_bytes:/ {print $2}')
    write_bytes=$(echo "$io" | awk '/^write_bytes:/ {print $2}')

    ps -p $pid -o pid,pcpu,pmem,comm --no-headers
    echo "  I/O: R:$read_bytes W:$write_bytes"
done

# Thread count per user
ps -u $USERNAME -L --no-headers | wc -l

# Open file descriptors per user
lsof -u $USERNAME 2>/dev/null | wc -l
```

### 6. Temperature Monitoring (Not Collected)
**Missing**: Hardware temperature sensors

```bash
# CPU temperature (if sensors available)
sensors 2>/dev/null | awk '/^Core/ {sum+=$3; count++} END {if(count>0) print "CPU Temp:", sum/count"°C"}'

# Alternative: thermal zones
paste <(cat /sys/class/thermal/thermal_zone*/type) \
      <(cat /sys/class/thermal/thermal_zone*/temp) | \
      awk '{printf "%s: %.1f°C\n", $1, $2/1000}'
```

### 7. System Load Context (Enhancement)
**Current**: Load average only
**Add**: Running vs total processes

```bash
# Process states
ps -eo state | sort | uniq -c
# Or simpler:
echo "Processes: $(ps ax | wc -l) total, $(ps r | wc -l) running"
```

### 8. GPU Utilization (If Applicable)
**Missing**: GPU stats for compute servers

```bash
# NVIDIA GPUs
nvidia-smi --query-gpu=index,utilization.gpu,memory.used,memory.total,temperature.gpu \
    --format=csv,noheader,nounits

# AMD GPUs
rocm-smi --showuse --showmeminfo --showtemp
```

### 9. Service/Daemon Status (Missing)
**Missing**: Critical service health

```bash
# Check systemd services
systemctl list-units --type=service --state=running --no-pager | wc -l
systemctl list-units --type=service --state=failed --no-pager

# Specific important services
for svc in sshd postgresql docker; do
    systemctl is-active $svc 2>/dev/null && echo "$svc: active" || echo "$svc: inactive"
done
```

### 10. Security/Audit Data (Missing)
**Missing**: Failed login attempts, sudo usage

```bash
# Failed SSH attempts (last hour)
journalctl -u sshd --since "1 hour ago" | grep -i "failed" | wc -l

# Failed login attempts
lastb -F -s "-1 hour" | wc -l

# Recent sudo usage
journalctl -u sudo --since "1 hour ago" -o cat | grep COMMAND | wc -l
```

## Recommended New Metrics Priority

### High Priority (Should Add)
1. ✅ **Actual CPU utilization %** (not just load average)
2. ✅ **Network throughput** (RX/TX bytes per interface)
3. ✅ **Disk I/O rates** (reads/writes per second)
4. ✅ **Swap usage** (critical for memory pressure)
5. ✅ **Per-user I/O statistics** (disk read/write)

### Medium Priority (Nice to Have)
6. **Temperature sensors** (if hardware monitoring available)
7. **Network errors/drops** (quality metrics)
8. **Process state breakdown** (running/sleeping/zombie)
9. **Failed login attempts** (security monitoring)
10. **Service health checks** (critical daemons)

### Low Priority (Optional)
11. GPU utilization (if compute workloads exist)
12. Memory pressure stall info (Linux 4.20+)
13. Per-filesystem I/O (if multiple mounts)

## Implementation Strategy

### Option 1: Enhanced Scripts (Recommended)
- Keep current structure
- Add new metrics to existing scripts
- Expand database schema to store new fields

### Option 2: Use Existing Tools
```bash
# Consider using established monitoring tools:
- **collectd**: Lightweight, modular, C-based
- **node_exporter**: Prometheus metrics (if you want time-series)
- **atop**: Comprehensive system monitoring
- **dstat**: Real-time resource stats
```

### Option 3: Hybrid Approach
- Use custom scripts for server-specific info
- Use `node_exporter` or similar for detailed metrics
- Parse both sources in DataCollection service

## Backward Compatibility Note
If you add new metrics, ensure database schema migrations are handled properly and frontend can gracefully handle missing fields from older data.
