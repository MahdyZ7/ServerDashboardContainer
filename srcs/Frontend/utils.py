# Utility functions for the Server Monitoring Dashboard
from datetime import datetime, timedelta
from typing import Any
import logging
from config import PERFORMANCE_THRESHOLDS, STATUS_CONFIG, KU_COLORS
from validation import validate_timestamp

logger = logging.getLogger(__name__)


def safe_float(val: Any, default: float = 0.0) -> float:
    """
    Safely convert value to float, return default if conversion fails

    Args:
        val: Value to convert
        default: Default value to return on failure

    Returns:
        Float value or default
    """
    try:
        return float(val)
    except (ValueError, TypeError, AttributeError):
        if val is not None:
            logger.debug(f"Failed to convert {val} to float, using default {default}")
        return default


def determine_server_status(metrics: dict) -> str:
    """
    Determine server status based on metrics

    Args:
        metrics: Server metrics dictionary

    Returns:
        Status string: 'online', 'warning', or 'offline'
    """
    if not metrics or not isinstance(metrics, dict):
        logger.warning("Invalid or empty metrics provided")
        return "offline"

    try:
        ram_percentage = safe_float(metrics.get("ram_percentage", 0))
        disk_percentage = safe_float(metrics.get("disk_percentage", 0))
        cpu_load = safe_float(metrics.get("cpu_load_5min", 0))

        # Check for warning conditions
        if (
            ram_percentage > PERFORMANCE_THRESHOLDS["memory_warning"]
            or disk_percentage > PERFORMANCE_THRESHOLDS["disk_warning"]
            or cpu_load > PERFORMANCE_THRESHOLDS["cpu_warning"]
        ):
            return "warning"

        # Check if server is offline based on timestamp
        timestamp_raw = metrics.get("timestamp")
        if timestamp_raw:
            try:
                timestamp = validate_timestamp(timestamp_raw)
                offline_threshold = timedelta(
                    minutes=STATUS_CONFIG["offline_timeout_minutes"]
                )
                if datetime.now() - timestamp.replace(tzinfo=None) > offline_threshold:
                    return "offline"
            except Exception as e:
                logger.warning(f"Failed to parse timestamp for status check: {e}")
                # If we can't parse timestamp, assume online if we got metrics
                return "online"

        return "online"

    except Exception as e:
        logger.error(f"Error determining server status: {e}")
        return "offline"


def get_performance_rating(cpu_load, ram_percentage, disk_percentage):
    """Calculate overall performance rating"""
    cpu_score = 100 - min(cpu_load * 10, 100)  # CPU load of 10 = 0 score
    ram_score = 100 - ram_percentage
    disk_score = 100 - disk_percentage

    overall_score = (cpu_score + ram_score + disk_score) / 3

    if overall_score >= 85:
        return "excellent", KU_COLORS["performance_good"]
    elif overall_score >= 70:
        return "good", KU_COLORS["performance_good"]
    elif overall_score >= 50:
        return "fair", KU_COLORS["performance_fair"]
    else:
        return "poor", KU_COLORS["performance_poor"]


def generate_alerts(metrics_list):
    """Generate system alerts based on metrics"""
    alerts = []

    for metric in metrics_list:
        server_name = metric.get("server_name", "Unknown")

        # CPU Alert
        cpu_load = safe_float(metric.get("cpu_load_5min", 0))
        if cpu_load > PERFORMANCE_THRESHOLDS["cpu_critical"]:
            alerts.append(
                {
                    "type": "critical",
                    "title": f"Critical CPU Load - {server_name}",
                    "description": f"CPU load is {cpu_load:.2f}, exceeding critical threshold",
                    "icon": "fas fa-exclamation-triangle",
                    "time": "Now",
                }
            )
        elif cpu_load > PERFORMANCE_THRESHOLDS["cpu_warning"]:
            alerts.append(
                {
                    "type": "warning",
                    "title": f"High CPU Load - {server_name}",
                    "description": f"CPU load is {cpu_load:.2f}, monitor closely",
                    "icon": "fas fa-exclamation-circle",
                    "time": "Now",
                }
            )

        # Memory Alert
        ram_percentage = metric.get("ram_percentage", 0)
        if ram_percentage > PERFORMANCE_THRESHOLDS["memory_critical"]:
            alerts.append(
                {
                    "type": "critical",
                    "title": f"Critical Memory Usage - {server_name}",
                    "description": f"Memory usage at {ram_percentage}%, immediate attention required",
                    "icon": "fas fa-memory",
                    "time": "Now",
                }
            )
        elif ram_percentage > PERFORMANCE_THRESHOLDS["memory_warning"]:
            alerts.append(
                {
                    "type": "warning",
                    "title": f"High Memory Usage - {server_name}",
                    "description": f"Memory usage at {ram_percentage}%",
                    "icon": "fas fa-memory",
                    "time": "Now",
                }
            )

        # Disk Alert
        disk_percentage = metric.get("disk_percentage", 0)
        if disk_percentage > PERFORMANCE_THRESHOLDS["disk_critical"]:
            alerts.append(
                {
                    "type": "critical",
                    "title": f"Critical Disk Usage - {server_name}",
                    "description": f"Disk usage at {disk_percentage}%, cleanup required",
                    "icon": "fas fa-hdd",
                    "time": "Now",
                }
            )
        elif disk_percentage > PERFORMANCE_THRESHOLDS["disk_warning"]:
            alerts.append(
                {
                    "type": "warning",
                    "title": f"High Disk Usage - {server_name}",
                    "description": f"Disk usage at {disk_percentage}%",
                    "icon": "fas fa-hdd",
                    "time": "Now",
                }
            )

    return alerts


