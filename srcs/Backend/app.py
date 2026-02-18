#!/usr/bin/env python3
"""
Unified Flask Application
Khalifa University Server Monitoring Dashboard
Combines API backend and Frontend dashboard in one application
Following Single Responsibility Principle and KU Brand Guidelines 2020
"""
from flask import Flask, render_template, jsonify
from flask_cors import CORS
import psycopg2
import logging
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import requests

from flask_config import Config, KU_COLORS, DASHBOARD_CONFIG, FONTS
from blueprints.dashboard import dashboard_bp

# Load environment variables
load_dotenv(".env")

# Database configuration
DB_CONFIG = {
    "host": "postgres",
    "user": "postgres",
    "password": os.getenv("POSTGRES_PASSWORD"),
    "database": "server_db",
}

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_db_connection():
    """Get database connection."""
    try:
        return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise


def create_app(config_class=Config):
    """
    Application factory pattern for creating Flask app
    Combines API backend and dashboard frontend
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Enable CORS
    CORS(app)

    # Register dashboard blueprint
    app.register_blueprint(dashboard_bp)

    # Inject global template variables
    @app.context_processor
    def inject_globals():
        """Inject KU brand colors and config into all templates"""
        return {
            'KU_COLORS': KU_COLORS,
            'DASHBOARD_CONFIG': DASHBOARD_CONFIG,
            'FONTS': FONTS,
        }

    # ==========================================
    # API Endpoints (formerly in api.py)
    # ==========================================

    @app.route('/health')
    @app.route('/api/health')
    def health_check():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'service': 'unified-dashboard',
            'timestamp': datetime.now().isoformat()
        })

    @app.route("/api/health/<server_name>", methods=["GET"])
    def get_server_health(server_name: str):
        """Get server health for a specific server."""
        ip_address_name = None
        for name, value in os.environ.items():
            if server_name in value:
                ip_address_name = name.split("_")[0] + "_IP"
                break
        server_ip = os.getenv(ip_address_name)
        if not server_ip:
            return jsonify(
                {"success": False, "error": f"No IP address found for {server_name}"}
            ), 404
        try:
            response = requests.get(f"http://{server_ip}", timeout=5)
            if response.status_code == 200:
                return jsonify(
                    {
                        "success": True,
                        "data": {
                            "server_name": server_name,
                            "ip_address": server_ip,
                            "timestamp": datetime.now().isoformat(),
                        },
                    }
                )
            else:
                return jsonify(
                    {"success": False, "error": f"Server {server_name} is not responding"}
                ), 500
        except Exception as e:
            return jsonify(
                {"success": False, "error": f"Error checking server health: {e}"}
            ), 500

    @app.route("/api/servers/metrics/latest", methods=["GET"])
    def get_latest_server_metrics():
        """Get the latest server metrics for all servers."""
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            query = """
            WITH latest_records AS (
                SELECT server_name, MAX(timestamp) as max_timestamp
                FROM server_metrics
                GROUP BY server_name
            )
            SELECT sm.*
            FROM server_metrics sm
            JOIN latest_records lr ON sm.server_name = lr.server_name AND sm.timestamp = lr.max_timestamp
            ORDER BY sm.server_name
            """

            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description]
            metrics = [dict(zip(columns, row)) for row in cursor.fetchall()]

            # Convert datetime objects to ISO format strings
            for metric in metrics:
                if "timestamp" in metric and metric["timestamp"]:
                    metric["timestamp"] = metric["timestamp"].isoformat()

            return jsonify({"success": True, "data": metrics, "count": len(metrics)})
        except Exception as e:
            logger.error(f"Error fetching latest server metrics: {e}")
            return jsonify({"success": False, "error": str(e)}), 500
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    @app.route("/api/servers/<server_name>/metrics/historical", methods=["GET"])
    @app.route("/api/servers/<server_name>/metrics/historical/<int:hours>", methods=["GET"])
    def get_historical_metrics(server_name, hours=24):
        """Get historical metrics for a specific server."""
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            query = """
            SELECT timestamp, ram_percentage, disk_percentage, cpu_load_1min,
                   cpu_load_5min, cpu_load_15min, tcp_connections, logged_users,
                   cpu_usage_percent, swap_used_mb, swap_total_mb, swap_percentage,
                   net_rx_bytes, net_tx_bytes
            FROM server_metrics
            WHERE server_name = %s AND timestamp > NOW() - INTERVAL %s
            ORDER BY timestamp
            """

            cursor.execute(query, (server_name, f"{hours} hours"))
            columns = [desc[0] for desc in cursor.description]
            metrics = [dict(zip(columns, row)) for row in cursor.fetchall()]

            # Convert datetime objects to ISO format strings
            for metric in metrics:
                if "timestamp" in metric and metric["timestamp"]:
                    metric["timestamp"] = metric["timestamp"].isoformat()

            return jsonify(
                {
                    "success": True,
                    "data": metrics,
                    "server_name": server_name,
                    "hours": hours,
                    "count": len(metrics),
                }
            )
        except Exception as e:
            logger.error(f"Error fetching historical metrics for {server_name}: {e}")
            return jsonify({"success": False, "error": str(e)}), 500
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    @app.route("/api/users/top", methods=["GET"])
    def get_top_users():
        """Get top users data from all servers."""
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            query = """
            SELECT server_name, username, cpu, mem, disk, process_count,
                   top_process, last_login, full_name, timestamp
            FROM top_users
            ORDER BY server_name, cpu DESC
            """

            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description]
            users = [dict(zip(columns, row)) for row in cursor.fetchall()]

            # Convert datetime objects to ISO format strings
            for user in users:
                if "timestamp" in user and user["timestamp"]:
                    user["timestamp"] = user["timestamp"].isoformat()
                if "last_login" in user and user["last_login"]:
                    user["last_login"] = user["last_login"].isoformat()

            return jsonify({"success": True, "data": users, "count": len(users)})
        except Exception as e:
            logger.error(f"Error fetching top users: {e}")
            return jsonify({"success": False, "error": str(e)}), 500
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    @app.route("/api/users/top/<server_name>", methods=["GET"])
    def get_top_users_by_server(server_name):
        """Get top users data for a specific server."""
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            query = """
            SELECT username, cpu, mem, disk, process_count,
                   top_process, last_login, full_name, timestamp
            FROM top_users
            WHERE server_name = %s
            ORDER BY cpu DESC
            """

            cursor.execute(query, (server_name,))
            columns = [desc[0] for desc in cursor.description]
            users = [dict(zip(columns, row)) for row in cursor.fetchall()]

            # Convert datetime objects to ISO format strings
            for user in users:
                if "timestamp" in user and user["timestamp"]:
                    user["timestamp"] = user["timestamp"].isoformat()
                if "last_login" in user and user["last_login"]:
                    user["last_login"] = user["last_login"].isoformat()

            return jsonify(
                {
                    "success": True,
                    "data": users,
                    "server_name": server_name,
                    "count": len(users),
                }
            )
        except Exception as e:
            logger.error(f"Error fetching top users for {server_name}: {e}")
            return jsonify({"success": False, "error": str(e)}), 500
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    @app.route("/api/servers/list", methods=["GET"])
    def get_server_list():
        """Get list of available servers."""
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            query = """
            SELECT DISTINCT server_name
            FROM server_metrics
            ORDER BY server_name
            """

            cursor.execute(query)
            servers = [row[0] for row in cursor.fetchall()]

            return jsonify({"success": True, "data": servers, "count": len(servers)})
        except Exception as e:
            logger.error(f"Error fetching server list: {e}")
            return jsonify({"success": False, "error": str(e)}), 500
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    @app.route("/api/servers/<server_name>/status", methods=["GET"])
    def get_server_status(server_name):
        """Get current status for a specific server."""
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            query = """
            SELECT *
            FROM server_metrics
            WHERE server_name = %s
            ORDER BY timestamp DESC
            LIMIT 1
            """

            cursor.execute(query, (server_name,))
            columns = [desc[0] for desc in cursor.description]
            result = cursor.fetchone()

            if not result:
                return jsonify(
                    {"success": False, "error": f"No data found for server {server_name}"}
                ), 404

            metric = dict(zip(columns, result))

            # Convert datetime objects to ISO format strings
            if "timestamp" in metric and metric["timestamp"]:
                metric["timestamp"] = metric["timestamp"].isoformat()

            # Determine server status
            ram_percentage = metric.get("ram_percentage", 0)
            disk_percentage = metric.get("disk_percentage", 0)
            cpu_load = float(metric.get("cpu_load_5min", 0))
            cpu_usage = metric.get("cpu_usage_percent")
            swap_percentage = metric.get("swap_percentage", 0) or 0

            # Use actual CPU utilization if available, otherwise fall back to load heuristic
            cpu_high = (float(cpu_usage) > 85) if cpu_usage is not None else (cpu_load > 5)

            if ram_percentage > 90 or disk_percentage > 90 or cpu_high or swap_percentage > 90:
                status = "warning"
            elif datetime.now() - datetime.fromisoformat(metric["timestamp"]) > timedelta(
                minutes=15
            ):
                status = "offline"
            else:
                status = "online"

            metric["status"] = status

            return jsonify({"success": True, "data": metric})
        except Exception as e:
            logger.error(f"Error fetching server status for {server_name}: {e}")
            return jsonify({"success": False, "error": str(e)}), 500
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    @app.route("/api/system/overview", methods=["GET"])
    def get_system_overview():
        """Get system overview statistics."""
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Get latest metrics for all servers
            latest_query = """
            WITH latest_records AS (
                SELECT server_name, MAX(timestamp) as max_timestamp
                FROM server_metrics
                GROUP BY server_name
            )
            SELECT sm.*
            FROM server_metrics sm
            JOIN latest_records lr ON sm.server_name = lr.server_name AND sm.timestamp = lr.max_timestamp
            """

            cursor.execute(latest_query)
            columns = [desc[0] for desc in cursor.description]
            metrics = [dict(zip(columns, row)) for row in cursor.fetchall()]

            # Calculate statistics
            total_servers = len(metrics)
            online_servers = 0
            warning_servers = 0
            offline_servers = 0

            total_cpu_load = 0
            total_cpu_usage = 0
            cpu_usage_count = 0
            total_ram_usage = 0
            total_disk_usage = 0
            total_swap_usage = 0
            total_users = 0
            total_rx_bytes = 0
            total_tx_bytes = 0

            for metric in metrics:
                ram_percentage = metric.get("ram_percentage", 0)
                disk_percentage = metric.get("disk_percentage", 0)
                cpu_load = float(metric.get("cpu_load_5min", 0))
                cpu_usage = metric.get("cpu_usage_percent")
                swap_percentage = metric.get("swap_percentage", 0) or 0

                cpu_high = (float(cpu_usage) > 85) if cpu_usage is not None else (cpu_load > 5)

                # Check if server is offline (no data in last 15 minutes)
                timestamp = metric.get("timestamp")
                if (
                    timestamp and (datetime.now() - timestamp).total_seconds() > 900
                ):  # 15 minutes
                    offline_servers += 1
                elif ram_percentage > 90 or disk_percentage > 90 or cpu_high or swap_percentage > 90:
                    warning_servers += 1
                else:
                    online_servers += 1

                # Accumulate totals
                total_cpu_load += cpu_load
                if cpu_usage is not None:
                    total_cpu_usage += float(cpu_usage)
                    cpu_usage_count += 1
                total_ram_usage += ram_percentage
                total_disk_usage += disk_percentage
                total_swap_usage += swap_percentage
                total_users += metric.get("logged_users", 0)
                total_rx_bytes += int(metric.get("net_rx_bytes") or 0)
                total_tx_bytes += int(metric.get("net_tx_bytes") or 0)

            # Calculate averages
            avg_cpu_load = total_cpu_load / total_servers if total_servers > 0 else 0
            avg_cpu_usage = total_cpu_usage / cpu_usage_count if cpu_usage_count > 0 else None
            avg_ram = total_ram_usage / total_servers if total_servers > 0 else 0
            avg_disk = total_disk_usage / total_servers if total_servers > 0 else 0
            avg_swap = total_swap_usage / total_servers if total_servers > 0 else 0

            # Get historical data for trends
            trend_query = """
            SELECT
                COUNT(DISTINCT server_name) as server_count,
                AVG(cpu_usage_percent) as avg_cpu_usage,
                AVG(cpu_load_5min) as avg_cpu_load,
                AVG(ram_percentage) as avg_ram
            FROM server_metrics
            WHERE timestamp > NOW() - INTERVAL '48 hours'
            AND timestamp <= NOW() - INTERVAL '24 hours'
            """

            cursor.execute(trend_query)
            prev_stats = cursor.fetchone()

            # Calculate trends
            server_trend = "stable"
            cpu_trend = "stable"
            ram_trend = "stable"

            if prev_stats and prev_stats[0]:
                if total_servers > prev_stats[0]:
                    server_trend = "up"
                elif total_servers < prev_stats[0]:
                    server_trend = "down"

                # Use cpu_usage_percent for trend if available, else load
                prev_cpu_usage = float(prev_stats[1]) if prev_stats[1] is not None else None
                prev_cpu_load = float(prev_stats[2]) if prev_stats[2] is not None else None
                prev_ram = float(prev_stats[3]) if prev_stats[3] is not None else None

                current_cpu = avg_cpu_usage if avg_cpu_usage is not None else avg_cpu_load
                prev_cpu = prev_cpu_usage if prev_cpu_usage is not None else prev_cpu_load

                if prev_cpu and current_cpu > prev_cpu * 1.1:
                    cpu_trend = "up"
                elif prev_cpu and current_cpu < prev_cpu * 0.9:
                    cpu_trend = "down"

                if prev_ram and avg_ram > prev_ram * 1.1:
                    ram_trend = "up"
                elif prev_ram and avg_ram < prev_ram * 0.9:
                    ram_trend = "down"

            overview_data = {
                "total_servers": total_servers,
                "online_servers": online_servers,
                "warning_servers": warning_servers,
                "offline_servers": offline_servers,
                "avg_cpu_load": round(avg_cpu_load, 1),
                "avg_cpu_usage": round(avg_cpu_usage, 1) if avg_cpu_usage is not None else None,
                "avg_ram_usage": round(avg_ram, 1),
                "avg_disk_usage": round(avg_disk, 1),
                "avg_swap_usage": round(avg_swap, 1),
                "total_net_rx_bytes": total_rx_bytes,
                "total_net_tx_bytes": total_tx_bytes,
                "total_active_users": total_users,
                "uptime_percentage": round((online_servers / total_servers * 100), 1)
                if total_servers > 0
                else 0,
                "trends": {"servers": server_trend, "cpu": cpu_trend, "ram": ram_trend},
            }

            return jsonify({"success": True, "data": overview_data})

        except Exception as e:
            logger.error(f"Error fetching system overview: {e}")
            return jsonify({"success": False, "error": str(e)}), 500
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    # ==========================================
    # Error Handlers
    # ==========================================

    @app.errorhandler(404)
    def not_found_error(error):
        """Custom 404 page"""
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Custom 500 page"""
        logger.error(f"Internal server error: {error}")
        return render_template('errors/500.html'), 500

    logger.info("Unified Flask Dashboard Application initialized successfully")
    return app


# Create the application instance
app = create_app()


if __name__ == '__main__':
    logger.info("Starting Khalifa University Server Monitoring Dashboard...")
    logger.info(f"Debug mode: {app.config['DEBUG']}")
    logger.info("Combined API + Frontend on single port")
    app.run(
        debug=app.config['DEBUG'],
        host='0.0.0.0',
        port=5000  # Unified port for both API and frontend
    )
