# Server Dashboard Container

Containerized server monitoring dashboard for student-facing server status, usage, and activity visibility.

Last reviewed: 2026-05-04

## Current State

This repository currently runs as a three-service Docker Compose stack:

| Service | Container | Purpose |
| --- | --- | --- |
| `postgres` | `postgres` | PostgreSQL database for server metrics and top-user records |
| `datacollection` | `DataCollection` | Cron-driven Python collector that connects to remote Linux servers over SSH |
| `dashboard` | `Dashboard` | Unified Flask app serving the REST API and the Jinja/HTML/CSS/JS dashboard |

The active frontend is not Dash. It is served by Flask templates in `srcs/Backend/templates/` with static JavaScript and CSS in `srcs/Backend/static/`. Charts are rendered with Chart.js in the browser.

## Architecture

```text
Browser
  |
  | HTTP :80
  v
Dashboard container
  Flask app on :5000
  - Jinja dashboard pages
  - REST API under /api
  |
  | PostgreSQL connection on backend Docker network
  v
PostgreSQL container
  - server_metrics
  - top_users

DataCollection container
  - cron schedules collection jobs
  - backend.py reads SERVER*_ environment variables
  - BashGetInfo.sh sends monitoring scripts to remote servers over SSH
  - parsed metrics are inserted into PostgreSQL
```

## Repository Layout

```text
.
├── docker-compose.yml
├── Makefile
├── README.md
├── CLAUDE.md
├── fix-port-conflict.sh
├── setup-autostart.sh
├── DesginGuideLine/
│   └── KU_Guidelines_2020_V7.pdf
├── Docs/
│   ├── INDEX.md
│   ├── Frontend-Improvements/
│   ├── Monitoring-Analysis/
│   ├── Project-Overview/
│   └── Schema-System/      # superseded, history only
└── srcs/
    ├── Backend/
    │   ├── app.py
    │   ├── api.py
    │   ├── flask_config.py
    │   ├── blueprints/
    │   ├── static/
    │   ├── templates/
    │   └── utils/
    └── DataCollection/
        ├── backend.py
        ├── BashGetInfo.sh
        ├── TopUsers.sh
        ├── LicenseUsage.sh
        ├── run-collection.sh
        ├── mini_monitering.sh
        ├── crontab
        └── start-cron.sh
```

## Features

- Server overview cards with online, warning, and offline status.
- Detailed server metrics for CPU, RAM, disk, swap, TCP connections, SSH, VNC, logged users, and cumulative network bytes.
- Historical charts for individual servers.
- User activity table with search, server filter, sorting, CPU/memory/disk/process data, top process, and I/O counters.
- Network activity panel with connection summaries.
- JSON and CSV export.
- Light and dark themes.
- Auto-refresh interval configured in `srcs/Backend/flask_config.py`.

## Configuration

Create a root `.env` file. At minimum:

```env
POSTGRES_PASSWORD=change-this
SECRET_KEY=change-this
DEBUG=False

SERVER1_NAME=Example Server
SERVER1_IP=192.0.2.10
SERVER1_USERNAME=student-monitor
SERVER1_PASSWORD=change-this
```

The collector reads `SERVER1_*` through `SERVER9_*` from environment variables. `SERVER*_IP`, `SERVER*_USERNAME`, and `SERVER*_PASSWORD` are currently required by `srcs/DataCollection/backend.py`.

## Running The Stack

```bash
make build
make ps
```

Open:

```text
http://localhost
```

Useful commands:

```bash
make logs
make logs-follow
make logs-Dashboard-tail
make logs-DataCollection-tail
make db-stats
make collect-once
make collect-once-with-disk
make cron-logs
make down
```

## API Endpoints

The Flask app in `srcs/Backend/app.py` exposes:

| Endpoint | Purpose |
| --- | --- |
| `GET /api/health` | Dashboard service health check |
| `GET /api/health/<server_name>` | Basic HTTP health check for one configured server |
| `GET /api/servers/metrics/latest` | Latest metric row per server |
| `GET /api/servers/<server_name>/metrics/historical/<hours>` | Historical metrics for one server |
| `GET /api/servers/<server_name>/status` | Latest status and metrics for one server |
| `GET /api/servers/list` | Distinct server names found in metrics |
| `GET /api/users/top` | Top users across all servers |
| `GET /api/users/top/<server_name>` | Top users for one server |
| `GET /api/system/overview` | Aggregate dashboard statistics |

`srcs/Backend/api.py` is a legacy standalone API file. The Compose stack starts `srcs/Backend/app.py`.

## Data Collection

The DataCollection image installs cron and registers `srcs/DataCollection/crontab`.

Current schedule:

| Schedule | Action |
| --- | --- |
| Every 15 minutes | Collect server metrics |
| Daily at 23:17 | Collect user disk usage |
| Sundays at 23:00 | Run retention cleanup |

Remote collection flow:

1. `backend.py` reads server config from `.env`.
2. `server_online()` pings each server.
3. `BashGetInfo.sh` uses `sshpass` to run `mini_monitering.sh` and `TopUsers.sh` remotely.
4. Python parsers convert script output into dictionaries.
5. Records are stored in PostgreSQL.

Security note: password-based SSH via `sshpass` is still active and should be replaced with SSH key authentication. See `Docs/Project-Overview/CODE_REVIEW_FIX_PLAN.md`.

## Documentation

Start with:

- `Docs/INDEX.md`
- `Docs/Project-Overview/CODE_REVIEW_FIX_PLAN.md`
- `Docs/Project-Overview/SSH_KEY_MIGRATION.md`
- `Docs/Project-Overview/TROUBLESHOOTING.md`

The database schema and its migrations are defined in `init_db()` in `srcs/DataCollection/backend.py`.

## Known Gaps

- The active Compose stack has no Nginx container and no separate Dash frontend container.
- Several historical docs describe older or planned architecture. Treat this README and `Docs/INDEX.md` as the current entry points.

## Improvement Plan

The prioritized remediation plan is tracked in:

```text
Docs/Project-Overview/CODE_REVIEW_FIX_PLAN.md
```
