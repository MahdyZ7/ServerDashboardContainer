# Unit tests for utils module
import pytest
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import (
    safe_float,
    determine_server_status,
    get_performance_rating,
    generate_alerts,
    format_uptime,
    get_status_badge_class,
    get_performance_badge_class,
    is_high_usage_user,
    get_trend_indicator,
    format_bytes,
    sanitize_server_name,
)
from config import PERFORMANCE_THRESHOLDS


class TestSafeFloat:
    """Tests for safe_float function"""

    def test_int_to_float(self):
        assert safe_float(42) == 42.0

    def test_float_to_float(self):
        assert safe_float(3.14) == 3.14

    def test_string_to_float(self):
        assert safe_float("3.14") == 3.14

    def test_invalid_string_returns_default(self):
        assert safe_float("invalid") == 0.0

    def test_none_returns_default(self):
        assert safe_float(None) == 0.0

    def test_custom_default(self):
        assert safe_float("invalid", default=99.0) == 99.0

    def test_list_returns_default(self):
        assert safe_float([1, 2, 3]) == 0.0


class TestDetermineServerStatus:
    """Tests for determine_server_status function"""

    def test_none_metrics_returns_offline(self):
        assert determine_server_status(None) == "offline"

    def test_empty_dict_returns_offline(self):
        assert determine_server_status({}) == "offline"

    def test_high_ram_returns_warning(self):
        metrics = {
            "ram_percentage": 90,
            "disk_percentage": 50,
            "cpu_load_5min": 2.0,
            "timestamp": datetime.now().isoformat(),
        }
        assert determine_server_status(metrics) == "warning"

    def test_high_disk_returns_warning(self):
        metrics = {
            "ram_percentage": 50,
            "disk_percentage": 90,
            "cpu_load_5min": 2.0,
            "timestamp": datetime.now().isoformat(),
        }
        assert determine_server_status(metrics) == "warning"

    def test_high_cpu_returns_warning(self):
        metrics = {
            "ram_percentage": 50,
            "disk_percentage": 50,
            "cpu_load_5min": 6.0,
            "timestamp": datetime.now().isoformat(),
        }
        assert determine_server_status(metrics) == "warning"

    def test_old_timestamp_returns_offline(self):
        old_time = datetime.now() - timedelta(hours=1)
        metrics = {
            "ram_percentage": 50,
            "disk_percentage": 50,
            "cpu_load_5min": 2.0,
            "timestamp": old_time.isoformat(),
        }
        assert determine_server_status(metrics) == "offline"

    def test_recent_timestamp_normal_metrics_returns_online(self):
        metrics = {
            "ram_percentage": 50,
            "disk_percentage": 50,
            "cpu_load_5min": 2.0,
            "timestamp": datetime.now().isoformat(),
        }
        assert determine_server_status(metrics) == "online"

    def test_invalid_timestamp_format_returns_online(self):
        """If timestamp can't be parsed, assume online if we got metrics"""
        metrics = {
            "ram_percentage": 50,
            "disk_percentage": 50,
            "cpu_load_5min": 2.0,
            "timestamp": "invalid",
        }
        status = determine_server_status(metrics)
        assert status in ["online", "warning"]  # Depends on metrics


class TestGetPerformanceRating:
    """Tests for get_performance_rating function"""

    def test_excellent_performance(self):
        rating, color = get_performance_rating(1.0, 10.0, 20.0)
        assert rating == "excellent"

    def test_good_performance(self):
        rating, color = get_performance_rating(2.0, 20.0, 30.0)
        assert rating == "good"

    def test_fair_performance(self):
        rating, color = get_performance_rating(5.0, 50.0, 50.0)
        assert rating == "fair"

    def test_poor_performance(self):
        rating, color = get_performance_rating(10.0, 90.0, 90.0)
        assert rating == "poor"

    def test_returns_color(self):
        rating, color = get_performance_rating(1.0, 10.0, 20.0)
        assert isinstance(color, str)
        assert color.startswith("#") or color.startswith("rgb")


