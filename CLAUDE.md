# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a containerized server monitoring dashboard system that collects metrics from multiple remote servers and displays them in a web-based dashboard. The system consists of three main components:

1. **DataCollection Backend** (`srcs/DataCollection/`) - Python service that monitors remote servers via SSH
2. **Unified Dashboard** (`srcs/Backend/`) - Flask application serving both REST API and web dashboard
3. **PostgreSQL Database** - Stores collected metrics and user activity data

## Architecture

The system uses Docker Compose to orchestrate **three services**:
- `postgres`: PostgreSQL database container
- `datacollection`: Python service that executes monitoring scripts on remote servers
- `dashboard`: Unified Flask application serving API + web dashboard on port 80

### Data Flow
1. DataCollection service connects to remote servers via SSH using credentials from environment variables
2. Executes bash monitoring scripts (`BashGetInfo.sh`, `TopUsers.sh`) on remote servers
3. Parses output and stores metrics in PostgreSQL database
4. Dashboard service provides REST API endpoints and renders the web dashboard
5. Dashboard frontend (vanilla HTML/CSS/JS + Chart.js) queries API and renders interactive views

### Database Schema
- `server_metrics`: System metrics (CPU, RAM, disk usage, connections, users)
- `top_users`: Per-user resource consumption data

## Dashboard Architecture (Unified Flask App)

The dashboard is a unified Flask application (`srcs/Backend/app.py`) combining API and frontend:

### Backend Structure
- **`app.py`** - Application factory with all API endpoints and error handlers
- **`flask_config.py`** - KU brand colors, dashboard config, fonts, thresholds
- **`blueprints/dashboard.py`** - Dashboard page routes (5 tabs)

### Frontend Structure (Vanilla HTML/CSS/JS)
- **Templates** (`templates/`) - Jinja2 templates
  - `base.html` - Base layout with header, theme toggle, scripts
  - `dashboard/index.html` - Main dashboard with tab navigation
  - `dashboard/panels/` - Tab panel templates (overview, servers, users, analytics, network)
  - `errors/` - 404 and 500 error pages
- **Static CSS** (`static/css/`) - Modular stylesheets
  - `main.css` - Core design system (variables, header, buttons, cards, footer)
  - `dashboard.css` - Server cards, progress rings, overview grid
  - `dark-mode.css` - Rich dark theme with blue glow accents
  - `tabs.css` - Tab navigation with sliding indicator
  - `cards.css` - Toast notifications, metric cards, alert cards
  - `tables.css` - Data tables with alternating rows, search, pagination
  - `charts.css` - Chart containers, controls, network grids
  - `animations.css` - Skeleton loading, stagger animations, micro-interactions
- **Static JS** (`static/js/`) - Modular JavaScript
  - `api.js` - API client with retry logic (3 attempts, exponential backoff, 10s timeout)
  - `dashboard.js` - Main data loading, rendering (progress rings, trend arrows)
  - `charts.js` - Chart.js manager with gradient fills, theme-aware colors
  - `tabs.js` - Tab switching with sliding indicator animation
  - `export.js` - JSON and CSV export with dropdown menu
  - `theme.js` - Dark mode toggle with localStorage persistence
  - `toast.js` - Toast notification system
  - `time.js` - System time display
  - `mobile.js` - Touch optimizations

### KU Brand Guidelines
- Primary: `#003DA5` (KU Blue, Pantone 293C)
- Secondary: `#6F5091` (KU Purple)
- Accent: `#78D64B` (KU Green)
- Font: Inter (closest free alternative to DIN Next)
- All colors defined in `flask_config.py` and CSS variables in `main.css`

## Development Commands

### Docker Operations
```bash
# Build and start all services (3 containers)
make build

# Start services (without rebuild)
make up

# Stop services
make down

# Clean up containers and images
make clean

# Complete cleanup (removes volumes, networks, and images)
make cclean

# Restart all services
make restart

# View logs for specific service
make logs-db              # PostgreSQL logs
make logs-DataCollection  # DataCollection service logs
make logs-Dashboard       # Dashboard logs

# Follow logs in real-time
make logs-follow

# Check service status
make ps
make status
```

### Service-Specific Operations
```bash
# Restart specific service
make restart-service SERVICE=Dashboard

# Rebuild specific service
make rebuild-service SERVICE=DataCollection

# Shell into specific service
make shell SERVICE=postgres
```

### Dependency Management (UV Package Manager)

