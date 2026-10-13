# Code review fix plan

First written 2026-05-04. Status re-checked against the code on 2026-10-12: items are
**done**, **open**, or **dropped** (no longer applies). Open items are in priority order
within each section.

## 1. Security

| Item | Status |
| --- | --- |
| Root password for KSRC1/2/3/5 was committed in `SSH_KEY_MIGRATION.md` (public repo, since `c7df345`) | **Open — urgent.** Removed from the current files; still in git history. Change the password on those servers, then decide on rewriting history. |
| Move collection from passwords to SSH keys, as a non-root `monitoring` account | **Open.** Collector supports `SERVER{n}_KEY_FILE`; no server uses it yet. Steps: [SSH_KEY_MIGRATION.md](SSH_KEY_MIGRATION.md). |
| HTTPS (or a TLS-terminating proxy) before wider student use | **Open.** |
| Restrict CORS (`CORS(app)` allows every origin) | **Open.** The pages are same-origin, so CORS can probably be removed. |
| Fail startup when `SECRET_KEY` is missing or the dev default | **Open.** `flask_config.py` falls back to `dev-secret-key-change-in-production`. |
| Stop returning raw exception text in API JSON | **Open.** 16 handlers return `str(e)`; log it with an ID and return a generic message. |
| Pin SSH host keys instead of `StrictHostKeyChecking=accept-new` | **Open.** |
| Passwords on the SSH command line or in logs | **Done.** `SSHPASS` env + `sshpass -e`; errors never include the command. |
| Remove `ssh-rsa` algorithm overrides | **Dropped.** KSRC1/KSRC2 run RHEL 6.6 (OpenSSH 5.3) and need them. |

## 2. Correctness bugs found in review

All fixed 2026-10-13.

| Item | Status |
| --- | --- |
| Server Details "Performance rating" used `cpu * 10` with CPU in percent, so any server above ~8 % CPU was Poor (`getPerformanceRating`, `dashboard.js`) | **Done.** Weights 0.4 CPU / 0.4 RAM / 0.2 disk; score stays 0–100. |
| Offline threshold differed: Server Details cards and `/api/system/overview` used 15 min (one collection interval) | **Done.** 30 min everywhere (`STALE_AFTER_MINUTES`). |
| `/api/servers/<name>/status` checked warning thresholds before staleness | **Done.** Staleness first. |
| `/api/servers/metrics/latest` (and `/api/system/overview`) joined on `MAX(timestamp)` | **Done.** Shared `LATEST_METRICS_SQL` (`DISTINCT ON`). |
| Cap `hours` on `/api/servers/<name>/metrics/historical/<hours>` | **Done.** 1 h – 90 days, like user history. |
| Physical CPU count was 0 where `/proc/cpuinfo` has no `physical id` | **Done.** Falls back to `lscpu` sockets, else NULL (shown as "?"). |
| Show why a server is not reporting | **Done.** `server_collection_status` (last attempt, last success, last error per server); shown in the overview fleet table, on server pages and in the "stopped reporting" attention item. |

## 3. Data collection

All findings of the 2026-09-24 collector review are fixed except one; see
[srcs/DataCollection/REVIEW.md](../../srcs/DataCollection/REVIEW.md).

| Item | Status |
| --- | --- |
| One schema source of truth | **Done.** `init_db()` in `backend.py`; the YAML schema, generators and migrations were removed. |
| Versioned, field-checked script output (no comma-separated parsing) | **Done.** |
| Timeouts on remote scripts; cron overlap | **Done.** |
| Current vs historical per-user data | **Done.** `top_users` (current) + `top_users_history`. |
| Network counters as rates | **Done.** `server_network` rates per interval. |
| Index `server_metrics(server_name, timestamp)` | **Done.** `top_users(server_name, cpu)` not added; the table is small. |

## 4. Dashboard

| Item | Status |
| --- | --- |
| Overview answers "which server should I use?" | **Done.** Fleet table ranked by free capacity, best server starred. |
| Per-server freshness and stale state | **Done** on the overview and server pages. |
| Tab ARIA ids | **Done** (`partials/nav.html`). |
| Bundle Chart.js, Font Awesome and the font locally (campus networks may block CDNs) | **Open.** |
| Duplicate event listeners after refresh; mobile layout of the User Activity table | **Not re-checked.** |
| "Green for online" | **Dropped.** KU blue is used for OK states by design (brand guidelines). |

## 5. Tests and tooling

| Item | Status |
| --- | --- |
| Parser and collector tests | **Done.** `srcs/DataCollection/tests` (run the scripts locally). |
| Rule tests (insights, server pages, licenses) | **Done.** `srcs/Backend/tests`. |
| API endpoint tests against a test database | **Open.** |
| JavaScript tests, a browser smoke test, `shellcheck`, CI | **Open.** |

## 6. Housekeeping

| Item | Status |
| --- | --- |
| Remove historical docs | **Done** (2026-10-12). |
| Remove `srcs/Backend/api.py` and `srcs/DataCollection/Dockerfile.old` (unused) | **Open.** |
| Rename `DesginGuideLine/` | **Open.** Update the references in CLAUDE.md when renaming. |
