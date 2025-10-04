# Input validation utilities for the Server Monitoring Dashboard
from typing import Any, Optional, Dict, List
from datetime import datetime
import logging
from exceptions import ValidationError

logger = logging.getLogger(__name__)


def validate_percentage(value: Any, field_name: str = "percentage") -> float:
    """
    Validate that a value is a valid percentage (0-100)

    Args:
        value: Value to validate
        field_name: Name of the field for error messages

    Returns:
        Validated float value

    Raises:
        ValidationError: If validation fails
    """
    try:
        float_value = float(value)
        if not 0 <= float_value <= 100:
            raise ValidationError(
                f"{field_name} must be between 0 and 100, got {float_value}",
                details={'field': field_name, 'value': value}
            )
        return float_value
    except (TypeError, ValueError) as e:
        raise ValidationError(
            f"Invalid {field_name} value: {value}",
            details={'field': field_name, 'value': value, 'error': str(e)}
        )


def validate_positive_number(value: Any, field_name: str = "number") -> float:
    """
    Validate that a value is a positive number

    Args:
        value: Value to validate
        field_name: Name of the field for error messages

    Returns:
        Validated float value

    Raises:
        ValidationError: If validation fails
    """
    try:
        float_value = float(value)
        if float_value < 0:
            raise ValidationError(
                f"{field_name} must be positive, got {float_value}",
                details={'field': field_name, 'value': value}
            )
        return float_value
    except (TypeError, ValueError) as e:
        raise ValidationError(
            f"Invalid {field_name} value: {value}",
            details={'field': field_name, 'value': value, 'error': str(e)}
        )


def validate_server_name(server_name: Any) -> str:
    """
    Validate and sanitize server name

    Args:
        server_name: Server name to validate

    Returns:
        Validated and sanitized server name

    Raises:
        ValidationError: If validation fails
    """
    if not server_name:
        raise ValidationError(
            "Server name cannot be empty",
            details={'value': server_name}
        )

    if not isinstance(server_name, str):
        raise ValidationError(
            f"Server name must be a string, got {type(server_name).__name__}",
            details={'value': server_name, 'type': type(server_name).__name__}
        )

    # Sanitize: remove leading/trailing whitespace
    sanitized = server_name.strip()

    if not sanitized:
        raise ValidationError(
            "Server name cannot be empty after sanitization",
            details={'original': server_name}
        )

    # Check length
    if len(sanitized) > 255:
        raise ValidationError(
            f"Server name too long: {len(sanitized)} characters (max 255)",
            details={'length': len(sanitized)}
        )

    return sanitized


def validate_time_range(hours: Any) -> int:
    """
    Validate time range in hours

    Args:
        hours: Number of hours to validate

    Returns:
        Validated integer hours

    Raises:
        ValidationError: If validation fails
    """
    try:
        int_hours = int(hours)
        if int_hours <= 0:
            raise ValidationError(
                f"Time range must be positive, got {int_hours}",
                details={'value': hours}
            )
        if int_hours > 8760:  # 1 year
            raise ValidationError(
                f"Time range too large: {int_hours} hours (max 8760)",
                details={'value': hours}
            )
        return int_hours
    except (TypeError, ValueError) as e:
        raise ValidationError(
            f"Invalid time range value: {hours}",
            details={'value': hours, 'error': str(e)}
        )


def validate_server_metrics(metrics: Dict) -> Dict:
    """
    Validate server metrics dictionary structure

    Args:
        metrics: Metrics dictionary to validate

    Returns:
        Validated metrics dictionary

    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(metrics, dict):
        raise ValidationError(
            f"Metrics must be a dictionary, got {type(metrics).__name__}",
            details={'type': type(metrics).__name__}
        )

    required_fields = ['server_name']
    missing_fields = [f for f in required_fields if f not in metrics]

    if missing_fields:
        raise ValidationError(
            f"Missing required fields: {', '.join(missing_fields)}",
            details={'missing_fields': missing_fields}
        )

    # Validate numeric fields if present
    numeric_fields = {
        'cpu_load_1min': (0, 100),
        'cpu_load_5min': (0, 100),
        'cpu_load_15min': (0, 100),
        'ram_percentage': (0, 100),
        'disk_percentage': (0, 100),
        'logged_users': (0, 10000),
        'tcp_connections': (0, 100000)
    }

    validated = metrics.copy()

    for field, (min_val, max_val) in numeric_fields.items():
        if field in validated:
            try:
                value = float(validated[field])
                if not min_val <= value <= max_val:
                    logger.warning(
                        f"Value for {field} out of expected range: {value} "
                        f"(expected {min_val}-{max_val})"
                    )
                validated[field] = value
            except (TypeError, ValueError):
                logger.warning(f"Invalid numeric value for {field}: {validated[field]}")
                validated[field] = 0

    return validated


def validate_timestamp(timestamp: Any) -> datetime:
    """
    Validate and parse timestamp

    Args:
        timestamp: Timestamp to validate (string or datetime)

    Returns:
        Validated datetime object

    Raises:
        ValidationError: If validation fails
    """
    if isinstance(timestamp, datetime):
        return timestamp

    if not isinstance(timestamp, str):
        raise ValidationError(
            f"Timestamp must be string or datetime, got {type(timestamp).__name__}",
            details={'type': type(timestamp).__name__}
        )

    # Try multiple timestamp formats
    formats = [
        '%Y-%m-%dT%H:%M:%S.%f',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%d %H:%M:%S.%f',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d',
    ]

    # Try ISO format with timezone
    try:
        return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        pass

    # Try other formats
    for fmt in formats:
        try:
            return datetime.strptime(timestamp, fmt)
        except ValueError:
            continue

    raise ValidationError(
        f"Unable to parse timestamp: {timestamp}",
        details={'value': timestamp, 'tried_formats': formats}
    )


def validate_user_data(user: Dict) -> Dict:
    """
    Validate user data dictionary structure

    Args:
        user: User data dictionary to validate

    Returns:
        Validated user dictionary

    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(user, dict):
        raise ValidationError(
            f"User data must be a dictionary, got {type(user).__name__}",
            details={'type': type(user).__name__}
        )

    required_fields = ['username']
    missing_fields = [f for f in required_fields if f not in user]

    if missing_fields:
        raise ValidationError(
            f"Missing required fields: {', '.join(missing_fields)}",
            details={'missing_fields': missing_fields}
        )

    validated = user.copy()

    # Validate numeric fields
    numeric_fields = ['cpu', 'mem', 'disk']
    for field in numeric_fields:
        if field in validated:
            try:
                validated[field] = float(validated[field])
            except (TypeError, ValueError):
                logger.warning(f"Invalid numeric value for {field}: {validated[field]}")
                validated[field] = 0.0

    return validated


def safe_get(dictionary: Dict, key: str, default: Any = None, validator: Optional[callable] = None) -> Any:
    """
    Safely get value from dictionary with optional validation

    Args:
        dictionary: Dictionary to get value from
        key: Key to retrieve
        default: Default value if key not found
        validator: Optional validation function

    Returns:
        Retrieved value or default
    """
    value = dictionary.get(key, default)

    if validator and value is not None:
        try:
            return validator(value)
        except Exception as e:
            logger.warning(f"Validation failed for key '{key}': {e}")
            return default

    return value
