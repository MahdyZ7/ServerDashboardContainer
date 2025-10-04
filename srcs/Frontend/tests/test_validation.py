# Unit tests for validation module
import pytest
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from validation import (
    validate_percentage, validate_positive_number, validate_server_name,
    validate_time_range, validate_timestamp, validate_server_metrics,
    validate_user_data, safe_get
)
from exceptions import ValidationError


class TestValidatePercentage:
    """Tests for validate_percentage function"""

    def test_valid_percentage_int(self):
        assert validate_percentage(50, 'test') == 50.0

    def test_valid_percentage_float(self):
        assert validate_percentage(75.5, 'test') == 75.5

    def test_valid_percentage_string(self):
        assert validate_percentage("85", 'test') == 85.0

    def test_percentage_zero(self):
        assert validate_percentage(0, 'test') == 0.0

    def test_percentage_hundred(self):
        assert validate_percentage(100, 'test') == 100.0

    def test_invalid_negative(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_percentage(-10, 'test')
        assert 'between 0 and 100' in str(exc_info.value)

    def test_invalid_over_hundred(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_percentage(150, 'test')
        assert 'between 0 and 100' in str(exc_info.value)

    def test_invalid_type(self):
        with pytest.raises(ValidationError):
            validate_percentage("abc", 'test')

    def test_none_value(self):
        with pytest.raises(ValidationError):
            validate_percentage(None, 'test')


class TestValidatePositiveNumber:
    """Tests for validate_positive_number function"""

    def test_valid_positive(self):
        assert validate_positive_number(42, 'test') == 42.0

    def test_zero_is_valid(self):
        assert validate_positive_number(0, 'test') == 0.0

    def test_float_positive(self):
        assert validate_positive_number(3.14, 'test') == 3.14

    def test_invalid_negative(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_positive_number(-5, 'test')
        assert 'must be positive' in str(exc_info.value)

    def test_invalid_string(self):
        with pytest.raises(ValidationError):
            validate_positive_number("invalid", 'test')


class TestValidateServerName:
    """Tests for validate_server_name function"""

    def test_valid_server_name(self):
        assert validate_server_name("Server1") == "Server1"

    def test_strips_whitespace(self):
        assert validate_server_name("  Server1  ") == "Server1"

    def test_empty_string_raises_error(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_server_name("")
        assert 'cannot be empty' in str(exc_info.value)

    def test_whitespace_only_raises_error(self):
        with pytest.raises(ValidationError):
            validate_server_name("   ")

    def test_none_raises_error(self):
        with pytest.raises(ValidationError):
            validate_server_name(None)

    def test_non_string_raises_error(self):
        with pytest.raises(ValidationError):
            validate_server_name(123)

    def test_too_long_raises_error(self):
        long_name = "a" * 256
        with pytest.raises(ValidationError) as exc_info:
            validate_server_name(long_name)
        assert 'too long' in str(exc_info.value)


class TestValidateTimeRange:
    """Tests for validate_time_range function"""

    def test_valid_hours(self):
        assert validate_time_range(24) == 24

    def test_valid_hours_string(self):
        assert validate_time_range("12") == 12

    def test_zero_is_invalid(self):
        with pytest.raises(ValidationError):
            validate_time_range(0)

    def test_negative_is_invalid(self):
        with pytest.raises(ValidationError):
            validate_time_range(-5)

    def test_too_large_is_invalid(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_time_range(10000)
        assert 'too large' in str(exc_info.value)

    def test_invalid_type(self):
        with pytest.raises(ValidationError):
            validate_time_range("invalid")


class TestValidateTimestamp:
    """Tests for validate_timestamp function"""

    def test_datetime_object_passthrough(self):
        dt = datetime.now()
        assert validate_timestamp(dt) == dt

    def test_iso_format_with_microseconds(self):
        ts = "2025-10-01T12:30:45.123456"
        result = validate_timestamp(ts)
        assert isinstance(result, datetime)
        assert result.year == 2025
        assert result.month == 10

    def test_iso_format_without_microseconds(self):
        ts = "2025-10-01T12:30:45"
        result = validate_timestamp(ts)
        assert isinstance(result, datetime)

    def test_space_separator(self):
        ts = "2025-10-01 12:30:45"
        result = validate_timestamp(ts)
        assert isinstance(result, datetime)

    def test_date_only(self):
        ts = "2025-10-01"
        result = validate_timestamp(ts)
        assert isinstance(result, datetime)

    def test_iso_with_timezone_z(self):
        ts = "2025-10-01T12:30:45Z"
        result = validate_timestamp(ts)
        assert isinstance(result, datetime)

    def test_invalid_format_raises_error(self):
        with pytest.raises(ValidationError):
            validate_timestamp("invalid")

    def test_non_string_non_datetime_raises_error(self):
        with pytest.raises(ValidationError):
            validate_timestamp(12345)


class TestValidateServerMetrics:
    """Tests for validate_server_metrics function"""

    def test_valid_metrics(self):
        metrics = {
            'server_name': 'Server1',
            'cpu_load_5min': 50.0,
            'ram_percentage': 75.0,
            'disk_percentage': 60.0
        }
        result = validate_server_metrics(metrics)
        assert result['server_name'] == 'Server1'
        assert result['cpu_load_5min'] == 50.0

    def test_missing_server_name_raises_error(self):
        metrics = {'cpu_load_5min': 50.0}
        with pytest.raises(ValidationError) as exc_info:
            validate_server_metrics(metrics)
        assert 'Missing required fields' in str(exc_info.value)

    def test_non_dict_raises_error(self):
        with pytest.raises(ValidationError):
            validate_server_metrics([])

    def test_converts_numeric_strings(self):
        metrics = {
            'server_name': 'Server1',
            'cpu_load_5min': '50.5',
            'ram_percentage': '75'
        }
        result = validate_server_metrics(metrics)
        assert result['cpu_load_5min'] == 50.5
        assert result['ram_percentage'] == 75.0

    def test_handles_out_of_range_values(self):
        """Should log warning but not raise error for out of range values"""
        metrics = {
            'server_name': 'Server1',
            'cpu_load_5min': 150.0  # Out of range but allowed
        }
        result = validate_server_metrics(metrics)
        assert result['cpu_load_5min'] == 150.0

    def test_handles_invalid_numeric_values(self):
        """Should convert invalid values to 0"""
        metrics = {
            'server_name': 'Server1',
            'cpu_load_5min': 'invalid'
        }
        result = validate_server_metrics(metrics)
        assert result['cpu_load_5min'] == 0


class TestValidateUserData:
    """Tests for validate_user_data function"""

    def test_valid_user_data(self):
        user = {
            'username': 'testuser',
            'cpu': 50.0,
            'mem': 30.0,
            'disk': 10.5
        }
        result = validate_user_data(user)
        assert result['username'] == 'testuser'
        assert result['cpu'] == 50.0

    def test_missing_username_raises_error(self):
        user = {'cpu': 50.0}
        with pytest.raises(ValidationError):
            validate_user_data(user)

    def test_converts_numeric_strings(self):
        user = {
            'username': 'testuser',
            'cpu': '25.5',
            'mem': '40',
            'disk': '5.0'
        }
        result = validate_user_data(user)
        assert result['cpu'] == 25.5
        assert result['mem'] == 40.0
        assert result['disk'] == 5.0

    def test_handles_invalid_numerics(self):
        """Should convert invalid numeric values to 0.0"""
        user = {
            'username': 'testuser',
            'cpu': 'invalid'
        }
        result = validate_user_data(user)
        assert result['cpu'] == 0.0


class TestSafeGet:
    """Tests for safe_get function"""

    def test_get_existing_key(self):
        data = {'key': 'value'}
        assert safe_get(data, 'key') == 'value'

    def test_get_missing_key_returns_default(self):
        data = {'key': 'value'}
        assert safe_get(data, 'missing', default='default') == 'default'

    def test_none_value_returns_none(self):
        data = {'key': None}
        assert safe_get(data, 'key') is None

    def test_with_validator_valid(self):
        data = {'number': '42'}
        result = safe_get(data, 'number', validator=int)
        assert result == 42

    def test_with_validator_invalid_returns_default(self):
        data = {'number': 'abc'}
        result = safe_get(data, 'number', default=0, validator=int)
        assert result == 0

    def test_validator_not_called_for_none(self):
        data = {'key': None}
        # Validator that would raise an error
        result = safe_get(data, 'key', validator=lambda x: 1/0)
        assert result is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