This project uses **UV** (https://docs.astral.sh/uv/), a fast Python package manager, instead of pip.

**Managing Dependencies:**
```bash
cd srcs/Backend  # or DataCollection or schema
uv sync

# Add/remove dependencies
uv add requests
uv remove requests

# Run Python scripts with UV
uv run app.py
```

**Docker Integration:**
All Dockerfiles use UV for dependency installation:
```dockerfile
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen
```

### Database Access
```bash
# Connect to PostgreSQL directly
psql -h localhost -U postgres -d server_db
```

## Configuration

### Environment Variables
Create `.env` file with:
- `POSTGRES_PASSWORD`: Database password
- `SERVER{1-7}_NAME`: Server display names
- `SERVER{1-7}_HOST`: Server IP addresses
- `SERVER{1-7}_USERNAME`: SSH usernames
- `SERVER{1-7}_PASSWORD`: SSH passwords
- `DEBUG`: Set to "True" for debug mode

### Dashboard Configuration
Edit `srcs/Backend/flask_config.py`:
- `DASHBOARD_CONFIG`: Title, refresh interval (default 15min), logo
- `PERFORMANCE_THRESHOLDS`: Alert thresholds for CPU/RAM/disk
- `KU_COLORS`: Khalifa University brand colors
- `CHART_CONFIG`: Default chart settings and time ranges
- `FONTS`: Font families and CDN URLs

## API Endpoints

The unified dashboard (`srcs/Backend/app.py`) provides REST endpoints at `/api/`:

### Server Metrics
- `GET /api/servers/metrics/latest` - Latest metrics for all servers
- `GET /api/servers/<server_name>/metrics/historical/<hours>` - Historical data
- `GET /api/servers/<server_name>/status` - Current status
- `GET /api/servers/list` - List of all available servers

### User Data
- `GET /api/users/top` - Top users across all servers
- `GET /api/users/top/<server_name>` - Top users for specific server

### System Overview
- `GET /api/system/overview` - Real-time system statistics and trends
- `GET /api/health` - Health check

## Common Development Tasks

### Adding a New Dashboard Component
1. Create or modify panel template in `templates/dashboard/panels/`
2. Add data loading function in `static/js/dashboard.js`
3. Add API method in `static/js/api.js` if new endpoint needed
4. Add CSS styles in appropriate stylesheet
5. Register in tab switcher if new tab needed

### Adding a New API Endpoint
1. Define route in `srcs/Backend/app.py`
2. Add database query function
3. Format response as `{'success': bool, 'data': ..., 'message': str}`
4. Add corresponding method in `static/js/api.js`

### Modifying CSS
- Design system variables are in `main.css` `:root` block
- Dark mode overrides in `dark-mode.css` under `[data-theme="dark"]`
- Each section has its own CSS file for modularity

## Important Files

### Dashboard Key Files
- `srcs/Backend/app.py` - Unified Flask application (API + frontend)
- `srcs/Backend/flask_config.py` - All configuration constants
- `srcs/Backend/blueprints/dashboard.py` - Dashboard page routes
- `srcs/Backend/templates/base.html` - Base HTML template
- `srcs/Backend/templates/dashboard/index.html` - Main dashboard template
- `srcs/Backend/static/css/main.css` - Core design system
- `srcs/Backend/static/js/dashboard.js` - Main dashboard logic

### Legacy Files (kept for rollback)
- `srcs/Frontend/` - Previous Dash-based frontend (not in use)
- `srcs/Nginx/` - Previous Nginx proxy config (not in use)
- `srcs/Backend/api.py` - Standalone API fallback

## Code Quality Standards

### Error Handling
- All API calls use retry logic with exponential backoff (in `api.js`)
- All user-facing operations show toast notifications on success/failure
- All exceptions logged with context using Python `logger.error(..., exc_info=True)`
- Empty/error states with retry buttons in all dashboard panels

### Validation
- All API responses validated for structure before rendering
- All HTML content escaped via `escapeHtml()` to prevent XSS
- Server names URL-encoded with `encodeURIComponent()` in API calls

## Troubleshooting

### Dashboard not loading
```bash
# Check if service is running
docker ps | grep Dashboard

# Check logs for errors
make logs-Dashboard

# Restart service
make restart-service SERVICE=dashboard
```

### API not responding
```bash
# Check health endpoint
curl http://localhost/api/health

# Check Dashboard container logs
make logs-Dashboard-tail
```

## Development Notes

- Services communicate via Docker network `backend`
- Dashboard served on `localhost:80` (unified port for API + frontend)
- Database persisted in Docker volume `postgres_data`
- Source code mounted as volumes for live development
- Dashboard uses API endpoints internally (never direct DB from browser)
- All containers configured with `init: true` for proper signal handling
- Auto-refresh interval: 15 minutes (configurable in `flask_config.py`)
- Dark mode: toggle button or Ctrl+D keyboard shortcut
- Export: JSON and CSV formats via dropdown menu
