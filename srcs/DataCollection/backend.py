#!/usr/bin/env python3
import subprocess
import psycopg2
import logging
from typing import Dict, List
import os
from dotenv import load_dotenv
import time
from parsers import DISK_NOT_COLLECTED, ParseError, parse_monitoring_data, parse_top_users
from rates import DISK_COUNTERS, NETWORK_COUNTERS, disk_rates, network_rates
from license_parser import match_server, parse_license_report

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
# Per-user history keeps only rows where the account was doing something
HISTORY_MIN_CPU: float = 5.0  # percent of one CPU
HISTORY_MIN_RSS_KB: int = 1024 * 1024  # 1 GiB
HISTORY_MIN_IO_BPS: int = 1024 * 1024  # 1 MiB/s
RETENTION_TABLES = ["server_metrics", "top_users", "top_users_history",
                    "server_filesystems", "server_disk_io", "server_network",
                    "license_snapshots", "license_usage_history", "license_checkouts",
                    "server_services"]
# Services whose state is checked on every server (space separated)
MONITORED_SERVICES: str = os.getenv("MONITORED_SERVICES", "sshd crond")
LICENSE_TIMEOUT_SECONDS: int = 90
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

# pg_advisory_lock key serialising init_db across concurrent cron jobs
SCHEMA_LOCK_ID = 7_301_001

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
				net_interface VARCHAR(64),
				procs_running INT,
				procs_blocked INT,
				procs_zombie INT,
				psi_cpu_some_avg60 NUMERIC(6,2),
				psi_memory_some_avg60 NUMERIC(6,2),
				psi_memory_full_avg60 NUMERIC(6,2),
				psi_io_some_avg60 NUMERIC(6,2),
				psi_io_full_avg60 NUMERIC(6,2)
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
        "ALTER TABLE server_metrics ADD COLUMN IF NOT EXISTS procs_running INT",
        "ALTER TABLE server_metrics ADD COLUMN IF NOT EXISTS procs_blocked INT",
        "ALTER TABLE server_metrics ADD COLUMN IF NOT EXISTS procs_zombie INT",
        "ALTER TABLE server_metrics ADD COLUMN IF NOT EXISTS psi_cpu_some_avg60 NUMERIC(6,2)",
        "ALTER TABLE server_metrics ADD COLUMN IF NOT EXISTS psi_memory_some_avg60 NUMERIC(6,2)",
        "ALTER TABLE server_metrics ADD COLUMN IF NOT EXISTS psi_memory_full_avg60 NUMERIC(6,2)",
        "ALTER TABLE server_metrics ADD COLUMN IF NOT EXISTS psi_io_some_avg60 NUMERIC(6,2)",
        "ALTER TABLE server_metrics ADD COLUMN IF NOT EXISTS psi_io_full_avg60 NUMERIC(6,2)",
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

    # Snapshot tables written once per collection run. Disk I/O and network
    # keep the raw kernel counters plus rates averaged since the previous run.
    detail_tables = [
        """
		CREATE TABLE IF NOT EXISTS server_filesystems (
			id BIGSERIAL PRIMARY KEY,
			timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			server_name VARCHAR(255),
			mount_point TEXT,
			fstype VARCHAR(32),
			source TEXT,
			size_bytes BIGINT,
			used_bytes BIGINT,
			avail_bytes BIGINT,
			use_percent NUMERIC(5,1),
			inodes_total BIGINT,
			inodes_used BIGINT,
			inode_percent NUMERIC(5,1)
		)""",
        """
		CREATE TABLE IF NOT EXISTS server_disk_io (
			id BIGSERIAL PRIMARY KEY,
			timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			server_name VARCHAR(255),
			device VARCHAR(64),
			name VARCHAR(255),
			reads BIGINT, sectors_read BIGINT, ms_reading BIGINT,
			writes BIGINT, sectors_written BIGINT, ms_writing BIGINT, ms_doing_io BIGINT,
			read_bps BIGINT,
			write_bps BIGINT,
			read_iops NUMERIC(12,2),
			write_iops NUMERIC(12,2),
			util_percent NUMERIC(5,1),
			await_ms NUMERIC(12,2)
		)""",
        """
		CREATE TABLE IF NOT EXISTS server_network (
			id BIGSERIAL PRIMARY KEY,
			timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			server_name VARCHAR(255),
			interface VARCHAR(64),
			rx_bytes BIGINT, tx_bytes BIGINT, rx_packets BIGINT, tx_packets BIGINT,
			rx_errors BIGINT, tx_errors BIGINT, rx_dropped BIGINT, tx_dropped BIGINT,
			rx_bps BIGINT,
			tx_bps BIGINT,
			rx_errors_delta BIGINT,
			tx_errors_delta BIGINT,
			rx_dropped_delta BIGINT,
			tx_dropped_delta BIGINT
		)""",
        # top_users keeps only the latest row per account; this keeps who was
        # active over time (rows below the HISTORY_MIN_* thresholds are skipped)
        """
		CREATE TABLE IF NOT EXISTS top_users_history (
			id BIGSERIAL PRIMARY KEY,
			timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			server_name VARCHAR(255),
			uid BIGINT,
			username VARCHAR(255),
			cpu NUMERIC(9,2),
			mem NUMERIC(7,2),
			rss_kb BIGINT,
			process_count INT,
			top_process VARCHAR(255),
			io_read_bps BIGINT,
			io_write_bps BIGINT
		)""",
        # monitored = requested via MONITORED_SERVICES; otherwise another failed unit
        """
		CREATE TABLE IF NOT EXISTS server_services (
			id BIGSERIAL PRIMARY KEY,
			timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			server_name VARCHAR(255),
			service VARCHAR(255),
			state VARCHAR(16),
			monitored BOOLEAN
		)""",
        "CREATE INDEX IF NOT EXISTS idx_server_services_server_time ON server_services (server_name, timestamp)",
        "CREATE INDEX IF NOT EXISTS idx_server_metrics_server_time ON server_metrics (server_name, timestamp)",
        "CREATE INDEX IF NOT EXISTS idx_server_filesystems_server_time ON server_filesystems (server_name, timestamp)",
        "CREATE INDEX IF NOT EXISTS idx_server_disk_io_device_time ON server_disk_io (server_name, device, timestamp)",
        "CREATE INDEX IF NOT EXISTS idx_server_network_iface_time ON server_network (server_name, interface, timestamp)",
        "CREATE INDEX IF NOT EXISTS idx_top_users_history_user_time ON top_users_history (username, timestamp)",
        "CREATE INDEX IF NOT EXISTS idx_top_users_history_server_time ON top_users_history (server_name, timestamp)",
    ]

    # License pools are queried once (not per compute server). A failed query
    # is recorded as a failed snapshot and never overwrites the last good values.
    detail_tables += [
        """
		CREATE TABLE IF NOT EXISTS license_snapshots (
			id BIGSERIAL PRIMARY KEY,
			timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			vendor VARCHAR(32),
			endpoint TEXT,
			status VARCHAR(16),
			daemon_status VARCHAR(64),
			error TEXT,
			features_total INT,
			features_counted INT,
			features_error INT,
			licenses_in_use INT,
			query_host VARCHAR(255)
		)""",
        # Current state per feature; observed_at = last snapshot that reported it
        """
		CREATE TABLE IF NOT EXISTS license_features (
			vendor VARCHAR(32),
			endpoint TEXT,
			feature VARCHAR(255),
			issued INT,
			in_use INT,
			error TEXT,
			version VARCHAR(64),
			expiry VARCHAR(32),
			observed_at TIMESTAMP,
			PRIMARY KEY (vendor, endpoint, feature)
		)""",
        """
		CREATE TABLE IF NOT EXISTS license_usage_history (
			id BIGSERIAL PRIMARY KEY,
			timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			snapshot_id BIGINT REFERENCES license_snapshots(id) ON DELETE CASCADE,
			vendor VARCHAR(32),
			feature VARCHAR(255),
			issued INT,
			in_use INT
		)""",
        # start_raw is lmstat's text (no year); start_at is resolved, NULL if ambiguous.
        # server_name is the monitored server matching client_host, if any.
        """
		CREATE TABLE IF NOT EXISTS license_checkouts (
			id BIGSERIAL PRIMARY KEY,
			timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			snapshot_id BIGINT REFERENCES license_snapshots(id) ON DELETE CASCADE,
			vendor VARCHAR(32),
			feature VARCHAR(255),
			username VARCHAR(255),
			client_host VARCHAR(255),
			server_name VARCHAR(255),
			display VARCHAR(255),
			version VARCHAR(64),
			server_host VARCHAR(255),
			server_port INT,
			handle BIGINT,
			start_raw VARCHAR(64),
			start_at TIMESTAMP,
			licenses INT
		)""",
        "CREATE INDEX IF NOT EXISTS idx_license_snapshots_vendor_time ON license_snapshots (vendor, timestamp)",
        "CREATE INDEX IF NOT EXISTS idx_license_usage_feature_time ON license_usage_history (feature, timestamp)",
        "CREATE INDEX IF NOT EXISTS idx_license_checkouts_snapshot ON license_checkouts (snapshot_id)",
        "CREATE INDEX IF NOT EXISTS idx_license_checkouts_user_time ON license_checkouts (username, timestamp)",
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

    # Not `with conn:` — since psycopg2 2.9 that opens a transaction even in
    # autocommit mode, and one failed migration would then abort the rest.
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        conn.autocommit = True
        with conn.cursor() as cursor:
            # Jobs start together (metrics + licenses); concurrent DDL deadlocks
            cursor.execute("SELECT pg_advisory_lock(%s)", (SCHEMA_LOCK_ID,))
            logger.info("Initializing database tables")
            cursor.execute(create_table_query)
            cursor.execute(create_table_query_2)
            for statement in detail_tables:
                cursor.execute(statement)
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
    finally:
        conn.close()  # also releases the advisory lock


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


def run_remote_script(server: Dict, script: str, args: List[str], timeout: int,
                      accept_status=(0,)) -> str:
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

    if result.returncode not in accept_status:
        reason = SSH_EXIT_REASONS.get(result.returncode, f"exit status {result.returncode}")
        # Login banners can be long; the last lines carry the actual error
        stderr_tail = " | ".join(result.stderr.strip().splitlines()[-3:])
        raise CollectionError(f"{script} on {server['name']}: {reason}. stderr: {stderr_tail}")
    return result.stdout


def run_monitoring_script(server: Dict) -> Dict:
    """Collect host metrics from one server."""
    output = run_remote_script(server, "mini_monitering.sh", ["--kv", "--services", MONITORED_SERVICES],
                               METRICS_TIMEOUT_SECONDS)
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
		cpu_iowait_percent, cpu_steal_percent, ram_available_mb, net_interface,
		procs_running, procs_blocked, procs_zombie, psi_cpu_some_avg60, psi_memory_some_avg60,
		psi_memory_full_avg60, psi_io_some_avg60, psi_io_full_avg60
	) VALUES (
		%(server_name)s, %(architecture)s, %(operating_system)s, %(physical_cpus)s, %(virtual_cpus)s,
		%(ram_used)s, %(ram_total)s, %(ram_percentage)s, %(disk_used)s, %(disk_total)s,
		%(disk_percentage)s, %(cpu_load_1min)s, %(cpu_load_5min)s, %(cpu_load_15min)s,
		%(last_boot)s, %(tcp_connections)s, %(logged_users)s, %(active_vnc_users)s, %(active_ssh_users)s,
		%(cpu_usage_percent)s, %(swap_used_mb)s, %(swap_total_mb)s, %(swap_percentage)s,
		%(net_rx_bytes)s, %(net_tx_bytes)s,
		%(cpu_iowait_percent)s, %(cpu_steal_percent)s, %(ram_available_mb)s, %(net_interface)s,
		%(procs_running)s, %(procs_blocked)s, %(procs_zombie)s, %(psi_cpu_some_avg60)s, %(psi_memory_some_avg60)s,
		%(psi_memory_full_avg60)s, %(psi_io_some_avg60)s, %(psi_io_full_avg60)s
	)
	"""

    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cursor:
                cursor.execute(insert_query, metrics)
                store_filesystems(cursor, metrics["server_name"], metrics.get("filesystems", []))
                for svc in metrics.get("services", []):
                    cursor.execute(
                        "INSERT INTO server_services (server_name, service, state, monitored) VALUES (%s, %s, %s, %s)",
                        (metrics["server_name"], svc["service"], svc["state"], bool(svc["monitored"])),
                    )
                store_counter_rows(cursor, metrics["server_name"], "server_disk_io", "device",
                                   ["name"], DISK_COUNTERS, disk_rates, metrics.get("block_devices", []))
                store_counter_rows(cursor, metrics["server_name"], "server_network", "interface",
                                   [], NETWORK_COUNTERS, network_rates, metrics.get("network", []))
                conn.commit()
        logger.info(
            f"Successfully stored metrics in database for {metrics['server_name']}"
        )
    except Exception as e:
        logger.error(
            f"Database error storing metrics for {metrics['server_name']}: {e}"
        )
        raise


def store_filesystems(cursor, server_name: str, filesystems: List[Dict]):
    """Append this run's per-mount capacity rows."""
    for fs in filesystems:
        cursor.execute("""
			INSERT INTO server_filesystems (server_name, mount_point, fstype, source, size_bytes,
				used_bytes, avail_bytes, use_percent, inodes_total, inodes_used, inode_percent)
			VALUES (%(server_name)s, %(mount_point)s, %(fstype)s, %(source)s, %(size_bytes)s,
				%(used_bytes)s, %(avail_bytes)s, %(use_percent)s, %(inodes_total)s, %(inodes_used)s,
				%(inode_percent)s)
		""", dict(fs, server_name=server_name))


