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

## Frontend Architecture (Recent Major Refactoring)

The Frontend has been significantly refactored with a modular architecture and comprehensive error handling:

### Core Modules
- **`exceptions.py`** - Custom exception hierarchy for typed error handling
- **`validation.py`** - Input validation utilities with type checking
- **`data_processing.py`** - Safe DataFrame operations with automatic error handling
- **`toast_utils.py`** - Toast notification system for user feedback
- **`api_client.py`** - Enhanced API client with retry logic (3 attempts, exponential backoff) and automatic caching
- **`callbacks.py`** / **`callbacks_enhanced.py`** - Dash callbacks with error handling and toast notifications
- **`components.py`** - UI component generators with safe data processing
- **`utils.py`** - Utility functions with validation and error handling

### Frontend Development Patterns

**Input Validation:**
```python
from validation import validate_percentage, validate_server_name, validate_timestamp

# Always validate user inputs
cpu = validate_percentage(user_input, 'cpu_usage')  # Ensures 0-100
server = validate_server_name(server_input)  # Sanitizes and validates
timestamp = validate_timestamp(time_string)  # Handles multiple formats
```

**Safe DataFrame Operations:**
```python
from data_processing import safe_create_dataframe, prepare_historical_dataframe

# Use safe utilities instead of raw pandas
df = safe_create_dataframe(data, name="metrics")  # Returns empty df on error
df = prepare_historical_dataframe(data, "Server1")  # Complete validation pipeline
```

**Error Handling:**
```python
from toast_utils import create_success_toast, create_error_toast
from exceptions import APIConnectionError, ValidationError

# Wrap risky operations
try:
    result = risky_operation()
    return result, create_success_toast("Operation successful!")
except APIConnectionError as e:
    logger.error(f"API error: {e}", exc_info=True)
    return None, create_error_toast("Failed to connect to server")
```

### CSS and Assets
- External CSS in `assets/styles.css` (550+ lines, KU brand compliant)
- Images in `assets/` directory (e.g., `KU_logo.png`)
- Dash automatically serves files from `assets/` folder

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

# View logs for specific service
make logs-db          # PostgreSQL logs
make logs-DataCollection  # DataCollection service logs
make logs-Frontend    # Dashboard logs

# Follow logs in real-time
make logs-follow

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

### Frontend Testing
```bash
cd srcs/Frontend

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=. --cov-report=html --cov-report=term-missing

# Run specific test file
pytest tests/test_validation.py

# Run specific test
pytest tests/test_validation.py::TestValidatePercentage::test_valid_percentage_int

# Run only unit tests
pytest -m unit

# Stop on first failure
pytest -x
```

### Dependency Management (UV Package Manager)

This project uses **UV** (https://docs.astral.sh/uv/), a fast Python package manager, instead of pip.

**Key Benefits:**
- 10-100x faster than pip
- Reproducible builds with uv.lock files
- Better caching and dependency resolution

**Managing Dependencies:**
```bash
# Install dependencies (creates virtual environment)
cd srcs/Backend  # or Frontend or DataCollection
uv sync

# Add a new dependency
uv add requests

# Remove a dependency
uv remove requests

# Update dependencies
uv lock --upgrade

# Run Python scripts with UV
uv run api.py
```

**Project Structure:**
- `pyproject.toml` - Dependency specifications
- `uv.lock` - Locked versions for reproducible builds
- `requirements.txt` - DEPRECATED (kept for reference only)

**Docker Integration:**
All Dockerfiles use UV for dependency installation:
```dockerfile
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen
```

**Test Infrastructure:**
- 103 unit tests across `test_validation.py`, `test_utils.py`
- Fixtures in `tests/conftest.py` (sample data)
- Target: >80% coverage on core modules (currently >85%)

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

### Frontend Configuration
Edit `srcs/Frontend/config.py`:
- `CACHE_TTL`: Cache time-to-live (default 900s)
- `MAX_RETRIES`: API retry attempts (default 3)
- `DEFAULT_TIMEOUT`: API timeout (default 10s)
- `PERFORMANCE_THRESHOLDS`: Alert thresholds for CPU/RAM/disk
- `KU_COLORS`: Khalifa University brand colors

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

## Common Development Tasks

### Adding a New Frontend Component
1. Create component function in `components.py`
2. Add error handling using try-catch
3. Use `safe_create_dataframe()` for DataFrame operations
4. Validate all inputs using functions from `validation.py`
5. Add component to layout in `Dash.py`
6. Register callback in `callbacks.py` with toast notifications
7. Write unit tests in `tests/test_components.py`

### Adding a New API Endpoint
1. Define route in `srcs/Backend/api.py`
2. Add database query function
3. Format response as `{'success': bool, 'data': ..., 'message': str}`
4. Add corresponding function in `srcs/Frontend/api_client.py`
5. Add validation for inputs

# Check API response times in logs
# Look for: "API request successful" with timing info
```

## Important Files

### Documentation
- `FRONTEND_IMPROVEMENT_PLAN.md` - Comprehensive improvement roadmap
- `FRONTEND_IMPROVEMENTS_SUMMARY.md` - Implementation details and metrics
- `README_IMPROVEMENTS.md` - Developer guide with code examples
- `TESTING_CHECKLIST.md` - Pre-deployment testing procedures
- `QUICK_REFERENCE.md` - Quick commands and tips
- `tests/README.md` - Testing guide

### Frontend Key Files
- `Dash.py` - Main application (refactored with external CSS)
- `callbacks.py` - Dash callbacks (standard version)
- `callbacks_enhanced.py` - Enhanced callbacks with toast notifications
- `config.py` - All configuration constants
- `assets/styles.css` - External stylesheet (550+ lines)

## Code Quality Standards

### Error Handling
- All API calls wrapped with retry logic (automatic in `api_client.py`)
- All user-facing operations show toast notifications on success/failure
- All exceptions logged with context using `logger.error(..., exc_info=True)`
- Never return `None` - return empty list/dict on errors

### Validation
- All user inputs validated using `validation.py` functions
- All API responses validated for structure
- All numeric values checked for valid ranges
- All server names sanitized before use

### Testing
- Write unit tests for all new utility functions
- Use fixtures from `conftest.py` for test data
- Aim for >80% coverage on new code
- Run `pytest` before committing

### Performance
- Use `safe_create_dataframe()` to avoid memory leaks

## Troubleshooting

### Frontend not loading
```bash
# Check if service is running
docker ps | grep Frontend

# Check logs for errors
make logs-Frontend

# Restart service
make restart-service SERVICE=Frontend
```

### Import errors in tests
Tests must be run from `srcs/Frontend` directory. The `conftest.py` handles path setup automatically.

## Development Notes

- Services communicate via Docker network `backend`
- API backend served on `localhost:5000`
- Frontend served on `localhost:3000`
- Database persisted in Docker volume `postgres_data`
- Source code mounted as volumes for live development
- Frontend uses API endpoints (never direct database connections)
- All containers configured with `init: true` for proper signal handling
- Auto-refresh interval: 15 minutes (configurable in `config.py`)
