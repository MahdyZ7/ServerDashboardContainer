# Server Dashboard Container

<div align="center">

**A comprehensive, containerized server monitoring system for real-time infrastructure oversight**

[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1.1-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Dash](https://img.shields.io/badge/Dash-3.1.0-00D4FF?logo=plotly&logoColor=white)](https://dash.plotly.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Latest-336791?logo=postgresql&logoColor=white)](https://www.postgresql.org/)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Architecture](#-architecture)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Development](#-development)
  - [Schema-Driven Architecture](#-new-schema-driven-architecture) ⭐ NEW!
- [Testing](#-testing)
- [API Documentation](#-api-documentation)
- [Documentation](#-documentation) ⭐ NEW!
- [Contributing](#-contributing)
- [Troubleshooting](#-troubleshooting)
- [License](#-license)

---

## 🎯 Overview

**Server Dashboard Container** is a containerized monitoring solution designed to collect, store, and visualize real-time metrics from multiple remote servers. Built with a microservices architecture, it provides insights into CPU usage, memory consumption, disk space, network connections, and user activity across your entire infrastructure.

### What This System Does

1. **Monitors Remote Servers** - Connects to multiple Linux servers via SSH and executes monitoring scripts
2. **Collects Metrics** - Gathers system metrics (CPU, RAM, disk, network) and user activity data every 15 minutes
3. **Stores Data** - Persists historical metrics in a PostgreSQL database for trend analysis
4. **Provides API Access** - Exposes REST endpoints for programmatic access to server data
5. **Visualizes Data** - Presents an interactive web dashboard with real-time status cards, graphs, and tables

### Use Cases

- **Infrastructure Monitoring** - Track health and performance of server clusters
- **Capacity Planning** - Analyze historical trends to predict resource needs
- **User Activity Tracking** - Monitor who is using which servers and their resource consumption
- **Alerting** - Identify servers with high resource usage or offline status
- **Compliance** - Maintain records of system usage and user activity

---

## ✨ Features

### Core Functionality

- **Multi-Server Monitoring** - Monitor up to 7 servers simultaneously (easily extensible)
- **Real-Time Metrics** - Live CPU load, RAM usage, disk space, network connections, logged users
- **Historical Data** - Store and analyze metrics over time (configurable retention periods)
- **User Activity Tracking** - Per-user CPU, memory, and disk usage across all servers
- **Automatic Data Collection** - Scheduled collection every 15 minutes via cron
- **REST API** - Full-featured API for integration with other tools

### Dashboard Features

- **Interactive UI** - Built with Plotly Dash for responsive, interactive visualizations
- **Status Cards** - Real-time server status with color-coded alerts (green/yellow/red)
- **Gauge Visualizations** - Intuitive gauge charts for CPU, RAM, and disk usage
- **Historical Graphs** - Time-series charts for trend analysis with configurable time ranges
- **User Tables** - Sortable, filterable tables showing top users and their resource consumption
- **Export Functionality** - Download data as Excel files for offline analysis
- **Auto-Refresh** - Configurable auto-refresh (default: 30 seconds)
- **Toast Notifications** - User-friendly success/error notifications

### Performance & Reliability

- **Error Handling** - Comprehensive error handling with automatic retry logic (3 attempts with exponential backoff)
- **Input Validation** - All inputs validated and sanitized
- **Health Checks** - Docker health checks for all services
- **Graceful Degradation** - System continues operating even if individual servers are unavailable
- **Structured Logging** - Detailed logs for debugging and monitoring


---

## 🏗 Architecture

### System Components

The system consists of 5 Docker containers orchestrated via Docker Compose:

```
┌─────────────────────────────────────────────────────────────┐
│                        Nginx Reverse Proxy                  │
│                         (Port 80)                           │
└────────────────────┬───────────────────┬───────────────────┘
                     │                   │
          ┌──────────▼─────────┐  ┌─────▼──────────┐
          │   Frontend (Dash)  │  │  API (Flask)   │
          │     Port 3000      │  │   Port 5000    │
          └──────────┬─────────┘  └─────┬──────────┘
                     │                   │
                     │                   │
          ┌──────────▼───────────────────▼──────────┐
          │          PostgreSQL Database            │
          │              Port 5432                  │
          └──────────▲─────────────────────────────┘
                     │
          ┌──────────┴─────────┐
          │   DataCollection   │
          │   (SSH Collector)  │
          └────────────────────┘
                     │
          ┌──────────▼─────────┐
          │  Remote Servers    │
          │   (via SSH)        │
          └────────────────────┘
```

### Component Details

#### 1. **Nginx** (`nginx`)
- **Role**: Reverse proxy and load balancer
- **Port**: 80 (HTTP)
- **Purpose**: Routes traffic to Frontend and API services

#### 2. **PostgreSQL** (`postgres`)
- **Role**: Database for metrics storage
- **Port**: 5432 (internal only)
- **Volumes**: Persistent storage at `postgres_data`
- **Tables**:
  - `server_metrics` - System-level metrics
  - `top_users` - Per-user resource consumption

#### 3. **DataCollection** (`backend`)
- **Role**: SSH-based metrics collector
- **Language**: Python 3.8+
- **Schedule**: Runs every 15 minutes via cron
- **Key Scripts**:
  - `backend.py` - Main collection loop
  - `BashGetInfo.sh` - SSH connection wrapper
  - `mini_monitering.sh` - System metrics script
  - `TopUsers.sh` - User activity script

#### 4. **API Backend** (`api`)
- **Role**: REST API for data access
- **Framework**: Flask 3.1.1
- **Port**: 5000 (internal)
- **Features**: CORS support, health checks, structured error responses

#### 5. **Frontend** (`frontend`)
- **Role**: Web dashboard
- **Framework**: Dash 3.1.0 (Plotly)
- **Port**: 3000 (internal)
- **Features**: Multi-tab interface, real-time updates, data export

### Data Flow

1. **Collection Phase** (every 15 minutes)
   - DataCollection service connects to remote servers via SSH
   - Executes bash scripts to gather metrics
   - Parses output and validates data
   - Stores metrics in PostgreSQL

2. **Query Phase** (on-demand)
   - Frontend sends requests to API
   - API queries PostgreSQL database
   - Data returned as JSON

3. **Display Phase** (real-time)
   - Frontend receives JSON data
   - Dash processes and visualizes data
   - User interacts with dashboard
   - Auto-refresh keeps data current

---

## 📦 Prerequisites

### Required Software

- **Docker** (version 20.10+)
- **Docker Compose** (version 2.0+)
- **Make** (for convenience commands)
- **Git** (for cloning repository)

### System Requirements

- **CPU**: 2+ cores recommended
- **RAM**: 4GB minimum, 8GB recommended
- **Disk**: 10GB+ for database storage
- **OS**: Linux (Ubuntu 20.04+, RHEL 8+, etc.) or macOS

### Remote Server Requirements

- **SSH Access**: Root or sudo access to target servers
- **OS**: Linux-based (tested on RHEL/CentOS/Ubuntu)
- **Commands**: Standard utilities (`ps`, `df`, `uptime`, `w`, etc.)

---

## 🚀 Installation

### Quick Start (5 Minutes)

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/ServerDashboardContainer.git
cd ServerDashboardContainer

# 2. Create environment configuration
cp .env.example .env
nano .env  # Edit with your server credentials

# 3. Build and start all services
make

# 4. Verify services are running
make ps

# 5. Access the dashboard
# Open your browser to http://localhost
```

### Detailed Installation Steps

#### Step 1: Clone Repository

```bash
git clone https://github.com/yourusername/ServerDashboardContainer.git
cd ServerDashboardContainer
```

#### Step 2: Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Database Configuration
POSTGRES_PASSWORD=your_secure_password_here

# Server 1 Configuration
SERVER1_NAME=Production-Server-1
SERVER1_HOST=192.168.1.10
SERVER1_USERNAME=root
SERVER1_PASSWORD=server1_ssh_password

# Server 2 Configuration
SERVER2_NAME=Development-Server
SERVER2_HOST=192.168.1.11
SERVER2_USERNAME=admin
SERVER2_PASSWORD=server2_ssh_password

# Add SERVER3-SERVER7 as needed...
```

**Security Note**: Keep your `.env` file secure and never commit it to version control.

#### Step 3: Build Docker Images

```bash
# Build all containers
make

# This will:
# - Build Python images for DataCollection, API, and Frontend
# - Pull PostgreSQL and Nginx images
# - Create Docker networks and volumes
# - Start all services in detached mode
```

#### Step 4: Verify Installation

```bash
# Check container status
make ps

# Expected output:
# NAME              STATUS              PORTS
# nginx             Up 30 seconds       0.0.0.0:80->80/tcp
# Frontend          Up 30 seconds       (healthy)
# API               Up 30 seconds       (healthy)
# DataCollection    Up 30 seconds
# postgres          Up 30 seconds       (healthy)

# Check logs for errors
make logs

# View specific service logs
make logs-Frontend
make logs-API
make logs-DataCollection
```

#### Step 5: Initial Data Collection

The DataCollection service runs every 15 minutes via cron. To trigger immediate collection:

```bash
# Run single collection cycle
make collect-once

# Check DataCollection logs
make logs-DataCollection

# You should see output like:
# INFO:__main__:Starting data collection cycle...
# INFO:__main__:Connected to Production-Server-1
# INFO:__main__:Collected metrics from 5 servers
```

#### Step 6: Access Dashboard

Open your web browser and navigate to:

```
http://localhost        # Via Nginx reverse proxy
http://localhost:3000   # Direct Frontend access (development)
```

You should see the Server Dashboard with:
- Server status cards (may show "offline" until first collection completes)
- Empty graphs (will populate after first collection)
- User activity tables

---

## ⚙ Configuration

### Environment Variables Reference

#### Database Configuration
```bash
POSTGRES_PASSWORD=secure_password     # PostgreSQL password
```

#### Server Configuration (repeat for SERVER1-SERVER7)
```bash
SERVER{N}_NAME=Display-Name           # Human-readable server name
SERVER{N}_HOST=hostname.domain.com    # Hostname or IP address
SERVER{N}_IP=192.168.1.10            # IP address (optional, used for ping checks)
SERVER{N}_USERNAME=root               # SSH username
SERVER{N}_PASSWORD=ssh_password       # SSH password
```

### Advanced Configuration

#### Collection Frequency
Edit `srcs/DataCollection/Dockerfile` to change cron schedule:

```dockerfile
# Default: Every 15 minutes
RUN echo "*/15 * * * * /usr/local/bin/python /app/backend.py >> /var/log/datacollection.log 2>&1" > /etc/cron.d/datacollection

# Change to every 5 minutes:
RUN echo "*/5 * * * * /usr/local/bin/python /app/backend.py >> /var/log/datacollection.log 2>&1" > /etc/cron.d/datacollection
```

#### Dashboard Refresh Rate
Edit `srcs/Frontend/Dash.py`:

```python
# Default: 30 seconds
DASHBOARD_CONFIG = {
    'refresh_interval': 30000,  # milliseconds
}

# Change to 60 seconds:
DASHBOARD_CONFIG = {
    'refresh_interval': 60000,
}
```

#### Data Retention
Edit `srcs/DataCollection/backend.py`:

```python
# Default: 3 months
def cleanup_old_data():
    cutoff_date = datetime.now() - timedelta(days=90)
    # ...

# Change to 6 months:
def cleanup_old_data():
    cutoff_date = datetime.now() - timedelta(days=180)
    # ...
```

---

## 💻 Usage

### Common Operations

#### Start/Stop Services

```bash
# Start all services
make up

# Stop all services
make down

# Restart all services
make restart

# Restart specific service
make restart-service SERVICE=Frontend
```

#### View Logs

```bash
# View recent logs from all services
make logs

# View logs from specific service
make logs-Frontend
make logs-API
make logs-DataCollection
make logs-db

# Follow logs in real-time
make logs-follow

# View only error logs
make logs-errors
```

#### Database Operations

```bash
# View database statistics
make db-stats

# Connect to PostgreSQL directly
psql -h localhost -U postgres -d server_db

# Useful queries:
# SELECT * FROM server_metrics ORDER BY timestamp DESC LIMIT 10;
# SELECT * FROM top_users WHERE server_name = 'Production-Server-1';
# SELECT COUNT(*) FROM server_metrics;
```

#### Maintenance

```bash
# Run data cleanup (removes data older than 3 months)
make cleanup-data

# View health status of all services
make health

# Rebuild specific service
make rebuild-service SERVICE=Frontend
```

#### Development Mode

```bash
# Run in foreground (non-detached) for debugging
make debug

# Shell into a container
make shell SERVICE=Frontend

# Run tests (Frontend)
cd srcs/Frontend
pytest -v
pytest --cov=. --cov-report=html
```

### Dashboard Usage Guide

#### Main Dashboard Tab
- **Server Status Cards**: Show current status (green=healthy, yellow=warning, red=critical, gray=offline)
- **Gauge Charts**: Visual indicators for CPU, RAM, and disk usage
- **Refresh Button**: Manually refresh data

#### Overview Tab
- **System Statistics**: Total servers, online/offline count, average CPU/RAM/disk
- **Top Servers**: Servers with highest resource usage
- **Alerts**: Servers requiring attention

#### Historical Metrics Tab
- **Server Selector**: Choose server to analyze
- **Time Range Selector**: 1 hour, 6 hours, 12 hours, 24 hours, or custom
- **Line Charts**: CPU, RAM, disk, and network trends over time

#### User Activity Tab
- **Top Users Table**: Users sorted by CPU usage
- **Filters**: Filter by server or search by username
- **Export**: Download user data as Excel file

---

## 🛠 Development

### Project Structure

```
ServerDashboardContainer/
├── docker-compose.yml              # Docker orchestration
├── Makefile                        # Convenience commands
├── .env                           # Environment configuration (not in repo)
├── README.md                      # This file
├── CLAUDE.md                      # AI assistant guide
│
├── Docs/                          # 📚 All documentation (organized)
│   ├── INDEX.md                   # Master documentation index
│   ├── Schema-System/             # Schema-driven architecture (NEW!)
│   ├── Monitoring-Analysis/       # System analysis & improvements
│   ├── Frontend-Improvements/     # Frontend refactoring docs
│   ├── Project-Overview/          # Setup & testing guides
│   └── generated/                 # Auto-generated docs from schema
│
├── schema/                        # 🚀 Schema-driven system (NEW!)
│   ├── metrics_schema.yaml        # Single source of truth
│   ├── pyproject.toml            # Schema generator dependencies
│   └── generators/                # Code generators
│       ├── generate_all.py        # Master generator
│       ├── generate_sql.py        # SQL migrations
│       ├── generate_python.py     # Python models
│       ├── generate_parsers.py    # Bash parsers
│       ├── generate_validators.py # Validators
│       ├── generate_typescript.py # TypeScript types
│       └── generate_docs.py       # Documentation
│
├── srcs/
│   ├── Nginx/
│   │   └── default.conf           # Nginx configuration
│   │
│   ├── DataCollection/
│   │   ├── Dockerfile
│   │   ├── pyproject.toml         # UV dependencies
│   │   ├── backend.py             # Main collector script
│   │   ├── BashGetInfo.sh         # SSH wrapper
│   │   ├── mini_monitering.sh     # System metrics script
│   │   ├── TopUsers.sh            # User activity script
│   │   └── generated/             # Auto-generated bash parsers
│   │
│   ├── Backend/
│   │   ├── Dockerfile
│   │   ├── pyproject.toml         # UV dependencies
│   │   ├── api.py                 # Flask REST API
│   │   ├── migrations/            # SQL migrations
│   │   └── generated/             # Auto-generated models
│   │       └── models/
│   │
│   └── Frontend/
│       ├── Dockerfile
│       ├── pyproject.toml         # UV dependencies
│       ├── Dash.py                # Main dashboard application
│       ├── api_client.py          # API wrapper with caching
│       ├── components.py          # UI components
│       ├── utils.py               # Utility functions
│       ├── callbacks.py           # Dash callbacks
│       ├── exceptions.py          # Custom exceptions
│       ├── validation.py          # Input validation
│       ├── data_processing.py     # DataFrame utilities
│       ├── toast_utils.py         # Toast notifications
│       ├── generated/             # Auto-generated validators
│       ├── assets/
│       │   └── styles.css         # External stylesheet
│       └── tests/
│           ├── conftest.py        # pytest fixtures
│           ├── test_validation.py # Validation tests
│           └── test_utils.py      # Utility tests
```

### 🚀 NEW: Schema-Driven Architecture

This project now uses a **schema-driven architecture** that dramatically simplifies adding new metrics!

#### What Is It?

Instead of manually editing 10+ files, you now edit **one YAML file** and run **one command** to generate all the code:

```yaml
# schema/metrics_schema.yaml - Single source of truth
- name: swap_percentage
  type: integer
  bash_output: true
  bash_index: 14
  description: "Swap usage percentage"
  validation:
    type: percentage
```

```bash
# Generate all code
cd schema/generators
uv run python generate_all.py
```

**Automatically generates:**
- ✅ SQL migrations
- ✅ Python dataclasses
- ✅ Bash output parsers
- ✅ Field validators
- ✅ TypeScript types
- ✅ Documentation

**Benefits:**
- **85% faster** - 15-30 minutes instead of 2-4 hours per metric
- **Zero sync bugs** - Everything generated from single source
- **Always documented** - Docs auto-update with code

**Learn more:** [Docs/Schema-System/SCHEMA_HOWTO.md](Docs/Schema-System/SCHEMA_HOWTO.md)

---

### Setting Up Development Environment

#### Prerequisites
```bash
# Install Python 3.8+
python3 --version

# Install UV (fast Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install development dependencies
uv sync  # In any service directory with pyproject.toml
```

#### Frontend Development

```bash
# Navigate to Frontend directory
cd srcs/Frontend

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest -v

# Run tests with coverage
pytest --cov=. --cov-report=html

# View coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux

# Code formatting
black *.py

# Linting
flake8 *.py --max-line-length=120
```

#### API Development

```bash
# Navigate to Backend directory
cd srcs/Backend

# Install dependencies
pip install -r requirements.txt

# Run Flask in development mode
FLASK_ENV=development python api.py

# API will be available at http://localhost:5000
```

#### Adding a New Server

1. Add configuration to `.env`:
```bash
SERVER8_NAME=New-Server
SERVER8_HOST=192.168.1.18
SERVER8_USERNAME=root
SERVER8_PASSWORD=password
```

2. Update `srcs/DataCollection/backend.py`:
```python
# Update SERVER_CONFIGS list
SERVER_CONFIGS = [
    # ... existing servers ...
    {
        'name': os.getenv('SERVER8_NAME'),
        'host': os.getenv('SERVER8_HOST'),
        'username': os.getenv('SERVER8_USERNAME'),
        'password': os.getenv('SERVER8_PASSWORD'),
    },
]
```

3. Restart services:
```bash
make restart-service SERVICE=DataCollection
```

### Code Style Guidelines

- **Python**: Follow PEP 8, use type hints, max line length 120
- **Naming**: snake_case for functions/variables, PascalCase for classes
- **Documentation**: Docstrings for all public functions
- **Error Handling**: Always handle exceptions, log errors with context
- **Testing**: Write tests for new functionality, maintain >80% coverage

---

## 🧪 Testing

### Running Tests

#### Frontend Tests (103 tests, >85% coverage)

```bash
# Navigate to Frontend directory
cd srcs/Frontend

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=. --cov-report=term-missing

# Run specific test file
pytest tests/test_validation.py

# Run specific test class
pytest tests/test_validation.py::TestValidatePercentage

# Run specific test
pytest tests/test_validation.py::TestValidatePercentage::test_valid_percentage_int

# Run and stop on first failure
pytest -x

# Run with print statements visible
pytest -s
```

#### Test Organization

- **test_validation.py** (38 tests)
  - Tests for input validation functions
  - Percentage, timestamp, server name validation
  - Edge cases and error handling

- **test_utils.py** (40+ tests)
  - Tests for utility functions
  - Status determination, uptime formatting
  - DataFrame operations

#### Test Fixtures

Available fixtures (defined in `conftest.py`):
- `sample_server_metrics` - Single server metrics
- `sample_historical_data` - Time-series data
- `multiple_servers_metrics` - Multiple servers
- `warning_server_metrics` - Triggers warnings
- `critical_server_metrics` - Triggers critical alerts

### Integration Testing

```bash
# Test API endpoints
curl http://localhost:5000/api/health
curl http://localhost:5000/api/servers/metrics/latest
curl http://localhost:5000/api/system/overview

# Test Frontend access
curl http://localhost:3000

# Test database connection
docker exec -it postgres psql -U postgres -d server_db -c "SELECT COUNT(*) FROM server_metrics;"
```

### Manual Testing Checklist

Before deploying changes, verify:

- [ ] All Docker containers are healthy: `make health`
- [ ] No errors in logs: `make logs-errors`
- [ ] Dashboard loads without errors
- [ ] All tabs are accessible
- [ ] Server status cards display correctly
- [ ] Graphs render with data
- [ ] User tables populate
- [ ] Refresh button works
- [ ] Toast notifications appear
- [ ] Export to Excel works
- [ ] API responds to all endpoints
- [ ] Data collection completes successfully

---

## 📚 API Documentation

### Base URL

```
http://localhost:5000/api
```

### Endpoints

#### Health Check
```http
GET /api/health

Response:
{
  "status": "healthy",
  "timestamp": "2025-10-01T12:00:00"
}
```

#### Get Latest Server Metrics
```http
GET /api/servers/metrics/latest

Response:
[
  {
    "server_name": "Production-Server-1",
    "cpu_load_1min": 2.5,
    "cpu_load_5min": 3.0,
    "cpu_load_15min": 2.8,
    "ram_percentage": 65.5,
    "disk_percentage": 45.2,
    "logged_users": 5,
    "tcp_connections": 120,
    "timestamp": "2025-10-01T12:00:00"
  },
  // ... more servers
]
```

#### Get Historical Metrics
```http
GET /api/servers/<server_name>/metrics/historical/<hours>

Example: GET /api/servers/Production-Server-1/metrics/historical/24

Response:
[
  {
    "timestamp": "2025-09-30T12:00:00",
    "cpu_load_5min": 3.0,
    "ram_percentage": 60.0,
    "disk_percentage": 45.0
  },
  // ... 24 hours of data
]
```

#### Get Server Status
```http
GET /api/servers/<server_name>/status

Response:
{
  "server_name": "Production-Server-1",
  "status": "healthy",
  "cpu_status": "normal",
  "ram_status": "normal",
  "disk_status": "normal",
  "last_seen": "2025-10-01T12:00:00"
}
```

#### Get Top Users
```http
GET /api/users/top

Response:
[
  {
    "username": "john_doe",
    "server_name": "Production-Server-1",
    "cpu": 45.5,
    "mem": 30.2,
    "disk": 12.0,
    "process_count": 25,
    "top_process": "python"
  },
  // ... more users
]
```

#### Get System Overview
```http
GET /api/system/overview

Response:
{
  "total_servers": 7,
  "online_servers": 6,
  "offline_servers": 1,
  "avg_cpu": 3.5,
  "avg_ram": 65.0,
  "avg_disk": 50.0,
  "total_users": 45,
  "alerts": [
    {
      "server": "Production-Server-2",
      "type": "warning",
      "message": "High RAM usage: 90%"
    }
  ]
}
```

### Error Responses

All endpoints return errors in this format:

```json
{
  "success": false,
  "error": "Error message here",
  "details": {
    "code": "API_ERROR",
    "timestamp": "2025-10-01T12:00:00"
  }
}
```

Common HTTP Status Codes:
- `200` - Success
- `400` - Bad Request (invalid parameters)
- `404` - Not Found (server doesn't exist)
- `500` - Internal Server Error

---

## 📚 Documentation

All project documentation has been organized into the `Docs/` folder for easy navigation.

### 📖 Documentation Structure

```
Docs/
├── INDEX.md                    # ⭐ START HERE - Master index
├── Schema-System/              # Schema-driven architecture
│   ├── SCHEMA_HOWTO.md        # Daily usage guide
│   ├── SCHEMA_REFACTORING_SUMMARY.md
│   ├── SCHEMA_DRIVEN_REFACTORING_PLAN.md
│   └── SCHEMA_MIGRATION_GUIDE.md
├── Monitoring-Analysis/        # System analysis & improvements
├── Frontend-Improvements/      # Frontend refactoring docs
├── Project-Overview/           # Setup & testing guides
└── generated/                  # Auto-generated from schema
```

### 🎯 Quick Links by Task

| Task | Document |
|------|----------|
| **Add a new metric** | [Schema-System/SCHEMA_HOWTO.md](Docs/Schema-System/SCHEMA_HOWTO.md) |
| **Understand architecture** | [Monitoring-Analysis/ARCHITECTURE_VISUAL.md](Docs/Monitoring-Analysis/ARCHITECTURE_VISUAL.md) |
| **Quick commands** | [Project-Overview/QUICK_REFERENCE.md](Docs/Project-Overview/QUICK_REFERENCE.md) |
| **Test before deployment** | [Project-Overview/TESTING_CHECKLIST.md](Docs/Project-Overview/TESTING_CHECKLIST.md) |
| **Check API endpoints** | [generated/API_DOCUMENTATION.md](Docs/generated/API_DOCUMENTATION.md) |

**Full documentation index:** [Docs/INDEX.md](Docs/INDEX.md)

---

## 🤝 Contributing

We welcome contributions! Here's how to get started:

### Getting Started

1. **Fork the Repository**
   ```bash
   # Click "Fork" on GitHub, then clone your fork
   git clone https://github.com/YOUR_USERNAME/ServerDashboardContainer.git
   cd ServerDashboardContainer
   ```

2. **Create a Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Set Up Development Environment**
   ```bash
   # Create .env file
   cp .env.example .env
   # Edit with your test server credentials

   # Build and start services
   make build
   ```

### Development Workflow

1. **Make Your Changes**
   - Write clean, documented code
   - Follow existing code style
   - Add type hints to Python functions
   - Update relevant documentation

2. **Write Tests**
   ```bash
   cd srcs/Frontend
   # Add tests to tests/ directory
   pytest tests/test_your_feature.py -v
   ```

3. **Test Your Changes**
   ```bash
   # Run test suite
   make test

   # Check logs for errors
   make logs-errors

   # Verify services are healthy
   make health

   # Test manually in browser
   open http://localhost:3000
   ```

4. **Commit Your Changes**
   ```bash
   git add .
   git commit -m "feat: Add feature description

   - Detailed change 1
   - Detailed change 2
   - Fixes #123"
   ```

5. **Push and Create Pull Request**
   ```bash
   git push origin feature/your-feature-name
   # Open pull request on GitHub
   ```

### Contribution Guidelines

#### Code Standards

- **Python Code**:
  - Use type hints for function parameters and returns
  - Handle errors gracefully with try-except blocks

- **Documentation**:
  - Update README.md if adding new features
  - Add inline comments for complex logic
  - Update API documentation for new endpoints
  - Include examples in docstrings

- **Testing**:
  - Write unit tests for new functions
  - Test both success and failure cases
  - Use pytest fixtures for test data

#### Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples**:
```bash
feat(frontend): Add dark mode toggle to dashboard

- Implemented theme switcher component
- Added CSS variables for color themes
- Persists user preference in localStorage

Closes #42

---

fix(api): Resolve race condition in cache invalidation

The cache was not properly invalidating when multiple
requests arrived simultaneously. Added mutex lock.

Fixes #87
```

### Areas We Need Help

#### High Priority
- [ ] **Docker Hub Images** - Create official Docker images for easier deployment
- [ ] **Email Alerts** - Send email notifications for critical server issues
- [ ] **HTTPS Support** - Add SSL/TLS configuration for Nginx


#### Medium Priority
- [ ] **Data Export API** - Add CSV/JSON export endpoints
- [ ] **Server Groups** - Organize servers into logical groups

#### Low Priority
- [ ] **Dark Mode** - Add dark theme to dashboard
- [ ] **Custom Alerts** - User-defined alert thresholds

### Pull Request Process

1. **Ensure Tests Pass**
   - All existing tests must pass
   - New features must include tests
   - Coverage should not decrease

2. **Update Documentation**
   - Update README.md if needed
   - Update API docs for new endpoints
   - Add inline code comments

3. **Code Review**
   - At least one maintainer approval required
   - Address all review comments
   - Keep PR scope focused

4. **Merge**
   - Squash commits before merging
   - Use descriptive merge commit message
   - Delete branch after merge

### Reporting Issues

When reporting bugs, please include:

- **Environment**: OS, Docker version, Browser (if UI issue)
- **Steps to Reproduce**: Detailed steps to trigger the bug
- **Expected Behavior**: What should happen
- **Actual Behavior**: What actually happens
- **Logs**: Relevant error messages from `make logs`
- **Screenshots**: If applicable

**Template**:
```markdown
## Bug Description
Brief description of the issue

## Environment
- OS: Ubuntu 22.04
- Docker: 24.0.5
- Browser: Chrome 118

## Steps to Reproduce
1. Start services with `make up`
2. Navigate to http://localhost:3000
3. Click on "Historical Metrics" tab
4. Select server "Production-1"

## Expected Behavior
Historical graphs should display

## Actual Behavior
Page shows "No data available" error

## Logs
```
[paste relevant logs here]
```

## Screenshots
[attach screenshots]
```

---

## 🐛 Troubleshooting

### Common Issues

#### Services Won't Start

**Symptom**: `make up` fails or containers exit immediately

**Solutions**:
```bash
# Check Docker daemon is running
sudo systemctl status docker

# Check for port conflicts
sudo netstat -tulpn | grep -E ':(80|3000|5000|5432)'

# View detailed error logs
make logs-all

# Completely rebuild
make cclean
make build
```

#### Database Connection Errors

**Symptom**: "could not connect to server" or "psycopg2.OperationalError"

**Solutions**:
```bash
# Check PostgreSQL is healthy
docker ps | grep postgres

# Check database logs
make logs-db

# Restart database
make restart-service SERVICE=postgres

# Verify credentials in .env
cat .env | grep POSTGRES_PASSWORD
```

#### SSH Connection Failures

**Symptom**: "SSH connection failed" in DataCollection logs

**Solutions**:
```bash
# Test SSH manually
ssh username@hostname

# Check credentials in .env
cat .env | grep SERVER1

# Check SSH is enabled on target server
# Verify firewall allows SSH (port 22)

# Check DataCollection logs for details
make logs-DataCollection
```

#### Dashboard Shows No Data

**Symptom**: Empty graphs and tables in dashboard

**Solutions**:
```bash
# Trigger immediate data collection
make collect-once

# Check if data exists in database
make db-stats

# Check API is responding
curl http://localhost:5000/api/servers/metrics/latest

# Clear cache and refresh
# Click "Refresh Data" button in dashboard
```

#### High Memory Usage

**Symptom**: System slowdown, containers being killed

**Solutions**:
```bash
# Check memory usage
docker stats

# Limit PostgreSQL memory in docker-compose.yml:
services:
  postgres:
    deploy:
      resources:
        limits:
          memory: 1G
```

#### Tests Failing

**Symptom**: pytest errors when running tests

**Solutions**:
```bash
# Clear pytest cache
cd srcs/Frontend
pytest --cache-clear

# Ensure running from correct directory
pwd  # Should be .../srcs/Frontend

# Check Python path
export PYTHONPATH=$(pwd):$PYTHONPATH

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Run with verbose output to see details
pytest -vv -s
```

### Getting Help

If you're stuck:

1. **Check Documentation**
   - Read relevant sections in this README
   - Check CLAUDE.md for developer guidance

2. **Search Issues**
   - GitHub Issues: Search for similar problems
   - Stack Overflow: Search for error messages

3. **Ask for Help**
   - Open a GitHub Issue with details
   - Include logs, environment info, and steps to reproduce

4. **Logs to Provide**
   ```bash
   # Capture all logs
   make logs-all > full_logs.txt

   # Capture error logs
   make logs-errors > error_logs.txt

   # Capture system info
   docker --version > system_info.txt
   docker compose version >> system_info.txt
   uname -a >> system_info.txt
   ```

---

## 📄 License

This project is licensed under the **MIT License**

### MIT License Summary

- ✅ Commercial use
- ✅ Modification
- ✅ Distribution
- ✅ Private use
- ❌ Liability
- ❌ Warranty



