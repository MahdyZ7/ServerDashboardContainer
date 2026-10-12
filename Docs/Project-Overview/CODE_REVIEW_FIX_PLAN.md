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

| Item | Status |
| --- | --- |
| Server Details "Performance rating" uses `cpu * 10` with CPU in percent: any server above ~8 % CPU is rated Poor (`getPerformanceRating`, `dashboard.js`) | **Open.** |
| Offline threshold differs: Server Details cards use 15 min (one collection interval, so servers flicker "Offline" before each run); overview, server pages and API insights use 30 min | **Open.** Use 30 min everywhere. |
| `/api/servers/<name>/status` checks warning thresholds before staleness, so a stale server can show "warning" | **Open.** |
| `/api/servers/metrics/latest` joins on `MAX(timestamp)` (duplicates on ties); use `DISTINCT ON` like the newer endpoints | **Open.** |
| Cap `hours` on `/api/servers/<name>/metrics/historical/<hours>` | **Open.** (User history is already capped at 90 days.) |
| Physical CPU count is 0 where `/proc/cpuinfo` has no `physical id` (some VMs) | **Open.** |
| Show "collection failed: <reason>" instead of only "not reporting" (store the last error per server) | **Open.** |

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
