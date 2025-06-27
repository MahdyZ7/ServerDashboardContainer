# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a containerized server monitoring dashboard system that collects metrics from multiple remote servers and displays them in a web-based dashboard. The system consists of four main components:

1. **DataCollection Backend** (`srcs/DataCollection/`) - Python service that monitors remote servers via SSH
2. **API Backend** (`srcs/Backend/`) - Flask REST API service for data access
3. **Frontend Dashboard** (`srcs/Frontend/`) - Dash web application for visualizing server metrics
4. **PostgreSQL Database** - Stores collected metrics and user activity data

## Architecture

The system uses Docker Compose to orchestrate four services:
- `postgres`: PostgreSQL database container 
- `datacollection`: Python service that executes monitoring scripts on remote servers
- `api`: Flask REST API service served on port 5000
- `frontend`: Dash web application served on port 3000

### Data Flow
1. DataCollection service connects to remote servers via SSH using credentials from environment variables
2. Executes bash monitoring scripts (`BashGetInfo.sh`, `TopUsers.sh`) on remote servers
3. Parses output and stores metrics in PostgreSQL database
4. API service provides REST endpoints for accessing stored data
5. Frontend queries API and renders interactive dashboard with server status, user activity, and historical metrics

### Database Schema
- `server_metrics`: System metrics (CPU, RAM, disk usage, connections, users)
- `top_users`: Per-user resource consumption data

## Development Commands

### Docker Operations
```bash
# Build and start all services
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

# View logs for all services
make logs

# View logs for specific service
make logs-db          # PostgreSQL logs
make logs-DataCollection  # Backend service logs
make logs-Frontend    # Dashboard logs

# Follow logs in real-time
make logs-follow

# Debug mode (non-detached)
make debug

# Check service status
make ps
make status
```

### Service-Specific Operations
```bash
# Restart specific service
make restart-service SERVICE=Frontend

# Rebuild specific service
make rebuild-service SERVICE=DataCollection

# Shell into specific service
make shell SERVICE=postgres
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

### Dependencies
- **DataCollection**: `psycopg2`, `python-dotenv`
- **API Backend**: `flask`, `flask-cors`, `psycopg2`, `python-dotenv`
- **Frontend**: `dash`, `pandas`, `plotly`, `requests`, `python-dotenv`

## Key Components

### DataCollection Service (`srcs/DataCollection/backend.py`)
- Main monitoring loop that runs every 5 minutes
- SSH-based remote script execution using `BashGetInfo.sh`
- Data parsing and PostgreSQL storage
- Server availability checking via ping

### API Backend Service (`srcs/Backend/api.py`)
- Flask REST API with CORS support
- Endpoints for server metrics, user data, and system overview
- Database connection management and error handling
- JSON response formatting with proper error codes

### Frontend Dashboard (`srcs/Frontend/Dash.py` and `enhanced_dash.py`)
- Multi-tab Dash application with Khalifa University branding
- Real-time server status cards with gauge visualizations
- User activity tables with filtering and sorting
- Historical metrics graphs with time range selection
- Auto-refresh every 30 seconds
- API-based data fetching instead of direct database queries

### Monitoring Scripts
- `BashGetInfo.sh`: SSH connection wrapper for executing remote scripts
- `mini_monitering.sh`: System metrics collection
- `TopUsers.sh`: User activity and resource usage collection

## API Endpoints

The API backend (`srcs/Backend/api.py`) provides the following REST endpoints:

### Server Metrics
- `GET /api/servers/metrics/latest` - Latest metrics for all servers
- `GET /api/servers/<server_name>/metrics/historical/<hours>` - Historical data for specific server
- `GET /api/servers/<server_name>/status` - Current status of specific server
- `GET /api/servers/list` - List of all available servers

### User Data
- `GET /api/users/top` - Top users across all servers
- `GET /api/users/top/<server_name>` - Top users for specific server

### System Overview
- `GET /api/system/overview` - Real-time system statistics and trends
- `GET /api/health` - API health check

## Development Notes

- Services communicate via Docker network `backend`
- API backend served on `localhost:5000`
- Frontend served on `localhost:3000` 
- Database persisted in Docker volume `postgres_data`
- Source code mounted as volumes for development
- All containers configured with `init: true` for proper signal handling
- Frontend uses API endpoints instead of direct database connections for better separation of concerns