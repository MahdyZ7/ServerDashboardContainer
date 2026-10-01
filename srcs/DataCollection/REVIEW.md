# Data collection review — 2026-09-24

The current scripts provide a useful inventory, but several measurements do not
answer “who is making this server busy right now?” Fix measurement semantics and
failure reporting before adding more columns. Findings below refer to the scripts
as reviewed; only the license helper and Dockerfile packaging change are implemented.

## Fix status — 2026-10-01

Implementation step 1 and parts of steps 2–3 are done and were verified against the live
servers (RHEL 6.6 → 9.8). Tests: `python3 -m unittest discover -s srcs/DataCollection/tests -v`.

| Finding | Status |
| --- | --- |
| Since-boot CPU in `mini_monitering.sh` | **Fixed.** Two explicit `/proc/stat` samples; busy, iowait and steal reported separately (new `cpu_iowait_percent`, `cpu_steal_percent`); guest not double-counted; no sample → NULL, never a fallback. Memory now uses `MemAvailable` (`ram_available_mb`). |
| Lifetime `ps %CPU` per user | **Fixed** in `TopUsers.sh`: per-process tick deltas keyed by (pid, start time), summed by numeric UID. Unit: percent of one logical CPU. `UserInfo.sh` (unused) still uses `ps`. |
| `DECIMAL(5,2)` overflow | **Fixed.** `top_users.cpu` → `NUMERIC(9,2)`, `mem` → `(7,2)`, `disk` → `(12,2)`, load averages → `(8,2)`; guarded migrations. |
| Cumulative / silently-zero I/O | **Fixed.** New `io_read_bps` / `io_write_bps` interval rates; I/O is NULL when none of an account's processes is readable. `io_*_bytes` remains the live-process cumulative total. Coverage is still partial without root. |
| Account discovery by shell | **Fixed.** Union of process-owner UIDs, login-shell accounts and logged-in users; names resolved with `getent passwd UID`. |
| Password on command line / in logs | **Fixed.** Password goes through `SSHPASS` (`sshpass -e`); errors never include the command. `SERVER{n}_KEY_FILE` is supported (BatchMode). SSH connect/keepalive limits and Python deadlines added; absolute script paths; remote args quoted. |
| `top_users.timestamp` never refreshed | **Fixed.** Every upsert sets the observation time. |
| Disk sentinel 0 | **Fixed.** Disk is NULL when unknown; `disk_collected_at` added. Not-collected/timed-out scans keep the old value. |
| Disk scan roots | **Partly fixed.** Home from passwd (not `/home/$user`), null-safe paths, allocated size (`du -k`), `nice`/`ionice`, per-account timeout, unreadable roots reported unknown. Quotas not used. |
| Fragile parsing | **Fixed.** Versioned output: `key=value` for host metrics, `#format=2` + TSV for users, `LC_ALL=C`, exact UID matching, field-count validation, ISO login times. |
| Cron overlap / env quoting / ICMP gate | **Fixed.** `run-collection.sh` (NUL-safe env load + `flock` per job); SSH tried directly; per-user failures no longer discard host metrics; weekly cleanup no longer collides with the 15-min run. Needs an image rebuild to take effect. |
| Per-mount disk, network deltas, SSH/VNC sessions, PSI, history, license integration | **Open** (steps 3–4). |

## Findings, in priority order