def store_counter_rows(cursor, server_name: str, table: str, key: str, labels: List[str],
                       counters: List[str], rate_fn, rows: List[Dict]):
    """Append counter rows, with rates computed against each key's previous row.

    `table`, `key`, `labels` and `counters` are code constants, never user input.
    """
    if not rows:
        return
    cursor.execute(f"""
		SELECT DISTINCT ON ({key}) {key}, {", ".join(counters)},
			EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - timestamp))
		FROM {table}
		WHERE server_name = %s AND timestamp > CURRENT_TIMESTAMP - INTERVAL '1 day'
		ORDER BY {key}, timestamp DESC
	""", (server_name,))
    previous = {}
    for row in cursor.fetchall():
        previous[row[0]] = (dict(zip(counters, row[1:-1])), float(row[-1]))

    for row in rows:
        prev, elapsed = previous.get(row[key], (None, None))
        values = dict(row, **rate_fn(prev, row, elapsed), server_name=server_name)
        columns = ["server_name", key, *labels, *counters, *rate_fn(None, row, None).keys()]
        cursor.execute(
            f"INSERT INTO {table} ({', '.join(columns)}) "
            f"VALUES ({', '.join(f'%({c})s' for c in columns)})",
            values,
        )


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
                    if (row["cpu"] >= HISTORY_MIN_CPU or row["rss_kb"] >= HISTORY_MIN_RSS_KB
                            or (row["io_read_bps"] or 0) + (row["io_write_bps"] or 0) >= HISTORY_MIN_IO_BPS):
                        cursor.execute("""
							INSERT INTO top_users_history (server_name, uid, username, cpu, mem, rss_kb,
								process_count, top_process, io_read_bps, io_write_bps)
							VALUES (%(server_name)s, %(uid)s, %(user)s, %(cpu)s, %(mem)s, %(rss_kb)s,
								%(process_count)s, %(top_process)s, %(io_read_bps)s, %(io_write_bps)s)
						""", row)
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


