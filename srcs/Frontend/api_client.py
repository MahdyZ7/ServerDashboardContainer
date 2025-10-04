# API client functions for the Server Monitoring Dashboard
import requests
import logging
import time
from typing import Optional, Dict, List, Any, Tuple
from config import API_BASE_URL
from exceptions import (
    APIConnectionError, APITimeoutError, APIResponseError,
    APIDataError
)
from cache_utils import cached, get_cache

# Configure logging with more detail
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
DEFAULT_TIMEOUT = 10
MAX_RETRIES = 3
RETRY_BACKOFF_FACTOR = 2
CACHE_TTL = 900  # 15 minutes


class APIResult:
    """Wrapper for API results with success/error information"""

    def __init__(self, success: bool, data: Any = None, error: Optional[Exception] = None):
        self.success = success
        self.data = data
        self.error = error

    def get_data_or_default(self, default: Any = None) -> Any:
        """Get data if successful, otherwise return default"""
        return self.data if self.success else default

    def __bool__(self):
        return self.success


def retry_on_failure(max_retries: int = MAX_RETRIES, backoff_factor: float = RETRY_BACKOFF_FACTOR):
    """
    Decorator to retry API calls on failure with exponential backoff

    Args:
        max_retries: Maximum number of retry attempts
        backoff_factor: Multiplier for exponential backoff
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (APIConnectionError, APITimeoutError) as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        wait_time = backoff_factor ** attempt
                        logger.warning(
                            f"API call failed (attempt {attempt + 1}/{max_retries}): {e}. "
                            f"Retrying in {wait_time}s..."
                        )
                        time.sleep(wait_time)
                    else:
                        logger.error(
                            f"API call failed after {max_retries} attempts: {e}"
                        )
                except Exception as e:
                    # Don't retry on other exceptions
                    logger.error(f"API call failed with non-retryable error: {e}")
                    raise

            # If we get here, all retries failed
            if last_exception:
                raise last_exception

        return wrapper
    return decorator


def _make_api_request(
    endpoint: str,
    timeout: int = DEFAULT_TIMEOUT,
    params: Optional[Dict] = None
) -> Tuple[bool, Any, Optional[Exception]]:
    """
    Make an API request with proper error handling

    Args:
        endpoint: API endpoint (relative to base URL)
        timeout: Request timeout in seconds
        params: Optional query parameters

    Returns:
        Tuple of (success, data, error)
    """
    url = f"{API_BASE_URL}{endpoint}"

    try:
        logger.debug(f"Making API request to {url}")
        response = requests.get(url, timeout=timeout, params=params)

        # Check HTTP status
        if response.status_code == 200:
            try:
                data = response.json()

                # Validate response structure
                if not isinstance(data, dict):
                    error = APIDataError(
                        "API response is not a dictionary",
                        details={'response': str(data)[:200]}
                    )
                    logger.error(f"Invalid response structure from {url}: {error}")
                    return False, None, error

                # Check if API indicates success
                if data.get('success'):
                    logger.debug(f"API request successful: {url}")
                    return True, data.get('data'), None
                else:
                    error = APIResponseError(
                        f"API returned success=false: {data.get('message', 'Unknown error')}",
                        status_code=200,
                        details={'response': data}
                    )
                    logger.warning(f"API returned error: {error}")
                    return False, None, error

            except ValueError as e:
                error = APIDataError(
                    "Failed to parse JSON response",
                    details={'error': str(e), 'response': response.text[:200]}
                )
                logger.error(f"JSON parse error from {url}: {error}")
                return False, None, error

        elif response.status_code == 404:
            error = APIResponseError(
                f"API endpoint not found: {endpoint}",
                status_code=404
            )
            logger.error(f"404 error from {url}: {error}")
            return False, None, error

        elif response.status_code >= 500:
            error = APIResponseError(
                f"Server error: {response.status_code}",
                status_code=response.status_code,
                details={'response': response.text[:200]}
            )
            logger.error(f"Server error from {url}: {error}")
            return False, None, error

        else:
            error = APIResponseError(
                f"HTTP error: {response.status_code}",
                status_code=response.status_code,
                details={'response': response.text[:200]}
            )
            logger.error(f"HTTP error from {url}: {error}")
            return False, None, error

    except requests.exceptions.Timeout as e:
        error = APITimeoutError(
            f"Request timed out after {timeout}s",
            details={'endpoint': endpoint, 'timeout': timeout}
        )
        logger.error(f"Timeout error for {url}: {error}")
        return False, None, error

    except requests.exceptions.ConnectionError as e:
        error = APIConnectionError(
            "Failed to connect to API",
            details={'endpoint': endpoint, 'error': str(e)}
        )
        logger.error(f"Connection error for {url}: {error}")
        return False, None, error

    except Exception as e:
        error = APIConnectionError(
            f"Unexpected error: {str(e)}",
            details={'endpoint': endpoint, 'error_type': type(e).__name__}
        )
        logger.error(f"Unexpected error for {url}: {error}", exc_info=True)
        return False, None, error


@retry_on_failure()
@cached(ttl_seconds=CACHE_TTL, key_prefix="server_metrics_")
def get_latest_server_metrics() -> List[Dict]:
    """
    Fetch latest server metrics from API

    Returns:
        List of server metrics dictionaries, empty list on error
    """
    success, data, error = _make_api_request("/servers/metrics/latest")

    if success and isinstance(data, list):
        logger.info(f"Fetched {len(data)} server metrics")
        return data
    else:
        logger.warning(f"Failed to fetch server metrics: {error}")
        return []


@retry_on_failure()
@cached(ttl_seconds=CACHE_TTL, key_prefix="top_users_")
def get_top_users() -> List[Dict]:
    """
    Fetch top users data from API

    Returns:
        List of user data dictionaries, empty list on error
    """
    success, data, error = _make_api_request("/users/top")

    if success and isinstance(data, list):
        logger.info(f"Fetched {len(data)} top users")
        return data
    else:
        logger.warning(f"Failed to fetch top users: {error}")
        return []


@retry_on_failure()
@cached(ttl_seconds=CACHE_TTL, key_prefix="historical_")
def get_historical_metrics(server_name: str, hours: int = 24) -> List[Dict]:
    """
    Fetch historical metrics for a specific server

    Args:
        server_name: Name of the server
        hours: Number of hours of historical data to fetch

    Returns:
        List of historical metrics, empty list on error
    """
    if not server_name or not isinstance(server_name, str):
        logger.error(f"Invalid server_name parameter: {server_name}")
        return []

    if not isinstance(hours, int) or hours <= 0:
        logger.error(f"Invalid hours parameter: {hours}")
        return []

    success, data, error = _make_api_request(
        f"/servers/{server_name}/metrics/historical/{hours}"
    )

    if success and isinstance(data, list):
        logger.info(f"Fetched {len(data)} historical metrics for {server_name}")
        return data
    else:
        logger.warning(f"Failed to fetch historical metrics for {server_name}: {error}")
        return []


@retry_on_failure()
@cached(ttl_seconds=CACHE_TTL, key_prefix="server_status_")
def get_server_status(server_name: str) -> Dict:
    """
    Fetch status for a specific server

    Args:
        server_name: Name of the server

    Returns:
        Server status dictionary, empty dict on error
    """
    if not server_name or not isinstance(server_name, str):
        logger.error(f"Invalid server_name parameter: {server_name}")
        return {}

    success, data, error = _make_api_request(f"/servers/{server_name}/status")

    if success and isinstance(data, dict):
        logger.info(f"Fetched status for {server_name}")
        return data
    else:
        logger.warning(f"Failed to fetch server status for {server_name}: {error}")
        return {}


@retry_on_failure()
@cached(ttl_seconds=CACHE_TTL, key_prefix="server_health_")
def get_server_health(server_name: str) -> Dict:
    """
    Fetch server health for a specific server

    Args:
        server_name: Name of the server

    Returns:
        Server health dictionary, empty dict on error
    """
    if not server_name or not isinstance(server_name, str):
        logger.error(f"Invalid server_name parameter: {server_name}")
        return {}

    success, data, error = _make_api_request(f"/health/{server_name}")

    if success and isinstance(data, dict):
        logger.info(f"Fetched health for {server_name}")
        return data
    else:
        logger.warning(f"Failed to fetch server health for {server_name}: {error}")
        return {}


@retry_on_failure()
@cached(ttl_seconds=CACHE_TTL, key_prefix="server_list_")
def get_server_list() -> List[str]:
    """
    Fetch list of all available servers

    Returns:
        List of server names, empty list on error
    """
    success, data, error = _make_api_request("/servers/list")

    if success and isinstance(data, list):
        logger.info(f"Fetched {len(data)} servers")
        return data
    else:
        logger.warning(f"Failed to fetch server list: {error}")
        return []


@retry_on_failure()
@cached(ttl_seconds=CACHE_TTL, key_prefix="top_users_server_")
def get_top_users_by_server(server_name: str) -> List[Dict]:
    """
    Fetch top users for a specific server

    Args:
        server_name: Name of the server

    Returns:
        List of user data dictionaries, empty list on error
    """
    if not server_name or not isinstance(server_name, str):
        logger.error(f"Invalid server_name parameter: {server_name}")
        return []

    success, data, error = _make_api_request(f"/users/top/{server_name}")

    if success and isinstance(data, list):
        logger.info(f"Fetched {len(data)} top users for {server_name}")
        return data
    else:
        logger.warning(f"Failed to fetch top users for {server_name}: {error}")
        return []


@retry_on_failure()
@cached(ttl_seconds=CACHE_TTL, key_prefix="system_overview_")
def get_system_overview() -> Dict:
    """
    Fetch system overview data

    Returns:
        System overview dictionary, empty dict on error
    """
    success, data, error = _make_api_request("/system/overview")

    if success and isinstance(data, dict):
        logger.info("Fetched system overview")
        return data
    else:
        logger.warning(f"Failed to fetch system overview: {error}")
        return {}


@retry_on_failure(max_retries=2)
def check_api_health() -> bool:
    """
    Check API health status

    Returns:
        True if API is healthy, False otherwise
    """
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            is_healthy = data.get('status') == 'healthy'
            logger.info(f"API health check: {'healthy' if is_healthy else 'unhealthy'}")
            return is_healthy
        else:
            logger.warning(f"API health check failed with status: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"API health check failed: {e}")
        return False


def invalidate_all_caches():
    """Invalidate all API caches (called on manual refresh)"""
    cache = get_cache()
    cache.clear()
    logger.info("All API caches invalidated")


def get_cache_stats() -> Dict:
    """Get statistics about API cache performance"""
    cache = get_cache()
    return cache.get_stats()
