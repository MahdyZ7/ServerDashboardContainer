# Refresh utility functions for the Server Monitoring Dashboard
from datetime import datetime
import logging
from typing import Dict
from api_client import check_api_health, invalidate_all_caches, get_cache_stats

logger = logging.getLogger(__name__)


def trigger_dashboard_refresh() -> Dict:
    """
    Trigger a manual refresh of all dashboard data

    This function invalidates all caches and checks API health.

    Returns:
        Dictionary with refresh status and timestamp
    """
    try:
        # Invalidate all caches first
        invalidate_all_caches()
        logger.info("Invalidated all caches for manual refresh")

        # Check API health before refreshing
        api_healthy = check_api_health()

        if not api_healthy:
            logger.warning("API health check failed during refresh")
            return {
                'success': False,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'message': 'API is not responding. Please check the backend service.'
            }

        # Get cache statistics
        cache_stats = get_cache_stats()

        # Return success with timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logger.info(f"Dashboard refresh triggered at {timestamp}")

        return {
            'success': True,
            'timestamp': timestamp,
            'message': f'Dashboard refreshed successfully at {timestamp}',
            'cache_stats': cache_stats
        }

    except Exception as e:
        logger.error(f"Error during dashboard refresh: {e}", exc_info=True)
        return {
            'success': False,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'message': f'Refresh failed: {str(e)}'
        }


def get_refresh_status_message(refresh_result):
    """
    Generate a user-friendly status message for the refresh operation

    Args:
        refresh_result: Dictionary returned by trigger_dashboard_refresh()

    Returns:
        String message for display
    """
    if refresh_result.get('success'):
        return f"✓ Last updated: {refresh_result.get('timestamp')}"
    else:
        return f"⚠ Update failed: {refresh_result.get('message', 'Unknown error')}"


def validate_refresh_interval(n_intervals):
    """
    Validate that the automatic refresh interval is working correctly

    Args:
        n_intervals: Number of intervals passed from dcc.Interval

    Returns:
        Boolean indicating if refresh should proceed
    """
    try:
        # Always allow refresh
        return True
    except Exception as e:
        logging.error(f"Error validating refresh interval: {e}")
        return False
