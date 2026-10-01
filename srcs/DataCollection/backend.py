#!/usr/bin/env python3
import subprocess
import psycopg2
import logging
from typing import Dict, List
import os
from dotenv import load_dotenv
import time
from parsers import DISK_NOT_COLLECTED, ParseError, parse_monitoring_data, parse_top_users

RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[0;33m"
BLUE = "\033[0;34m"
PURPLE = "\033[0;35m"
CYAN = "\033[0;36m"
NC = "\033[0m"  # No Color

load_dotenv(".env")

data_collection_interval: int = 15  # in minutes (only used in continuous mode)
user_disk_data_interval: int = 1 * int(
    60 * 24 / data_collection_interval
)  # 1 time a day (only used in continuous mode)
data_retention_days: int = 90  # 3 months data retention
retention_cleanup_interval: int = 7 * int(
    60 * 24 / data_collection_interval
)  # Run cleanup weekly (only used in continuous mode)

# Deadlines for one remote script run (SSH connect is separately limited to 10 s)
METRICS_TIMEOUT_SECONDS: int = 90
TOP_USERS_TIMEOUT_SECONDS: int = 300
# Disk scans are low priority and limited per account on the remote side
DISK_SCAN_TIMEOUT_PER_USER: int = int(os.getenv("DISK_SCAN_TIMEOUT_PER_USER", "900"))
DISK_SCAN_TIMEOUT_SECONDS: int = int(os.getenv("DISK_SCAN_TIMEOUT_SECONDS", str(4 * 3600)))

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Database configuration
DB_CONFIG = {
    "host": "postgres",
    "user": "postgres",
    "password": os.getenv("POSTGRES_PASSWORD"),
    "database": "server_db",
}


def init_db():
    """Initialize the PostgreSQL database and create necessary tables if they do not exist."""
    create_table_query = """
		CREATE TABLE IF NOT EXISTS server_metrics (
				id BIGSERIAL PRIMARY KEY,
				timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
				server_name VARCHAR(255),
				architecture VARCHAR(255),
				operating_system VARCHAR(255),
				physical_cpus INT,
				virtual_cpus INT,
				ram_used VARCHAR(30),
				ram_total VARCHAR(30),
				ram_percentage INT,
				disk_used VARCHAR(30),
				disk_total VARCHAR(30),
				disk_percentage INT,
				cpu_load_1min NUMERIC(8,2),
				cpu_load_5min NUMERIC(8,2),
				cpu_load_15min NUMERIC(8,2),
				last_boot VARCHAR(255),
				tcp_connections INT,
				logged_users INT,
				active_vnc_users INT,
				active_ssh_users INT,
				cpu_usage_percent NUMERIC(5,2) DEFAULT NULL,
				swap_used_mb INT DEFAULT 0,
				swap_total_mb INT DEFAULT 0,
				swap_percentage INT DEFAULT 0,
				net_rx_bytes BIGINT DEFAULT 0,
				net_tx_bytes BIGINT DEFAULT 0,
				cpu_iowait_percent NUMERIC(5,2),
				cpu_steal_percent NUMERIC(5,2),
				ram_available_mb INT,
				net_interface VARCHAR(64)
		)
	"""

    # cpu is percent of ONE logical CPU (400 = four cores busy), measured over a
    # short sample. disk is allocated GiB, NULL when unknown; disk_collected_at
    # records when it was last measured. timestamp is the last observation.
    create_table_query_2 = """
		CREATE TABLE IF NOT EXISTS top_users (
			id BIGSERIAL PRIMARY KEY,
			timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			server_name VARCHAR(255),
			username VARCHAR(255),
			cpu NUMERIC(9,2),
			mem NUMERIC(7,2),
			disk NUMERIC(12,2),
			process_count INT DEFAULT 0,
			top_process VARCHAR(255) DEFAULT NULL,
			last_login TIMESTAMP DEFAULT NULL,
			full_name VARCHAR(255) DEFAULT NULL,
			io_read_bytes BIGINT,
			io_write_bytes BIGINT,
			uid BIGINT,
			rss_kb BIGINT,
			io_read_bps BIGINT,
			io_write_bps BIGINT,
			disk_collected_at TIMESTAMP,
			UNIQUE (server_name, username)
		)
	"""

    # Migration: add new columns to existing tables if they don't exist yet
    migration_queries = [
        "ALTER TABLE server_metrics ADD COLUMN IF NOT EXISTS cpu_usage_percent DECIMAL(5,2) DEFAULT NULL",
        "ALTER TABLE server_metrics ADD COLUMN IF NOT EXISTS swap_used_mb INT DEFAULT 0",
        "ALTER TABLE server_metrics ADD COLUMN IF NOT EXISTS swap_total_mb INT DEFAULT 0",
        "ALTER TABLE server_metrics ADD COLUMN IF NOT EXISTS swap_percentage INT DEFAULT 0",
        "ALTER TABLE server_metrics ADD COLUMN IF NOT EXISTS net_rx_bytes BIGINT DEFAULT 0",
        "ALTER TABLE server_metrics ADD COLUMN IF NOT EXISTS net_tx_bytes BIGINT DEFAULT 0",
        "ALTER TABLE server_metrics ADD COLUMN IF NOT EXISTS cpu_iowait_percent NUMERIC(5,2)",
        "ALTER TABLE server_metrics ADD COLUMN IF NOT EXISTS cpu_steal_percent NUMERIC(5,2)",
        "ALTER TABLE server_metrics ADD COLUMN IF NOT EXISTS ram_available_mb INT",
        "ALTER TABLE server_metrics ADD COLUMN IF NOT EXISTS net_interface VARCHAR(64)",
        "ALTER TABLE top_users ADD COLUMN IF NOT EXISTS io_read_bytes BIGINT DEFAULT 0",
        "ALTER TABLE top_users ADD COLUMN IF NOT EXISTS io_write_bytes BIGINT DEFAULT 0",
        "ALTER TABLE top_users ADD COLUMN IF NOT EXISTS uid BIGINT",
        "ALTER TABLE top_users ADD COLUMN IF NOT EXISTS rss_kb BIGINT",
        "ALTER TABLE top_users ADD COLUMN IF NOT EXISTS io_read_bps BIGINT",
        "ALTER TABLE top_users ADD COLUMN IF NOT EXISTS io_write_bps BIGINT",
        "ALTER TABLE top_users ADD COLUMN IF NOT EXISTS disk_collected_at TIMESTAMP",
        # Unknown readings are NULL, not 0
        "ALTER TABLE top_users ALTER COLUMN disk DROP DEFAULT",
        "ALTER TABLE top_users ALTER COLUMN io_read_bytes DROP DEFAULT",
        "ALTER TABLE top_users ALTER COLUMN io_write_bytes DROP DEFAULT",
    ]

    # Widen numeric columns that overflowed at 999.99 (table, column, precision)
    widen_columns = [
        ("server_metrics", "cpu_load_1min", 8),
        ("server_metrics", "cpu_load_5min", 8),
        ("server_metrics", "cpu_load_15min", 8),
        ("top_users", "cpu", 9),
        ("top_users", "mem", 7),
        ("top_users", "disk", 12),
    ]

    with psycopg2.connect(**DB_CONFIG) as conn:
        # Autocommit so one failed migration cannot abort the ones after it
        conn.autocommit = True
        with conn.cursor() as cursor:
            logger.info("Initializing database tables")
            cursor.execute(create_table_query)
            cursor.execute(create_table_query_2)
            for migration in migration_queries:
                try:
                    cursor.execute(migration)
                except Exception as e:
                    logger.warning(f"Migration skipped: {e}")
            for table, column, precision in widen_columns:
                cursor.execute(
                    "SELECT numeric_precision FROM information_schema.columns "
                    "WHERE table_name = %s AND column_name = %s",
                    (table, column),
                )
                row = cursor.fetchone()
                if row and row[0] is not None and row[0] < precision:
                    logger.info(f"Widening {table}.{column} to NUMERIC({precision},2)")
                    cursor.execute(
                        f"ALTER TABLE {table} ALTER COLUMN {column} TYPE NUMERIC({precision},2)"
                    )


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d] - %(message)s",
    datefmt="%d-%B-%Y %H:%M:%S",
)

