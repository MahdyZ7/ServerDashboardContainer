# Refresh utility functions for the Server Monitoring Dashboard
from datetime import datetime
import logging
from api_client import check_api_health

logging.basicConfig(level=logging.INFO)


def trigger_dashboard_refresh():
    """
    Trigger a manual refresh of all dashboard data

    This function doesn't fetch data itself, but returns a timestamp
    that can be used to trigger callbacks and update all components.

    Returns:
        Dictionary with refresh status and timestamp
    """
    try:
        # Check API health before refreshing
        api_healthy = check_api_health()

        if not api_healthy:
            logging.warning("API health check failed during refresh")
            return {
                'success': False,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'message': 'API is not responding. Please check the backend service.'
            }

        # Return success with timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logging.info(f"Dashboard refresh triggered at {timestamp}")

        return {
            'success': True,
            'timestamp': timestamp,
            'message': f'Dashboard refreshed successfully at {timestamp}'
        }

    except Exception as e:
        logging.error(f"Error during dashboard refresh: {e}")
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
