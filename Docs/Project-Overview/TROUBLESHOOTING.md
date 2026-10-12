# Troubleshooting

Three containers: `postgres`, `DataCollection` (cron + SSH collectors) and `Dashboard`
(Flask, published on port 80). Start every investigation with:

```bash
make ps                          # all three running? Dashboard healthy?
curl http://localhost/api/health
make logs-DataCollection-tail    # last collection runs
make logs-Dashboard-tail
```

## Dashboard

**Page does not load / port 80 already in use.** Something on the host holds port 80
(httpd or a system nginx).

```bash
sudo lsof -i :80
make fix-port-conflict           # stops and disables httpd / nginx on this host
make up
```

**Code changes do not show up.** Source is bind-mounted, but the app runs without the
reloader, so Python and template changes need `make restart-service SERVICE=dashboard`.
Static CSS/JS URLs carry the file's modification time, so a normal browser reload picks
them up.

**Panels show "Failed to load".** Open the failing endpoint directly (e.g.
`curl http://localhost/api/overview/fleet`); the JSON `error` and the Dashboard log name the
cause. A `relation "…" does not exist` error means the collector has not created a new
table yet: tables are created by `init_db()` in `srcs/DataCollection/backend.py` on the next
collection run (`make collect-once`).

## A server shows "Not reporting"

The overview greys out a server after 30 minutes without data. The collector log says why:

```bash
make logs-DataCollection | grep -E "ERROR.*<SERVER NAME>" | tail -3
```

| Log message | Meaning and fix |
|---|---|
| `SSH connection failed … No route to host` / `timed out` | Host down or unreachable from KSRC7. Check the machine and the network path (`ping`, `ssh` from the host). |
| `authentication failed (wrong password)` | `SERVER{n}_PASSWORD` in `.env` no longer matches. Update it, or switch the server to a key ([SSH_KEY_MIGRATION.md](SSH_KEY_MIGRATION.md)). |
| `Host key verification failed` | The server's SSH host key changed (reinstall?). Confirm with its admin before removing the old entry from the container's `known_hosts`. |
| `timed out after 90s` | The script hung on the server, usually a stuck NFS mount in `df`. Check `mount` and `dmesg` there. |
| `expected format_version=2` | The server ran an old copy of a script; the collector sends the scripts on every run, so check that the container mounts `srcs/DataCollection`. |

Changes to `.env` need `make restart-service SERVICE=datacollection` (cron jobs read the
container's environment).

## Server page details

- **Lab share "Not mounted" or "Not responding".** Read from `/proc/mounts`; "not responding"
  means `stat -f` on the mount did not answer within 10 s (a hung NFS server or network).
  Check on the server with `mount | grep KSRC_lab_share` and `timeout 10 df -h /KSRC_lab_share`.
  The name checked comes from `REQUIRED_MOUNTS` in `.env`.
- **"Session detail arrives with the next collection."** The latest run predates the
  session/mount checks, or it failed; it fills in after the next 15-minute run.
- **VNC desktop shows "No viewer" while someone uses it.** Viewers are counted from
  established TCP connections on the desktop's port. A viewer that connects through a proxy
  on another host is not visible from the server.

## EDA licenses

The license job runs every 5 minutes on `LICENSE_QUERY_SERVER` (KSRC7).

```bash
make logs-DataCollection | grep -i license | tail -5
```

- **"Server not answering" / query failed:** run the same query by hand on KSRC7,
  `"$LICENSE_SYNOPSYS_LMUTIL" lmstat -c "$LICENSE_SYNOPSYS_SERVER" -S snpslmd`. The dashboard keeps
  the last good figures meanwhile and never shows a failed query as zero use.
- **Validity "Server up" with no expiry:** expiry dates (`lmstat -i`) arrive with the next run.

## Database

```bash
make logs-db
make db-stats                    # row counts of server_metrics and top_users
make shell SERVICE=postgres      # then: psql -U postgres -d server_db
```

Data older than 90 days is removed by the weekly cleanup job (Sundays 23:05).