# Create logger for this module
logger = logging.getLogger(__name__)


class CollectionError(Exception):
    """A remote script failed. The message never contains credentials."""


# Exit statuses from BashGetInfo.sh (ssh / sshpass)
SSH_EXIT_REASONS = {
    255: "SSH connection failed (host unreachable, refused or timed out)",
    5: "authentication failed (wrong password)",
    6: "host key verification failed",
}


def run_remote_script(server: Dict, script: str, args: List[str], timeout: int) -> str:
    """Run a local script on the server over SSH and return its stdout.

    Credentials are passed through the environment so they never appear in the
    process list, in exception text or in logs.
    """
    env = dict(os.environ)
    env.pop("SSHPASS", None)
    env.pop("SSH_KEY_FILE", None)
    if server.get("key_file"):
        env["SSH_KEY_FILE"] = server["key_file"]
    elif server.get("password"):
        env["SSHPASS"] = server["password"]

    command = [
        os.path.join(SCRIPT_DIR, "BashGetInfo.sh"),
        server["ip"],
        server["username"],
        os.path.join(SCRIPT_DIR, script),
        *args,
    ]
    logger.debug(f"Running {script} on {server['name']}")
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, env=env, timeout=timeout
        )
    except subprocess.TimeoutExpired:
        raise CollectionError(f"{script} on {server['name']} timed out after {timeout}s") from None

    if result.returncode != 0:
        reason = SSH_EXIT_REASONS.get(result.returncode, f"exit status {result.returncode}")
        # Login banners can be long; the last lines carry the actual error
        stderr_tail = " | ".join(result.stderr.strip().splitlines()[-3:])
        raise CollectionError(f"{script} on {server['name']}: {reason}. stderr: {stderr_tail}")
    return result.stdout