def read_license_config() -> Dict:
    """License query settings; empty dict when license collection is not configured.

    LICENSE_QUERY_SERVER   name of a monitored server (SERVER{n}_NAME) with the vendor
                           tools installed; the report runs there over SSH
    LICENSE_CADENCE_SERVER / LICENSE_SYNOPSYS_SERVER   port@host specs
    LICENSE_CADENCE_LMUTIL / LICENSE_SYNOPSYS_LMUTIL   absolute lmutil paths on that server
    """
    host = os.getenv("LICENSE_QUERY_SERVER")
    if not host:
        return {}
    options = {
        "--cadence-server": os.getenv("LICENSE_CADENCE_SERVER"),
        "--synopsys-server": os.getenv("LICENSE_SYNOPSYS_SERVER"),
        "--cadence-lmutil": os.getenv("LICENSE_CADENCE_LMUTIL"),
        "--synopsys-lmutil": os.getenv("LICENSE_SYNOPSYS_LMUTIL"),
    }
    args = []
    for option, value in options.items():
        if value:
            args += [option, value]
    return {"host": host, "args": args}


def collect_licenses() -> bool:
    """Query the license servers once and store one snapshot per vendor."""
    config = read_license_config()
    if not config:
        logger.info("License collection not configured (LICENSE_QUERY_SERVER unset); skipping")
        return True
    servers = readServerList()
    query_server = next((s for s in servers if s["name"] == config["host"]), None)
    if query_server is None:
        logger.error(f"LICENSE_QUERY_SERVER={config['host']} is not one of the configured servers")
        return False
    try:
        # Exit 1 = a vendor query reported errors; the parser judges each vendor's status
        report = run_remote_script(query_server, "LicenseUsage.sh", config["args"],
                                   LICENSE_TIMEOUT_SECONDS, accept_status=(0, 1))
    except CollectionError as e:
        logger.error(f"License query failed: {e}")
        store_failed_license_query(config["host"], str(e))
        return False

    snapshots = parse_license_report(report)
    if not snapshots:
        logger.error("License report contained no vendor sections")
        store_failed_license_query(config["host"], "report contained no vendor sections")
        return False
    store_license_snapshots(snapshots, servers, config["host"])
    for snap in snapshots:
        log = logger.info if snap["status"] == "ok" else logger.warning
        log(f"License {snap['vendor']}: {snap['status']}, "
            f"{sum(f['in_use'] or 0 for f in snap['features'])} in use, "
            f"{len(snap['checkouts'])} checkouts" + (f" ({snap['error']})" if snap["error"] else ""))
    return any(s["status"] != "failed" for s in snapshots)


