# Pytest configuration and fixtures
import pytest
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def sample_server_metrics():
    """Fixture providing sample server metrics data"""
    return {
        "server_name": "TestServer1",
        "cpu_load_1min": 2.5,
        "cpu_load_5min": 3.0,
        "cpu_load_15min": 2.8,
        "ram_percentage": 65.5,
        "disk_percentage": 45.2,
        "logged_users": 5,
        "tcp_connections": 120,
        "physical_cpus": 8,
        "virtual_cpus": 16,
        "ram_total": "64GB",
        "ram_used": "42GB",
        "disk_total": "1TB",
        "disk_used": "452GB",
        "operating_system": "Linux 5.14",
        "last_boot": (datetime.now() - timedelta(days=30)).isoformat(),
        "timestamp": datetime.now().isoformat(),
        "active_ssh_users": 3,
        "active_vnc_users": 2,
    }


@pytest.fixture
def sample_historical_data():
    """Fixture providing sample historical metrics"""
    base_time = datetime.now() - timedelta(hours=24)
    data = []

    for i in range(24):
        timestamp = base_time + timedelta(hours=i)
        data.append(
            {
                "server_name": "TestServer1",
                "cpu_load_1min": 2.0 + (i % 5),
                "cpu_load_5min": 2.5 + (i % 5),
                "cpu_load_15min": 3.0 + (i % 5),
                "ram_percentage": 50 + (i % 20),
                "disk_percentage": 40 + (i % 10),
                "logged_users": 3 + (i % 3),
                "tcp_connections": 100 + (i % 50),
                "timestamp": timestamp.isoformat(),
            }
        )

    return data


@pytest.fixture
def sample_user_data():
    """Fixture providing sample user activity data"""
    return [
        {
            "username": "user1",
            "server_name": "TestServer1",
            "cpu": 25.5,
            "mem": 15.2,
            "disk": 5.0,
            "process_count": 12,
            "top_process": "python",
            "last_login": datetime.now().isoformat(),
            "full_name": "Test User 1",
        },
        {
            "username": "user2",
            "server_name": "TestServer1",
            "cpu": 60.0,
            "mem": 45.0,
            "disk": 12.5,
            "process_count": 25,
            "top_process": "matlab",
            "last_login": (datetime.now() - timedelta(hours=2)).isoformat(),
            "full_name": "Test User 2",
        },
        {
            "username": "user3",
            "server_name": "TestServer2",
            "cpu": 10.0,
            "mem": 8.0,
            "disk": 2.0,
            "process_count": 5,
            "top_process": "bash",
            "last_login": (datetime.now() - timedelta(days=1)).isoformat(),
            "full_name": "Test User 3",
        },
    ]


@pytest.fixture
def empty_metrics():
    """Fixture providing empty metrics"""
    return {}


@pytest.fixture
def multiple_servers_metrics(sample_server_metrics):
    """Fixture providing metrics for multiple servers"""
    servers = []
    for i in range(1, 6):
        server = sample_server_metrics.copy()
        server["server_name"] = f"Server{i}"
        server["cpu_load_5min"] = 2.0 + i
        server["ram_percentage"] = 50 + (i * 5)
        server["disk_percentage"] = 40 + (i * 3)
        servers.append(server)
    return servers


@pytest.fixture
def warning_server_metrics(sample_server_metrics):
    """Fixture providing metrics that should trigger warnings"""
    metrics = sample_server_metrics.copy()
    metrics["ram_percentage"] = 90  # High RAM
    metrics["cpu_load_5min"] = 7.0  # High CPU
    return metrics


@pytest.fixture
def critical_server_metrics(sample_server_metrics):
    """Fixture providing metrics that should trigger critical alerts"""
    metrics = sample_server_metrics.copy()
    metrics["ram_percentage"] = 97  # Critical RAM
    metrics["disk_percentage"] = 96  # Critical disk
    metrics["cpu_load_5min"] = 9.0  # Critical CPU
    return metrics


@pytest.fixture
def offline_server_metrics(sample_server_metrics):
    """Fixture providing metrics for an offline server"""
    metrics = sample_server_metrics.copy()
    # Old timestamp indicating server is offline
    metrics["timestamp"] = (datetime.now() - timedelta(hours=2)).isoformat()
    return metrics


@pytest.fixture
def mock_api_response_success():
    """Fixture for successful API response structure"""
    return {"success": True, "data": [], "message": "Success"}


@pytest.fixture
def mock_api_response_error():
    """Fixture for error API response structure"""
    return {"success": False, "data": None, "message": "Error occurred"}


# Markers for test categorization
def pytest_configure(config):
    """Configure custom markers"""
    config.addinivalue_line(
        "markers", "unit: Unit tests that don't require external dependencies"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests that may require API/database"
    )
    config.addinivalue_line("markers", "slow: Tests that take longer than 1 second")