def run_monitoring_script(server: Dict) -> Dict:
    """Collect host metrics from one server."""
    output = run_remote_script(server, "mini_monitering.sh", ["--kv"], METRICS_TIMEOUT_SECONDS)
    return parse_monitoring_data(output)


def get_top_users(server: Dict, get_storage_usage: bool = False) -> Dict:
    """Collect per-account usage from one server, optionally with disk scans."""
    args = ["--no-headers"]
    timeout = TOP_USERS_TIMEOUT_SECONDS
    if get_storage_usage:
        args += ["--collect-disk", "--disk-timeout", str(DISK_SCAN_TIMEOUT_PER_USER)]
        timeout = DISK_SCAN_TIMEOUT_SECONDS
    output = run_remote_script(server, "TopUsers.sh", args, timeout)
    return parse_top_users(output)


def store_metrics(metrics: Dict):
    """Store the parsed metrics in the PostgreSQL database."""
    insert_query = """
	INSERT INTO server_metrics (
		server_name, architecture, operating_system, physical_cpus, virtual_cpus,
		ram_used, ram_total, ram_percentage, disk_used, disk_total,
		disk_percentage, cpu_load_1min, cpu_load_5min, cpu_load_15min,
		last_boot, tcp_connections, logged_users, active_vnc_users, active_ssh_users,
		cpu_usage_percent, swap_used_mb, swap_total_mb, swap_percentage,
		net_rx_bytes, net_tx_bytes,
		cpu_iowait_percent, cpu_steal_percent, ram_available_mb, net_interface
	) VALUES (
		%(server_name)s, %(architecture)s, %(operating_system)s, %(physical_cpus)s, %(virtual_cpus)s,
		%(ram_used)s, %(ram_total)s, %(ram_percentage)s, %(disk_used)s, %(disk_total)s,
		%(disk_percentage)s, %(cpu_load_1min)s, %(cpu_load_5min)s, %(cpu_load_15min)s,
		%(last_boot)s, %(tcp_connections)s, %(logged_users)s, %(active_vnc_users)s, %(active_ssh_users)s,
		%(cpu_usage_percent)s, %(swap_used_mb)s, %(swap_total_mb)s, %(swap_percentage)s,
		%(net_rx_bytes)s, %(net_tx_bytes)s,
		%(cpu_iowait_percent)s, %(cpu_steal_percent)s, %(ram_available_mb)s, %(net_interface)s
	)
	"""

    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cursor:
                cursor.execute(insert_query, metrics)
                conn.commit()
        logger.info(
            f"Successfully stored metrics in database for {metrics['server_name']}"
        )
    except Exception as e:
        logger.error(
            f"Database error storing metrics for {metrics['server_name']}: {e}"
        )
        raise


