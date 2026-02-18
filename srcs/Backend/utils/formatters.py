"""
Data Formatters
Single Responsibility: Format and transform data for display
"""
from datetime import datetime
from typing import Any, Dict, List, Optional


def format_percentage(value: float, decimals: int = 1) -> str:
    """
    Format a percentage value with specified decimal places

    Args:
        value: The percentage value
        decimals: Number of decimal places (default: 1)

    Returns:
        Formatted percentage string
    """
    try:
        return f"{float(value):.{decimals}f}%"
    except (ValueError, TypeError):
        return "0.0%"


def format_bytes(bytes_value: int, decimals: int = 2) -> str:
    """
    Format bytes into human-readable format (KB, MB, GB, TB)

    Args:
        bytes_value: Value in bytes
        decimals: Number of decimal places (default: 2)

    Returns:
        Formatted string (e.g., "1.5 GB")
    """
    try:
        bytes_value = float(bytes_value)
        if bytes_value < 1024:
            return f"{bytes_value:.{decimals}f} B"
        elif bytes_value < 1024 ** 2:
            return f"{bytes_value / 1024:.{decimals}f} KB"
        elif bytes_value < 1024 ** 3:
            return f"{bytes_value / (1024 ** 2):.{decimals}f} MB"
        elif bytes_value < 1024 ** 4:
            return f"{bytes_value / (1024 ** 3):.{decimals}f} GB"
        else:
            return f"{bytes_value / (1024 ** 4):.{decimals}f} TB"
    except (ValueError, TypeError):
        return "0 B"


def format_timestamp(timestamp: Any, format_string: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format a timestamp into a readable string

    Args:
        timestamp: datetime object or ISO format string
        format_string: Output format string

    Returns:
        Formatted timestamp string
    """
    try:
        if isinstance(timestamp, str):
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        elif isinstance(timestamp, datetime):
            dt = timestamp
        else:
            return "N/A"

        return dt.strftime(format_string)
    except (ValueError, TypeError, AttributeError):
        return "N/A"


def format_uptime(seconds: int) -> str:
    """
    Format uptime in seconds to human-readable format

    Args:
        seconds: Uptime in seconds

    Returns:
        Formatted uptime string (e.g., "2 days, 3 hours")
    """
    try:
        seconds = int(seconds)
        days, remainder = divmod(seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, _ = divmod(remainder, 60)

        parts = []
        if days > 0:
            parts.append(f"{days} day{'s' if days != 1 else ''}")
        if hours > 0:
            parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
        if minutes > 0 or not parts:
            parts.append(f"{minutes} min{'s' if minutes != 1 else ''}")

        return ", ".join(parts[:2])  # Show only first 2 parts
    except (ValueError, TypeError):
        return "N/A"


def format_load_average(load: float, cores: int = 1) -> str:
    """
    Format CPU load average with context

    Args:
        load: Load average value
        cores: Number of CPU cores (for percentage calculation)

    Returns:
        Formatted load string with percentage
    """
    try:
        load = float(load)
        if cores > 0:
            percentage = (load / cores) * 100
            return f"{load:.2f} ({percentage:.1f}%)"
        return f"{load:.2f}"
    except (ValueError, TypeError):
        return "0.00"


def get_status_class(metric_type: str, value: float, thresholds: Dict[str, float]) -> str:
    """
    Get CSS class based on metric value and thresholds

    Args:
        metric_type: Type of metric ('cpu', 'memory', 'disk')
        value: Current value
        thresholds: Dictionary of threshold values

    Returns:
        CSS class name
    """
    try:
        value = float(value)
        warning_key = f"{metric_type}_warning"
        critical_key = f"{metric_type}_critical"

        if warning_key in thresholds and critical_key in thresholds:
            if value >= thresholds[critical_key]:
                return "status-critical"
            elif value >= thresholds[warning_key]:
                return "status-warning"
            else:
                return "status-good"
        return "status-unknown"
    except (ValueError, TypeError, KeyError):
        return "status-unknown"


def get_performance_rating(cpu_load: float, ram_usage: float, disk_usage: float) -> Dict[str, Any]:
    """
    Calculate overall performance rating

    Args:
        cpu_load: CPU load percentage
        ram_usage: RAM usage percentage
        disk_usage: Disk usage percentage

    Returns:
        Dictionary with rating, class, and color
    """
    try:
        # Calculate weighted score (lower is better)
        score = (cpu_load * 0.4) + (ram_usage * 0.4) + (disk_usage * 0.2)

        if score < 40:
            return {
                "rating": "Excellent",
                "class": "perf-excellent",
                "icon": "fa-check-circle",
                "score": score
            }
        elif score < 60:
            return {
                "rating": "Good",
                "class": "perf-good",
                "icon": "fa-thumbs-up",
                "score": score
            }
        elif score < 80:
            return {
                "rating": "Fair",
                "class": "perf-fair",
                "icon": "fa-exclamation-triangle",
                "score": score
            }
        else:
            return {
                "rating": "Poor",
                "class": "perf-poor",
                "icon": "fa-exclamation-circle",
                "score": score
            }
    except (ValueError, TypeError):
        return {
            "rating": "Unknown",
            "class": "perf-unknown",
            "icon": "fa-question-circle",
            "score": 0
        }


def truncate_text(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """
    Truncate text to specified length with suffix

    Args:
        text: Input text
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated text
    """
    try:
        text = str(text)
        if len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix
    except (ValueError, TypeError):
        return ""
