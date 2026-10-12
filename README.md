# Server Dashboard Container

Status dashboard for the KSRC research servers: which machine has room for a job, who is on
it (SSH and VNC), whether the lab share is mounted, what needs an administrator, and the state
of the Cadence and Synopsys license pools. Built to the Khalifa University 2020 brand
guidelines (`DesginGuideLine/KU_Guidelines_2020_V7.pdf`).

Live at `http://ksrc7.kunet.ae/`; each server has a page at `/server/<name>`.

## How it works

```text
Monitored servers (RHEL 6–9)            KSRC7 (this stack, Docker Compose)
  mini_monitering.sh  ◄── SSH ──┐   ┌──────────────────────────────────────────┐
  TopUsers.sh         ◄── SSH ──┤   │ DataCollection  cron: metrics every 15 min,│
  LicenseUsage.sh (KSRC7) ◄─────┘   │   licenses every 5 min, disk scan nightly  │
                                    │        │ parsed rows                       │
                                    │        ▼                                   │
                                    │ postgres (server_db)                       │
                                    │        ▲                                   │
                                    │ Dashboard  Flask: REST API + pages, :80    │
                                    └──────────────────────────────────────────┘
```

- **DataCollection** (`srcs/DataCollection/`): `backend.py` runs each script on each server
  through `BashGetInfo.sh` (scripts are sent over SSH, nothing is installed remotely), parses
  the versioned output (`parsers.py`, `license_parser.py`) and stores it. `init_db()` in
  `backend.py` is the schema.
- **Dashboard** (`srcs/Backend/`): `app.py` serves the API under `/api` and the pages
  (Jinja templates, plain CSS/JS, Chart.js).

## Pages

| Page | Shows |
| --- | --- |
| Usage Overview (`/`) | One-screen board: servers ranked by free capacity, what needs attention, license validity and use |
| Server Details | Per-server specification sheets; mounts, disks, network and services per machine |
| User Activity | Per-account CPU, memory, disk, I/O and licenses held; history per user |
| Performance Analytics, Network Monitor | Historical charts and network figures |
| Server page (`/server/<name>`) | Free CPU and memory, lab share, VNC desktops, SSH logins, top users |

## Setup

Create `.env` in the repository root (never committed):

```env
POSTGRES_PASSWORD=...
SECRET_KEY=...

SERVER1_NAME=KSRC1
SERVER1_HOST=ksrc1.kunet.ae
SERVER1_IP=10.10.19.73
SERVER1_USERNAME=monitoring
SERVER1_KEY_FILE=/keys/ksrc1_monitoring    # or SERVER1_PASSWORD=...

LICENSE_QUERY_SERVER=KSRC7                 # optional: EDA license collection
```

All variables, including `REQUIRED_MOUNTS`, `MONITORED_SERVICES` and the license settings, are
listed in [CLAUDE.md](CLAUDE.md#environment-variables). Prefer SSH keys over passwords:
[SSH_KEY_MIGRATION.md](Docs/Project-Overview/SSH_KEY_MIGRATION.md).

```bash
make build          # build and start the three containers
make ps             # status
make collect-once   # run a collection now instead of waiting for cron
```

Open `http://localhost/`.

## Everyday commands

```bash
make logs-DataCollection-tail    # collection runs and failures
make logs-Dashboard-tail
make restart-service SERVICE=dashboard        # after Python/template changes
make restart-service SERVICE=datacollection   # after .env changes
make enable-autostart            # start on boot (Docs/Project-Overview/AUTO_START.md)
```

## Tests

```bash
python3 -m unittest discover -s srcs/DataCollection/tests   # runs the collectors locally
python3 -m pytest -q srcs/Backend/tests
```

## Documentation

See [Docs/INDEX.md](Docs/INDEX.md).