def store_top_users(server_name: str, top_users_dict: Dict):
    """Store the top users data in the PostgreSQL database.

    Every write refreshes `timestamp` (last observation). Disk is only replaced
    when this run measured it, so a skipped or timed-out scan keeps the old value.
    """
    top_users: List[Dict] = top_users_dict.get("top_users", [])
    usernames = [user["user"] for user in top_users]
    upsert_query = """
		INSERT INTO top_users (server_name, username, uid, cpu, mem, rss_kb, disk, disk_collected_at,
			process_count, top_process, last_login, full_name,
			io_read_bytes, io_write_bytes, io_read_bps, io_write_bps, timestamp)
		VALUES (%(server_name)s, %(user)s, %(uid)s, %(cpu)s, %(mem)s, %(rss_kb)s, %(disk)s,
			CASE WHEN %(disk_collected)s THEN CURRENT_TIMESTAMP END,
			%(process_count)s, %(top_process)s, %(last_login)s, %(full_name)s,
			%(io_read_bytes)s, %(io_write_bytes)s, %(io_read_bps)s, %(io_write_bps)s, CURRENT_TIMESTAMP)
		ON CONFLICT (server_name, username) DO UPDATE SET
			uid = EXCLUDED.uid,
			cpu = EXCLUDED.cpu,
			mem = EXCLUDED.mem,
			rss_kb = EXCLUDED.rss_kb,
			disk = CASE WHEN %(disk_collected)s THEN EXCLUDED.disk ELSE top_users.disk END,
			disk_collected_at = COALESCE(EXCLUDED.disk_collected_at, top_users.disk_collected_at),
			process_count = EXCLUDED.process_count,
			top_process = EXCLUDED.top_process,
			last_login = EXCLUDED.last_login,
			full_name = EXCLUDED.full_name,
			io_read_bytes = EXCLUDED.io_read_bytes,
			io_write_bytes = EXCLUDED.io_write_bytes,
			io_read_bps = EXCLUDED.io_read_bps,
			io_write_bps = EXCLUDED.io_write_bps,
			timestamp = EXCLUDED.timestamp
	"""
    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cursor:
                for user in top_users:
                    row = dict(user, server_name=server_name)
                    row["disk_collected"] = user["disk"] is not DISK_NOT_COLLECTED
                    if not row["disk_collected"]:
                        row["disk"] = None
                    cursor.execute(upsert_query, row)
                # Remove users not in the current top_users list
                if usernames:
                    delete_query = f"""
						DELETE FROM top_users WHERE server_name = %s AND username NOT IN ({", ".join(["%s"] * len(usernames))})
					"""
                    cursor.execute(delete_query, [server_name] + usernames)
                else:
                    delete_query = "DELETE FROM top_users WHERE server_name = %s"
                    cursor.execute(delete_query, (server_name,))
                conn.commit()
        logger.info(f"Successfully stored top users in database for {server_name}")
    except Exception as e:
        logger.error(f"Database error storing top users for {server_name}: {e}")
        raise


