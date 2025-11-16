# Generated Validators
# Schema Version: 1.0.0
# Generated At: 2025-11-05T00:11:46.315719
# DO NOT EDIT MANUALLY

from typing import Any, Optional


class ValidationError(Exception):
    """Validation error exception."""

    pass


def validate_string(
    value: Any, field_name: str = "field", max_length: Optional[int] = None
) -> str:
    """Validate string with optional max length."""
    if not isinstance(value, str):
        raise ValidationError(
            f"{field_name} must be a string, got {type(value).__name__}"
        )
    if max_length is not None and len(value) > max_length:
        raise ValidationError(f"{field_name} exceeds max length {max_length}")
    return value


def validate_integer(
    value: Any,
    field_name: str = "field",
    min_val: Optional[int] = None,
    max_val: Optional[int] = None,
) -> int:
    """Validate integer with optional min/max."""
    try:
        val = int(value)
        if min_val is not None and val < min_val:
            raise ValidationError(f"{field_name} must be >= {min_val}, got {val}")
        if max_val is not None and val > max_val:
            raise ValidationError(f"{field_name} must be <= {max_val}, got {val}")
        return val
    except (ValueError, TypeError):
        raise ValidationError(
            f"{field_name} must be an integer, got {type(value).__name__}"
        )


def validate_percentage(value: Any, field_name: str = "field") -> float:
    """Validate percentage (0-100)."""
    try:
        val = float(value)
        if val < 0 or val > 100:
            raise ValidationError(f"{field_name} must be between 0 and 100, got {val}")
        return val
    except (ValueError, TypeError):
        raise ValidationError(
            f"{field_name} must be a number, got {type(value).__name__}"
        )


def validate_float(
    value: Any,
    field_name: str = "field",
    min_val: Optional[float] = None,
    max_val: Optional[float] = None,
) -> float:
    """Validate float with optional min/max."""
    try:
        val = float(value)
        if min_val is not None and val < min_val:
            raise ValidationError(f"{field_name} must be >= {min_val}, got {val}")
        if max_val is not None and val > max_val:
            raise ValidationError(f"{field_name} must be <= {max_val}, got {val}")
        return val
    except (ValueError, TypeError):
        raise ValidationError(
            f"{field_name} must be a number, got {type(value).__name__}"
        )


# Field-specific validators


class ServerMetricsValidator:
    """Validator for server_metrics fields."""

    @staticmethod
    def validate_architecture(value: Any) -> Any:
        """Validate System architecture (kernel, release, machine)."""
        return validate_string(value, "architecture", 255)

    @staticmethod
    def validate_os(value: Any) -> Any:
        """Validate Operating system name and version."""
        return validate_string(value, "os", 100)

    @staticmethod
    def validate_physical_cpus(value: Any) -> Any:
        """Validate Number of physical CPU sockets."""
        return validate_integer(value, "physical_cpus", 0, 256)

    @staticmethod
    def validate_virtual_cpus(value: Any) -> Any:
        """Validate Number of virtual CPU cores (threads)."""
        return validate_integer(value, "virtual_cpus", 0, 1024)

    @staticmethod
    def validate_ram_used(value: Any) -> Any:
        """Validate RAM currently in use."""
        return validate_string(value, "ram_used", None)

    @staticmethod
    def validate_ram_total(value: Any) -> Any:
        """Validate Total RAM available."""
        return validate_string(value, "ram_total", None)

    @staticmethod
    def validate_ram_percentage(value: Any) -> Any:
        """Validate RAM usage percentage."""
        return validate_percentage(value, "ram_percentage")

    @staticmethod
    def validate_disk_used(value: Any) -> Any:
        """Validate Disk space used."""
        return validate_string(value, "disk_used", None)

    @staticmethod
    def validate_disk_total(value: Any) -> Any:
        """Validate Total disk space."""
        return validate_string(value, "disk_total", None)

    @staticmethod
    def validate_disk_percentage(value: Any) -> Any:
        """Validate Disk usage percentage."""
        return validate_string(value, "disk_percentage", None)

    @staticmethod
    def validate_cpu_load_1min(value: Any) -> Any:
        """Validate CPU load average (1 minute)."""
        return validate_string(value, "cpu_load_1min", None)

    @staticmethod
    def validate_cpu_load_5min(value: Any) -> Any:
        """Validate CPU load average (5 minutes)."""
        return validate_string(value, "cpu_load_5min", None)

    @staticmethod
    def validate_cpu_load_15min(value: Any) -> Any:
        """Validate CPU load average (15 minutes)."""
        return validate_string(value, "cpu_load_15min", None)

    @staticmethod
    def validate_last_boot(value: Any) -> Any:
        """Validate Last system boot time."""
        return validate_string(value, "last_boot", None)

    @staticmethod
    def validate_tcp_connections(value: Any) -> Any:
        """Validate Number of TCP connections."""
        return validate_integer(value, "tcp_connections", 0, None)

    @staticmethod
    def validate_logged_users(value: Any) -> Any:
        """Validate Number of logged-in users."""
        return validate_integer(value, "logged_users", 0, None)

    @staticmethod
    def validate_active_vnc(value: Any) -> Any:
        """Validate Active VNC sessions."""
        return validate_integer(value, "active_vnc", 0, None)

    @staticmethod
    def validate_active_ssh(value: Any) -> Any:
        """Validate Active SSH sessions."""
        return validate_integer(value, "active_ssh", 0, None)


class TopUsersValidator:
    """Validator for top_users fields."""

    @staticmethod
    def validate_username(value: Any) -> Any:
        """Validate Username."""
        return validate_string(value, "username", 50)

    @staticmethod
    def validate_cpu_percentage(value: Any) -> Any:
        """Validate CPU usage percentage."""
        return validate_float(value, "cpu_percentage", 0, 1000)

    @staticmethod
    def validate_memory_percentage(value: Any) -> Any:
        """Validate Memory usage percentage."""
        return validate_float(value, "memory_percentage", 0, 100)

    @staticmethod
    def validate_disk_usage_gb(value: Any) -> Any:
        """Validate Disk usage in GB."""
        return validate_float(value, "disk_usage_gb", 0, None)

    @staticmethod
    def validate_process_count(value: Any) -> Any:
        """Validate Number of processes."""
        return validate_integer(value, "process_count", 0, None)

    @staticmethod
    def validate_top_process(value: Any) -> Any:
        """Validate Top CPU-consuming process."""
        return validate_string(value, "top_process", 255)

    @staticmethod
    def validate_last_login(value: Any) -> Any:
        """Validate Last login timestamp."""
        return validate_string(value, "last_login", None)

    @staticmethod
    def validate_full_name(value: Any) -> Any:
        """Validate User's full name."""
        return validate_string(value, "full_name", 255)