def format_uptime(boot_time: Any) -> str:
    """
    Format server uptime based on boot time

    Args:
        boot_time: Boot time as string or datetime

    Returns:
        Formatted uptime string
    """
    if not boot_time:
        return "Unknown"

    try:
        if isinstance(boot_time, str):
            boot_datetime = validate_timestamp(boot_time)
        elif isinstance(boot_time, datetime):
            boot_datetime = boot_time
        else:
            logger.warning(f"Invalid boot_time type: {type(boot_time)}")
            return "Unknown"

        uptime = datetime.now() - boot_datetime.replace(tzinfo=None)
        days = uptime.days
        hours = uptime.seconds // 3600
        minutes = (uptime.seconds % 3600) // 60

        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    except Exception as e:
        logger.warning(f"Failed to format uptime: {e}")
        return "Unknown"


def calculate_resource_utilization(metrics):
    """Calculate overall resource utilization score"""
    if not metrics:
        return 0

    cpu_load = safe_float(metrics.get("cpu_load_5min", 0))
    ram_percentage = metrics.get("ram_percentage", 0)
    disk_percentage = metrics.get("disk_percentage", 0)

    # Normalize CPU load (assuming 8 cores as baseline)
    cpu_normalized = min(cpu_load / 8.0 * 100, 100)

    # Calculate weighted average
    utilization = cpu_normalized * 0.4 + ram_percentage * 0.4 + disk_percentage * 0.2
    return min(utilization, 100)


def get_status_badge_class(status):
    """Get CSS class for status badge"""
    return STATUS_CONFIG["status_classes"].get(status, "status-offline")


def get_performance_badge_class(performance):
    """Get CSS class for performance badge"""
    return STATUS_CONFIG["performance_classes"].get(performance, "perf-poor")


def is_high_usage_user(user_data):
    """Check if user has high resource usage"""
    cpu_usage = safe_float(user_data.get("cpu", 0))
    mem_usage = safe_float(user_data.get("mem", 0))

    return (
        cpu_usage > PERFORMANCE_THRESHOLDS["high_cpu_usage"]
        or mem_usage > PERFORMANCE_THRESHOLDS["high_memory_usage"]
    )


def get_trend_indicator(current_value, previous_value):
    """Get trend indicator (up/down/stable) for metrics"""
    if previous_value is None or current_value is None:
        return "stable", ""

    diff = current_value - previous_value
    percentage_change = (diff / previous_value * 100) if previous_value != 0 else 0

    if abs(percentage_change) < 5:  # Less than 5% change is considered stable
        return "stable", "→"
    elif percentage_change > 0:
        return "up", f"↑ {percentage_change:.1f}%"
    else:
        return "down", f"↓ {abs(percentage_change):.1f}%"


def format_bytes(bytes_value):
    """Format bytes to human readable format"""
    try:
        bytes_value = float(bytes_value)
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} PB"
    except (ValueError, TypeError):
        return "0 B"


def sanitize_server_name(server_name):
    """Sanitize server name for use in HTML IDs"""
    if not server_name:
        return "unknown"
    return server_name.lower().replace(" ", "-").replace("_", "-")
