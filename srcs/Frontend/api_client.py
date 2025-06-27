# API client functions for the Server Monitoring Dashboard
import requests
import logging
from config import API_BASE_URL

# Configure logging
logging.basicConfig(level=logging.INFO)

def get_latest_server_metrics():
    """Fetch latest server metrics from API"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/servers/metrics/latest", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                return data.get('data', [])
        return []
    except Exception as e:
        logging.error(f"API error fetching server metrics: {e}")
        return []


def get_top_users():
    """Fetch top users data from API"""
    try:
        response = requests.get(f"{API_BASE_URL}/users/top", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                return data.get('data', [])
        return []
    except Exception as e:
        logging.error(f"API error fetching top users: {e}")
        return []


def get_historical_metrics(server_name, hours=24):
    """Fetch historical metrics for a specific server"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/servers/{server_name}/metrics/historical/{hours}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                return data.get('data', [])
        return []
    except Exception as e:
        logging.error(
            f"API error fetching historical metrics for {server_name}: {e}")
        return []


def get_server_status(server_name):
    """Fetch status for a specific server"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/servers/{server_name}/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                return data.get('data', {})
        return {}
    except Exception as e:
        logging.error(f"API error fetching server status for {server_name}: {e}")
        return {}


def get_server_list():
    """Fetch list of all available servers"""
    try:
        response = requests.get(f"{API_BASE_URL}/servers/list", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                return data.get('data', [])
        return []
    except Exception as e:
        logging.error(f"API error fetching server list: {e}")
        return []


def get_top_users_by_server(server_name):
    """Fetch top users for a specific server"""
    try:
        response = requests.get(f"{API_BASE_URL}/users/top/{server_name}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                return data.get('data', [])
        return []
    except Exception as e:
        logging.error(f"API error fetching top users for {server_name}: {e}")
        return []


def get_system_overview():
    """Fetch system overview data"""
    try:
        response = requests.get(f"{API_BASE_URL}/system/overview", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                return data.get('data', {})
        return {}
    except Exception as e:
        logging.error(f"API error fetching system overview: {e}")
        return {}


def check_api_health():
    """Check API health status"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get('status') == 'healthy'
        return False
    except Exception as e:
        logging.error(f"API health check failed: {e}")
        return False