| Priority | Location | Finding and recommended change |
| --- | --- | --- |
| High | `mini_monitering.sh:31–40` | The first `awk` assigns variables inside awk and prints nothing. The second awk receives empty shell variables, so the supposed half-second delta is actually a since-boot average. Capture both samples explicitly, include steal time, avoid double-counting guest fields, and report idle, iowait and steal separately. A valid 0% sample must not trigger the fallback. |
| High | `TopUsers.sh:35`, `UserInfo.sh:8` | `ps %CPU` is a lifetime average. Sample process CPU deltas over the same interval as host metrics. Aggregate by numeric UID, resolve display names afterwards, and label 100% as one logical CPU (also expose percent of whole-host capacity). |
| High | `backend.py:79–81` | Per-user CPU is `DECIMAL(5,2)`, allowing only 999.99. A user consuming ten or more cores can exceed that and reject the write. Increase precision and decide whether to store core equivalents or host-normalized percent. The disk field also tops out at 999.99 GiB. |
| High | `TopUsers.sh:17–30` | I/O is the cumulative sum of currently alive processes, not a rate or a stable user counter. Exits cause totals to fall; permission failures silently become zero. Calculate deltas per `(boot_id, PID, start_time)` before summing by UID; report inaccessible/exited processes and sample coverage. Consider cgroup accounting for persistent job totals. |
| High | `TopUsers.sh:89` | Selecting accounts by shell omits service/batch accounts and can miss directory users when NSS enumeration is disabled. Discover UIDs from running processes and union with login sessions; use `getent passwd UID` to resolve each owner. |
| High | `BashGetInfo.sh:8`, `backend.py:154–168,187–205` | Passwords enter the wrapper's command line, and logging a `CalledProcessError` can include that command and password. Follow the existing SSH-key migration plan, sanitize errors, set SSH connect/keepalive limits and a Python subprocess deadline. Use absolute script paths and safe remote argument quoting. |
| Medium | `backend.py:370–393`, `backend.py:cleanup_old_data()` | Upserts never refresh `top_users.timestamp`; cleanup can delete active rows based on their original insertion time. Update observation time on every write. Keep timestamped history separately if the dashboard should answer who used a resource earlier. |
| Medium | `backend.py:229,366` | Missing disk data and a measured zero share the same sentinel. Skipped scans preserve the existing value, but so does a genuine zero. Use nullable values plus `disk_collected_at` and an explicit collection status. |
| Medium | `TopUsers.sh:4–13` | Scanning `/home/user` and directories owned by that user in `/eda_work` measures selected trees, not ownership of every file. It misses nested ownership and nonstandard homes; `du -b` measures apparent size. Use filesystem quotas where available, or clearly label scan roots and allocated vs apparent size. Use null-delimited paths/arrays, one scan per root, and daily low-priority scans with time limits. |
| Medium | `mini_monitering.sh:23–26,47–64` | Filesystem totals hide individual full mounts (and omit NFS); SSH/VNC socket counts are not distinct people/sessions. Network fields are counters for only one chosen interface. Store per-mount capacity/inodes, separate connection/session/user counts, and interface identity plus RX/TX deltas, errors and drops. |
| Medium | `TopUsers.sh:35,66,70`, `backend.py:217,248` | The process table includes a header, usernames have a fixed width, process names are whitespace-split, usernames become regex patterns, login dates depend on locale, and “CSV” is parsed with `split(',')`. Prefer versioned JSON with numeric units, ISO timestamps, nulls and per-field status. Until then, use headerless UID-based output, exact comparisons and `LC_ALL=C`; validate field counts. |
| Medium | `crontab`, `backend.py:server_online()` | Scheduled jobs can overlap; reading the container environment through `xargs` destroys quoting. Use a single scheduler or `flock`, preserve environment values safely, and try SSH directly rather than requiring ICMP success. Separate disk/license failures from successful host metrics. |
| Medium (fixed here) | `Dockerfile:30` | The image omitted `mini_monitering.sh`; the Compose source bind mount masked the omission. The image now includes all collector scripts and the new license helper. Vendor `lmutil` remains an external runtime requirement. |