def readServerList() -> List[Dict]:
    """Read server configurations from environment variables."""
    servers = []
    for i in range(1, 10):
        server_name = os.getenv(f"SERVER{i}_NAME")
        if not server_name:
            continue
        logger.debug(f"Server {i} ({server_name}) found in environment variables")
        servers.append(
            {
                "name": server_name,
                "host": os.getenv(f"SERVER{i}_HOST"),
                "ip": os.getenv(f"SERVER{i}_IP"),
                "username": os.getenv(f"SERVER{i}_USERNAME"),
                "password": os.getenv(f"SERVER{i}_PASSWORD"),
                "key_file": os.getenv(f"SERVER{i}_KEY_FILE"),
            }
        )
    return servers


def cleanup_old_data():
    """Remove data older than the retention period from the database."""
    try:
        logger.info(
            f"Starting data retention cleanup (removing data older than {data_retention_days} days)"
        )

        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cursor:
                # Calculate the cutoff date
                cutoff_date = f"NOW() - INTERVAL '{data_retention_days} days'"

                # Clean up old server_metrics data
                delete_metrics_query = f"""
					DELETE FROM server_metrics
					WHERE timestamp < {cutoff_date}
				"""
                cursor.execute(delete_metrics_query)
                deleted_metrics = cursor.rowcount

                # Clean up old top_users data
                delete_users_query = f"""
					DELETE FROM top_users
					WHERE timestamp < {cutoff_date}
				"""
                cursor.execute(delete_users_query)
                deleted_users = cursor.rowcount

                conn.commit()

                logger.info("Data retention cleanup completed:")
                logger.info(f"  - Removed {deleted_metrics} server_metrics records")
                logger.info(f"  - Removed {deleted_users} top_users records")

                if deleted_metrics > 0 or deleted_users > 0:
                    # Run VACUUM to reclaim disk space
                    conn.autocommit = True
                    cursor.execute("VACUUM ANALYZE server_metrics, top_users")
                    conn.autocommit = False
                    logger.info("Database vacuum completed to reclaim disk space")

    except Exception as e:
        logger.error(f"Error during data retention cleanup: {e}")
        raise


def run_single_collection_cycle(collect_disk_usage=False, run_cleanup=False):
    """Run a single data collection cycle for all servers."""
    try:
        # Initialize the database
        init_db()
        logger.info("Database initialized successfully")

        # Get server list
        server_list = readServerList()
        if not server_list:
            logger.error("No servers found in environment variables. Exiting.")
            return False

        logger.info(f"Found {len(server_list)} servers to monitor:")
        for server in server_list:
            logger.info(f"  - {server['name']} ({server['ip']})")

        # Run data retention cleanup if requested
        if run_cleanup:
            logger.info("Running data retention cleanup...")
            try:
                cleanup_old_data()
            except Exception as e:
                logger.error(f"Data retention cleanup failed: {e}")

        # Collect data from all servers. Host metrics and per-user data are
        # stored independently so a slow or failing user scan keeps host data.
        success_count = 0
        for server in server_list:
            try:
                metrics = run_monitoring_script(server)
                metrics["server_name"] = server["name"]
                store_metrics(metrics)
                success_count += 1
            except (CollectionError, ParseError) as e:
                logger.error(f"Host metrics failed for {server['name']}: {e}")
                continue  # unreachable or broken: skip the per-user run as well
            except Exception as e:
                logger.error(f"Error storing host metrics for {server['name']}: {e}", exc_info=True)
                continue

            try:
                top_users = get_top_users(server, collect_disk_usage)
                store_top_users(server["name"], top_users)
                logger.info(f"Successfully collected data for {server['name']}")
            except (CollectionError, ParseError) as e:
                logger.error(f"Per-user data failed for {server['name']}: {e}")
            except Exception as e:
                logger.error(f"Error storing per-user data for {server['name']}: {e}", exc_info=True)

        logger.info(
            f"Collection cycle completed. Successfully processed {success_count}/{len(server_list)} servers."
        )
        return success_count > 0

    except Exception as e:
        logger.critical(f"Critical error in collection cycle: {e}")
        logger.debug("Collection cycle traceback:", exc_info=True)
        return False