def store_failed_license_query(query_host: str, error: str):
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO license_snapshots (vendor, status, error, query_host) VALUES ('all', 'failed', %s, %s)",
                (error[:2000], query_host),
            )


def store_license_snapshots(snapshots: List[Dict], servers: List[Dict], query_host: str):
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cursor:
            for snap in snapshots:
                features = snap["features"]
                cursor.execute("""
					INSERT INTO license_snapshots (vendor, endpoint, status, daemon_status, error,
						features_total, features_counted, features_error, licenses_in_use, query_host)
					VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
				""", (snap["vendor"], snap["endpoint"], snap["status"], snap["daemon_status"],
                      snap["error"], len(features),
                      sum(f["in_use"] is not None for f in features),
                      sum(bool(f["error"]) for f in features),
                      sum(f["in_use"] or 0 for f in features), query_host))
                snapshot_id = cursor.fetchone()[0]
                if snap["status"] == "failed":
                    continue  # keep the last good feature state

                for f in features:
                    cursor.execute("""
						INSERT INTO license_features (vendor, endpoint, feature, issued, in_use, error,
							version, expiry, observed_at)
						VALUES (%(vendor)s, %(endpoint)s, %(feature)s, %(issued)s, %(in_use)s, %(error)s,
							%(version)s, %(expiry)s, CURRENT_TIMESTAMP)
						ON CONFLICT (vendor, endpoint, feature) DO UPDATE SET
							issued = EXCLUDED.issued, in_use = EXCLUDED.in_use, error = EXCLUDED.error,
							version = COALESCE(EXCLUDED.version, license_features.version),
							expiry = COALESCE(EXCLUDED.expiry, license_features.expiry),
							observed_at = EXCLUDED.observed_at
					""", dict(f, vendor=snap["vendor"], endpoint=snap["endpoint"]))
                    if f["in_use"]:
                        cursor.execute("""
							INSERT INTO license_usage_history (snapshot_id, vendor, feature, issued, in_use)
							VALUES (%s, %s, %s, %s, %s)
						""", (snapshot_id, snap["vendor"], f["feature"], f["issued"], f["in_use"]))
                # Features no longer served by this endpoint
                cursor.execute("""
					DELETE FROM license_features WHERE vendor = %s AND endpoint = %s
					AND observed_at < CURRENT_TIMESTAMP - INTERVAL '7 days'
				""", (snap["vendor"], snap["endpoint"]))

                for c in snap["checkouts"]:
                    cursor.execute("""
						INSERT INTO license_checkouts (snapshot_id, vendor, feature, username, client_host,
							server_name, display, version, server_host, server_port, handle,
							start_raw, start_at, licenses)
						VALUES (%(snapshot_id)s, %(vendor)s, %(feature)s, %(username)s, %(client_host)s,
							%(server_name)s, %(display)s, %(version)s, %(server_host)s, %(server_port)s,
							%(handle)s, %(start_raw)s, %(start_at)s, %(licenses)s)
					""", dict(c, snapshot_id=snapshot_id, vendor=snap["vendor"],
                              server_name=match_server(c["client_host"], servers)))
            conn.commit()
    logger.info("Stored license snapshots")


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
                deleted = {}
                for table in RETENTION_TABLES:
                    cursor.execute(
                        f"DELETE FROM {table} WHERE timestamp < NOW() - %s * INTERVAL '1 day'",
                        (data_retention_days,),
                    )
                    deleted[table] = cursor.rowcount
                conn.commit()

                logger.info("Data retention cleanup completed:")
                for table, count in deleted.items():
                    logger.info(f"  - Removed {count} {table} records")

                if any(deleted.values()):
                    # Run VACUUM to reclaim disk space
                    conn.autocommit = True
                    cursor.execute(f"VACUUM ANALYZE {', '.join(RETENTION_TABLES)}")
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

    if os.getenv("LICENSES_ONLY") == "true":
        # License snapshot only (scheduled separately from host metrics)
        try:
            init_db()
            exit(0 if collect_licenses() else 1)
        except Exception as e:
            logger.error(f"License collection failed: {e}", exc_info=True)
            exit(1)

    elif os.getenv("CLEANUP_ONLY") == "true":
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