The CPU interpretation above follows the [procps ps manual](https://man7.org/linux/man-pages/man1/ps.1.html).

## What to collect next

| Question | Recommended measurements | Suggested cadence |
| --- | --- | --- |
| Is the host CPU saturated? | Sampled user/system/idle/iowait/steal %, load divided by online logical CPUs, runnable and uninterruptible tasks, CPU pressure | 1–5 second sample every 30–60 seconds |
| Is memory slowing jobs down? | `MemAvailable`, RSS by user, optional proportional set size (PSS), swap-in/out rates, major faults, memory pressure | 30–60 seconds; PSS less frequently |
| Is storage the bottleneck? | Per-device read/write bytes/s, IOPS, latency and queue depth; per-mount free bytes/inodes; I/O pressure; separate NFS client metrics where relevant | I/O every 30–60 seconds; capacity every 5 minutes |
| Who is consuming resources? | UID/user, PID/PPID, process start time, elapsed time, CPU rate, RSS/PSS, read/write rate, threads, state, executable, cgroup/job ID | Shared 1–5 second sample every 30–60 seconds |
| Who is logged in? | User, session ID, remote address, login time, terminal/display | Every 1–5 minutes; separate from process owners |
| Which license pool is busy? | Endpoint, vendor, feature, issued/in-use count, checkout owner/client host/time, query status/time | Start at 5 minutes, once per unique pool; tune after measuring query cost |

These intervals are starting recommendations. Fifteen-minute snapshots can miss
short EDA jobs entirely. A one-second sample each minute also misses activity between
samples; continuous collection or job accounting is needed for complete history.
RSS sums can double-count shared memory; label the metric or collect PSS when
permissions and overhead allow. A high CPU percentage alone does not imply overload:
queueing, memory/I/O pressure and job latency explain whether users are waiting.

Linux exposes resource-stall measurements under `/proc/pressure/{cpu,memory,io}`;
mark unsupported kernels as unavailable. See the [kernel PSI documentation](https://docs.kernel.org/accounting/psi.html).

For immediate interactive diagnosis, install sysstat on the monitored host and run:

```bash
LC_ALL=C mpstat -P ALL 1 5
LC_ALL=C pidstat -u -r -d -w -p ALL 1 5
LC_ALL=C iostat -y -dx 1 5
ps -eo uid,user:32,pid,ppid,etimes,nlwp,stat,rss,comm --sort=-rss
```

`pidstat` supplies interval CPU, faults and I/O by process; `iostat -y` skips the
initial since-boot report. Some process data needs additional read permissions.
Use field names or supported structured output rather than fixed column positions
when automating these tools. See [pidstat](https://man7.org/linux/man-pages/man1/pidstat.1.html)
and [iostat](https://man7.org/linux/man-pages/man1/iostat.1.html).

For the existing scripts, keep machine-readable output on stdout and diagnostics
on stderr. Add collection timestamps, duration, timeout/error status and coverage.
Use dependency checks and explicit handling of optional commands; blindly enabling
`set -e` on the current pipelines would turn expected missing data into aborted runs.
Full command arguments should be an opt-in diagnostic because they can contain
credentials or confidential design paths; executable/job identity is safer by default.

## Cadence and Synopsys license report

`LicenseUsage.sh` now queries the vendor daemons with `lmutil lmstat -S cdslmd`
and `-S snpslmd`. The report preserves the utility's feature totals and individual
checkout rows, including owner, client host/display and start time when provided.
It supports different vendor binaries, connection and whole-query timeouts, and
continues to the second vendor when the first fails. Known errors, including
per-feature errors, produce a nonzero exit code while retaining diagnostic output.
This is a human-readable CLI report; database/API/dashboard integration is not yet implemented.

With the endpoints confirmed for this installation:

```bash
export CDS_LIC_FILE='5280@ku1bpaawv043.kunet.ae'
export SNPSLMD_LICENSE_FILE='27030@ku1bpaawv043'
bash srcs/DataCollection/LicenseUsage.sh --active-only

# Select just one vendor, or omit --active-only to include unused features.
bash srcs/DataCollection/LicenseUsage.sh --vendor synopsys --active-only
```

The script uses `lmutil` from PATH by default. Override `CADENCE_LMUTIL` and
`SYNOPSYS_LMUTIL` (or the corresponding command-line options) with binaries from
your installed vendor distributions. For example, the Synopsys binary found here is
`/opt/synopsys/Installs/scl/2025.03-SP2/linux64/bin/lmutil`.
No proprietary binaries are downloaded or bundled with this project.
In a container, mount the vendor tools and required runtime libraries and explicitly
provide the environment; host shell settings are not automatically copied into Docker.
Alternatively, run the script over SSH on an EDA host where those tools already work.
For `BashGetInfo.sh`, use an absolute local script path and configure the environment
on the remote side; noninteractive SSH may not load the usual EDA setup files.

The live check on 2026-09-24 reached both daemons. Synopsys returned active checkout
owners and hosts. Cadence returned many `unsupported by licensed server` feature
errors, alongside some valid totals. Treat Cadence usage as incomplete and have the
license administrator investigate using the supported vendor utilities. This result
does not identify the underlying cause and does not mean those features are unused.

`lmstat` is a snapshot of served licenses. It does not prove that a process is
actively computing, and a handle is not a PID. Shared/duplicate-grouped licenses,
queued users and unserved licenses are not fully represented. Checkout time formats
may omit a year/timezone; retain the raw value and query timestamp instead of guessing.
The vendor documents the options and limits in the [FlexNet lmstat manual](https://docs.revenera.com/fnp/2025r1/LicAdmin_Guide/Content/helplibrary/lmstat.htm).
Cadence also documents [the license-path setting and lmutil command](https://community.cadence.com/cadence_technology_forums/pcb-design/f/pcb-design/35325/how-to-find-out-which-license-server-is-being-used).

For dashboard integration, add separate license-pool snapshots and checkout rows:

- Pool snapshot: observed time, configured endpoint/pool ID, vendor, feature,
  issued and in-use counts, query status, duration and last successful observation.
- Checkout: snapshot ID, feature/version, username, client host, display,
  license-server host/port, handle, raw checkout time, and seat count when reported.
- Correlate using normalized client host and username, with explicit host aliases;
  do not assume a checkout identifies a particular PID unless the vendor supplies it.
- Query a shared pool once rather than once per compute server. Keep feature IDs
  intact and maintain an optional friendly product-name mapping.
- Preserve the last successful snapshot as stale on failure; never turn failure into
  zero usage. Keep history for trends; investigate vendor reporting/accounting logs
  separately if denied requests or complete checkout durations are required.

## Implementation order and validation

1. Fix CPU sampling, CPU/disk numeric ranges, credentials in errors and timeouts.
2. Add versioned structured output, unknown/error states and correct observation times.
3. Add interval per-user CPU/I/O, pressure, per-device/per-mount data and history.
4. Integrate the license report using real output fixtures from the installed vendors.
   Update schema source, migrations, collector, API and UI together; generated and
   handwritten schema/parser definitions already need reconciliation.

Tests for the new helper run without a server:

```bash
python3 -m unittest discover -s srcs/DataCollection/tests -v
bash -n srcs/DataCollection/LicenseUsage.sh
```

They cover quoting/server lists, explicit configuration, checkout-owner preservation,
partial failures, errors with exit status zero, active-only filtering and deadlines.
Live checks validate connectivity and installed output formats; they do not establish
complete accounting coverage. No database migrations or production schedules were changed.