def main_continuous():
    """Run in continuous mode with periodic data collection."""
    try:
        logger.info("=" * 50)
        logger.info("Starting DataCollection Backend Service (Continuous Mode)")
        logger.info(f"Data collection interval: {data_collection_interval} minutes")
        logger.info(
            f"User disk data collection interval: {user_disk_data_interval} cycles"
        )
        logger.info(f"Data retention period: {data_retention_days} days")
        logger.info(f"Retention cleanup interval: {retention_cleanup_interval} cycles")
        logger.info("=" * 50)

        disk_data_counter: int = 0
        cleanup_counter: int = 0

        # Run initial setup and cleanup
        run_single_collection_cycle(collect_disk_usage=False, run_cleanup=True)

        logger.info("Starting continuous monitoring loop...")
        while True:
            # Handle periodic tasks
            logger.debug(
                f"Starting monitoring cycle (disk data counter: {disk_data_counter}, cleanup counter: {cleanup_counter})"
            )

            # Determine if we should collect disk usage this cycle
            collect_disk_usage = disk_data_counter >= user_disk_data_interval
            if collect_disk_usage:
                disk_data_counter = 0
                logger.debug("This cycle will collect disk usage data for users")
            else:
                disk_data_counter += 1

            # Determine if we should run cleanup this cycle
            run_cleanup = cleanup_counter >= retention_cleanup_interval
            if run_cleanup:
                cleanup_counter = 0
            else:
                cleanup_counter += 1

            # Run collection cycle
            run_single_collection_cycle(
                collect_disk_usage=collect_disk_usage, run_cleanup=run_cleanup
            )

            logger.debug(
                f"Monitoring cycle completed. Sleeping for {data_collection_interval} minutes..."
            )
            time.sleep(60 * data_collection_interval)

    except Exception as e:
        logger.critical(f"Critical error in continuous mode: {e}")
        logger.debug("Continuous mode traceback:", exc_info=True)
        raise


def main_scheduled():
    """Run in scheduled mode for single execution."""
    logger.info("=" * 50)
    logger.info("Starting DataCollection Backend Service (Scheduled Mode)")
    logger.info(f"Data retention period: {data_retention_days} days")
    logger.info("=" * 50)

    # Determine what to do based on environment variables
    collect_disk_usage = os.getenv("COLLECT_DISK_USAGE", "false").lower() == "true"
    run_cleanup = os.getenv("RUN_CLEANUP", "false").lower() == "true"

    logger.info(
        f"Collection mode: disk_usage={collect_disk_usage}, cleanup={run_cleanup}"
    )

    # Run single collection cycle
    success = run_single_collection_cycle(
        collect_disk_usage=collect_disk_usage, run_cleanup=run_cleanup
    )

    if success:
        logger.info("Scheduled execution completed successfully.")
        return 0
    else:
        logger.error("Scheduled execution completed with errors.")
        return 1


if __name__ == "__main__":
    # Determine execution mode based on environment variables
    mode = os.getenv("EXECUTION_MODE", "continuous").lower()

    if os.getenv("CLEANUP_ONLY") == "true":
        # Legacy cleanup-only mode
        logger.info("Running in cleanup-only mode")
        try:
            init_db()
            cleanup_old_data()
            logger.info("Cleanup completed successfully. Exiting.")
            exit(0)
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            exit(1)

    elif mode == "scheduled":
        # Scheduled execution mode - runs once then exits
        exit_code = main_scheduled()
        exit(exit_code)

    elif mode == "continuous":
        # Continuous execution mode (default) - runs forever
        main_continuous()

    else:
        logger.error(
            f"Unknown execution mode: {mode}. Valid modes: continuous, scheduled"
        )
        exit(1)