class TestGenerateAlerts:
    """Tests for generate_alerts function"""

    def test_no_alerts_for_normal_metrics(self):
        metrics = [
            {
                "server_name": "Server1",
                "cpu_load_5min": 2.0,
                "ram_percentage": 50,
                "disk_percentage": 50,
            }
        ]
        alerts = generate_alerts(metrics)
        assert len(alerts) == 0

    def test_cpu_warning_alert(self):
        metrics = [
            {
                "server_name": "Server1",
                "cpu_load_5min": PERFORMANCE_THRESHOLDS["cpu_warning"] + 0.1,
                "ram_percentage": 50,
                "disk_percentage": 50,
            }
        ]
        alerts = generate_alerts(metrics)
        assert len(alerts) > 0
        assert any("CPU" in alert["title"] for alert in alerts)

    def test_cpu_critical_alert(self):
        metrics = [
            {
                "server_name": "Server1",
                "cpu_load_5min": PERFORMANCE_THRESHOLDS["cpu_critical"] + 0.1,
                "ram_percentage": 50,
                "disk_percentage": 50,
            }
        ]
        alerts = generate_alerts(metrics)
        assert len(alerts) > 0
        critical_alerts = [a for a in alerts if a["type"] == "critical"]
        assert len(critical_alerts) > 0

    def test_memory_alert(self):
        metrics = [
            {
                "server_name": "Server1",
                "cpu_load_5min": 2.0,
                "ram_percentage": PERFORMANCE_THRESHOLDS["memory_warning"] + 1,
                "disk_percentage": 50,
            }
        ]
        alerts = generate_alerts(metrics)
        assert len(alerts) > 0
        assert any(
            "Memory" in alert["title"] or "RAM" in alert["title"] for alert in alerts
        )

    def test_disk_alert(self):
        metrics = [
            {
                "server_name": "Server1",
                "cpu_load_5min": 2.0,
                "ram_percentage": 50,
                "disk_percentage": PERFORMANCE_THRESHOLDS["disk_warning"] + 1,
            }
        ]
        alerts = generate_alerts(metrics)
        assert len(alerts) > 0
        assert any("Disk" in alert["title"] for alert in alerts)

    def test_multiple_servers_multiple_alerts(self):
        metrics = [
            {
                "server_name": "Server1",
                "cpu_load_5min": PERFORMANCE_THRESHOLDS["cpu_critical"] + 1,
                "ram_percentage": 50,
                "disk_percentage": 50,
            },
            {
                "server_name": "Server2",
                "cpu_load_5min": 2.0,
                "ram_percentage": PERFORMANCE_THRESHOLDS["memory_critical"] + 1,
                "disk_percentage": 50,
            },
        ]
        alerts = generate_alerts(metrics)
        assert len(alerts) >= 2


class TestFormatUptime:
    """Tests for format_uptime function"""

    def test_none_returns_unknown(self):
        assert format_uptime(None) == "Unknown"

    def test_empty_string_returns_unknown(self):
        assert format_uptime("") == "Unknown"

    def test_days_hours_minutes(self):
        boot_time = datetime.now() - timedelta(days=2, hours=3, minutes=15)
        result = format_uptime(boot_time)
        assert "2d" in result
        assert "h" in result

    def test_hours_minutes(self):
        boot_time = datetime.now() - timedelta(hours=5, minutes=30)
        result = format_uptime(boot_time)
        assert "5h" in result
        assert "m" in result
        assert "d" not in result

    def test_minutes_only(self):
        boot_time = datetime.now() - timedelta(minutes=45)
        result = format_uptime(boot_time)
        assert "m" in result
        assert "h" not in result
        assert "d" not in result


class TestIsHighUsageUser:
    """Tests for is_high_usage_user function"""

    def test_high_cpu_usage(self):
        user_data = {"cpu": PERFORMANCE_THRESHOLDS["high_cpu_usage"] + 1, "mem": 20}
        assert is_high_usage_user(user_data) is True

    def test_high_memory_usage(self):
        user_data = {"cpu": 20, "mem": PERFORMANCE_THRESHOLDS["high_memory_usage"] + 1}
        assert is_high_usage_user(user_data) is True

    def test_normal_usage(self):
        user_data = {"cpu": 20, "mem": 30}
        assert is_high_usage_user(user_data) is False

    def test_string_values(self):
        user_data = {
            "cpu": str(PERFORMANCE_THRESHOLDS["high_cpu_usage"] + 1),
            "mem": "20",
        }
        assert is_high_usage_user(user_data) is True


class TestGetTrendIndicator:
    """Tests for get_trend_indicator function"""

    def test_increasing_trend(self):
        trend, indicator = get_trend_indicator(100, 90)
        assert trend == "up"
        assert "↑" in indicator

    def test_decreasing_trend(self):
        trend, indicator = get_trend_indicator(90, 100)
        assert trend == "down"
        assert "↓" in indicator

    def test_stable_trend(self):
        trend, indicator = get_trend_indicator(100, 98)
        assert trend == "stable"
        assert "→" in indicator

    def test_none_previous_value(self):
        trend, indicator = get_trend_indicator(100, None)
        assert trend == "stable"

    def test_zero_previous_value(self):
        """Should handle division by zero"""
        trend, indicator = get_trend_indicator(50, 0)
        # Should not crash
        assert trend in ["up", "down", "stable"]


class TestFormatBytes:
    """Tests for format_bytes function"""

    def test_bytes(self):
        result = format_bytes(500)
        assert "500" in result
        assert "B" in result

    def test_kilobytes(self):
        result = format_bytes(1024)
        assert "1.0" in result
        assert "KB" in result

    def test_megabytes(self):
        result = format_bytes(1024 * 1024)
        assert "1.0" in result
        assert "MB" in result

    def test_gigabytes(self):
        result = format_bytes(1024 * 1024 * 1024)
        assert "1.0" in result
        assert "GB" in result

    def test_invalid_input(self):
        result = format_bytes("invalid")
        assert result == "0 B"


class TestSanitizeServerName:
    """Tests for sanitize_server_name function"""

    def test_simple_name(self):
        assert sanitize_server_name("Server1") == "server1"

    def test_with_spaces(self):
        assert sanitize_server_name("Server 1") == "server-1"

    def test_with_underscores(self):
        assert sanitize_server_name("Server_1") == "server-1"

    def test_mixed_case(self):
        assert sanitize_server_name("MyServer") == "myserver"

    def test_empty_string(self):
        assert sanitize_server_name("") == "unknown"

    def test_none(self):
        assert sanitize_server_name(None) == "unknown"


class TestGetStatusBadgeClass:
    """Tests for get_status_badge_class function"""

    def test_online_status(self):
        assert get_status_badge_class("online") == "status-online"

    def test_warning_status(self):
        assert get_status_badge_class("warning") == "status-warning"

    def test_offline_status(self):
        assert get_status_badge_class("offline") == "status-offline"

    def test_unknown_status_returns_offline(self):
        assert get_status_badge_class("unknown") == "status-offline"


class TestGetPerformanceBadgeClass:
    """Tests for get_performance_badge_class function"""

    def test_excellent(self):
        assert get_performance_badge_class("excellent") == "perf-excellent"

    def test_good(self):
        assert get_performance_badge_class("good") == "perf-good"

    def test_fair(self):
        assert get_performance_badge_class("fair") == "perf-fair"

    def test_poor(self):
        assert get_performance_badge_class("poor") == "perf-poor"

    def test_unknown_returns_poor(self):
        assert get_performance_badge_class("unknown") == "perf-poor"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
