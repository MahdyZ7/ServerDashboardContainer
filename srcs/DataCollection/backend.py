#!/usr/bin/env python3
from math import ceil
import subprocess
import psycopg2
import logging
from typing import Dict, List
import os
from dotenv import load_dotenv
import time

RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[0;33m'
BLUE = '\033[0;34m'
PURPLE = '\033[0;35m'
CYAN = '\033[0;36m'
NC = '\033[0m'  # No Color

load_dotenv(".env")

data_collection_interval: int = 15 # in minutes (only used in continuous mode)
user_disk_data_interval: int =  1 * int(60 * 24 / data_collection_interval) # 1 time a day (only used in continuous mode)
data_retention_days: int = 90  # 3 months data retention
retention_cleanup_interval: int = 7 * int(60 * 24 / data_collection_interval)  # Run cleanup weekly (only used in continuous mode)

# Database configuration
DB_CONFIG = {
	'host': 'postgres',
	'user': 'postgres',
	'password': os.getenv("POSTGRES_PASSWORD"),
	'database': 'server_db'
}


def init_db():
	"""Initialize the PostgreSQL database and create necessary tables if they do not exist."""
	create_table_query = '''
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
				cpu_load_1min DECIMAL(5,2),
				cpu_load_5min DECIMAL(5,2),
				cpu_load_15min DECIMAL(5,2),
				last_boot VARCHAR(255),
				tcp_connections INT,
				logged_users INT,
				active_vnc_users INT,
				active_ssh_users INT
		)
	'''

	create_table_query_2 = '''
		CREATE TABLE IF NOT EXISTS top_users (
			id BIGSERIAL PRIMARY KEY,
			timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			server_name VARCHAR(255),
			username VARCHAR(255),
			cpu DECIMAL(5,2),
			mem DECIMAL(5,2),
			disk DECIMAL(5,2) DEFAULT 0,
			process_count INT DEFAULT 0,
			top_process VARCHAR(255) DEFAULT NULL,
			last_login TIMESTAMP DEFAULT NULL,
			full_name VARCHAR(255) DEFAULT NULL,
			UNIQUE (server_name, username)
		)
	'''
	with psycopg2.connect(**DB_CONFIG) as conn:
		with conn.cursor() as cursor:
			logger.info("Initializing database tables")
			cursor.execute(create_table_query)
			cursor.execute(create_table_query_2)
			conn.commit()


# Configure logging
logging.basicConfig(
	level=logging.INFO,
	format='[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d] - %(message)s',
	datefmt='%d-%B-%Y %H:%M:%S'
)

# Create logger for this module
logger = logging.getLogger(__name__)


def server_online(server: Dict) -> bool:
	"""Check if the server is online by pinging it."""
	try:
		logger.debug(f"Checking connectivity to server {server['name']} ({server['ip']})")
		command_string = ['ping', '-c', '1', '-w', '5', server['ip']]
		result = subprocess.run(
			command_string, capture_output=True, text=True, check=True)
		logger.debug(f"Server {server['name']} is online")
		return True
	except subprocess.CalledProcessError as e:
		logger.error(f"Server {server['name']} ({server['ip']}) is offline - ping failed: {e}")
		return False


def run_monitoring_script(server: Dict) -> str:
	"""Execute the bash monitoring script and return its output."""
	try:
		logger.debug(f"Running monitoring script for server {server['name']}")
		# Get the directory of the current script
		current_dir = os.path.dirname(os.path.abspath(__file__))
		script_path = os.path.join(current_dir, 'BashGetInfo.sh')
		command_string = [script_path, server['ip'], server['username'],
						  server['password'], "mini_monitering.sh", "--line-format"]
		# Make sure the script is executable
		os.chmod(script_path, 0o755)

		# Run the script
		result = subprocess.run(command_string,
								capture_output=True,
								text=True,
								check=True)
		logger.debug(f"Successfully retrieved monitoring data for {server['name']}")
		return result.stdout.strip()
	except subprocess.CalledProcessError as e:
		logger.error(f"Failed to run monitoring script for {server['name']}: {e}")
		if e.stderr:
			logger.error(f"Script stderr: {e.stderr}")
		raise


def get_top_users(server: Dict, get_storage_usage: bool = False) -> Dict:
	"""Get the top CPU and memory users on the server."""
	try:
		logger.debug(f"Getting top users for server {server['name']} (disk usage: {get_storage_usage})")
		# Get the directory of the current script
		current_dir = os.path.dirname(os.path.abspath(__file__))
		script_path = os.path.join(current_dir, 'BashGetInfo.sh')
		command_string = [script_path, server['ip'], server['username'],
						  server['password'], "TopUsers.sh", "--no-headers"]
		if get_storage_usage:
			command_string.append("--collect-disk")
		# Make sure the script is executable
		os.chmod(script_path, 0o755)

		# Run the script
		result = subprocess.run(command_string,
								capture_output=True,
								text=True,
								check=True)
		logger.debug(f"Successfully retrieved top users data for {server['name']}")
		return parse_top_users(result.stdout)
	except subprocess.CalledProcessError as e:
		logger.error(f"Failed to get top users for {server['name']}: {e}")
		if e.stderr:
			logger.error(f"TopUsers script stderr: {e.stderr}")
		raise


def parse_top_users(data: str) -> Dict:
	"""Parse the top users data from the monitoring script into a dictionary."""
	try:
		top_users = []
		for line in data.splitlines():
			if not line or line.strip() == '':
				continue
			user, cpu, mem, disk, procs, top_proc, last_login, full_name = line.split()
			top_users.append({
				'user': user,
				'cpu': float(cpu),
				'mem': float(mem),
				'disk': float(disk) if disk != 'nan' and disk != 'OFF' else 0,
				'process_count': int(procs),
				'top_process': top_proc if top_proc != 'nan' else None,
				'last_login': last_login,
				'full_name': full_name if full_name != 'nan' else None
			})
		return {'top_users': top_users}
	except Exception as e:
		logger.error(f"Failed to parse top users data: {e}")
		logger.debug(f"Raw data that failed to parse: {data}")
		raise


def parse_monitoring_data(data: str) -> Dict:
	"""Parse the CSV output from the monitoring script into a dictionary."""
	try:
		# Split the CSV data
		(arch, os_info, pcpu, vcpu, ram_ratio, ram_perc,
		 disk_ratio, disk_perc, cpu_load_1min, cpu_load_5min, cpu_load_15min,
		 last_boot, tcp, users, active_vnc_users, active_ssh_users) = data.split(',')

		# Parse RAM information
		ram_used, ram_total = ram_ratio.split('/')

		# Parse disk information
		disk_used, disk_total = disk_ratio.split('/')

		# Convert last_boot to datetime
		# last_boot_dt = datetime.strptime(last_boot, '%Y-%m-%d %H:%M')

		# Remove '%' from percentage values and convert to float
		disk_perc = int(disk_perc.strip('%'))
		ram_perc = int(ram_perc)

		return {
			'architecture': arch,
			'operating_system': os_info,
			'physical_cpus': int(pcpu),
			'virtual_cpus': int(vcpu),
			'ram_used': ram_used,
			'ram_total': ram_total,
			'ram_percentage': ram_perc,
			'disk_used': disk_used,
			'disk_total': disk_total,
			'disk_percentage': disk_perc,
			'cpu_load_1min': cpu_load_1min,
			'cpu_load_5min': cpu_load_5min,
			'cpu_load_15min': cpu_load_15min,
			'last_boot': last_boot,
			'tcp_connections': int(tcp),
			'logged_users': int(users),
			'active_vnc_users': int(active_vnc_users),
			'active_ssh_users': int(active_ssh_users)
		}
	except Exception as e:
		logger.error(f"Failed to parse monitoring data: {e}")
		logger.debug(f"Raw monitoring data that failed to parse: {data}")
		raise


def store_metrics(metrics: Dict):
	"""Store the parsed metrics in the PostgreSQL database."""
	insert_query = """
	INSERT INTO server_metrics (
		server_name, architecture, operating_system, physical_cpus, virtual_cpus,
		ram_used, ram_total, ram_percentage, disk_used, disk_total,
		disk_percentage, cpu_load_1min, cpu_load_5min, cpu_load_15min,
		last_boot, tcp_connections, logged_users, active_vnc_users, active_ssh_users
	) VALUES (
		%(server_name)s, %(architecture)s, %(operating_system)s, %(physical_cpus)s, %(virtual_cpus)s,
		%(ram_used)s, %(ram_total)s, %(ram_percentage)s, %(disk_used)s, %(disk_total)s,
		%(disk_percentage)s, %(cpu_load_1min)s, %(cpu_load_5min)s, %(cpu_load_15min)s,
		%(last_boot)s, %(tcp_connections)s, %(logged_users)s, %(active_vnc_users)s, %(active_ssh_users)s
	)
	"""

	try:
		with psycopg2.connect(**DB_CONFIG) as conn:
			with conn.cursor() as cursor:
				cursor.execute(insert_query, metrics)
				conn.commit()
		logger.info(f"Successfully stored metrics in database for {metrics['server_name']}")
	except Exception as e:
		logger.error(f"Database error storing metrics for {metrics['server_name']}: {e}")
		raise


def store_top_users(server_name: str, top_users_dict: Dict):
	"""Store the top users data in the PostgreSQL database."""
	top_users: List[Dict] = top_users_dict.get('top_users', [])
	usernames = [user['user'] for user in top_users]
	try:
		with psycopg2.connect(**DB_CONFIG) as conn:
			with conn.cursor() as cursor:
				for user in top_users:
					user['server_name'] = server_name
					if user['last_login'] == '--':
						user['last_login'] = None
					if user['disk'] == 0:
						insert_query = """
							INSERT INTO top_users (server_name, username, cpu, mem, disk, process_count, top_process, last_login, full_name)
							VALUES (%(server_name)s, %(user)s, %(cpu)s, %(mem)s, %(disk)s, %(process_count)s, %(top_process)s, %(last_login)s, %(full_name)s)
							ON CONFLICT (server_name, username) DO UPDATE SET
								cpu = EXCLUDED.cpu,
								mem = EXCLUDED.mem,
								process_count = EXCLUDED.process_count,
								top_process = EXCLUDED.top_process,
								last_login = EXCLUDED.last_login,
								full_name = EXCLUDED.full_name
						"""
					else:
						insert_query = """
							INSERT INTO top_users (server_name, username, cpu, mem, disk, process_count, top_process, last_login, full_name)
							VALUES (%(server_name)s, %(user)s, %(cpu)s, %(mem)s, %(disk)s, %(process_count)s, %(top_process)s, %(last_login)s, %(full_name)s)
							ON CONFLICT (server_name, username) DO UPDATE SET
								cpu = EXCLUDED.cpu,
								mem = EXCLUDED.mem,
								disk = EXCLUDED.disk,
								process_count = EXCLUDED.process_count,
								top_process = EXCLUDED.top_process,
								last_login = EXCLUDED.last_login,
								full_name = EXCLUDED.full_name
						"""
					cursor.execute(insert_query, user)
				# Remove users not in the current top_users list
				if usernames:
					delete_query = f"""
						DELETE FROM top_users WHERE server_name = %s AND username NOT IN ({', '.join(['%s']*len(usernames))})
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
	for i in range(1, 8):
		server_name = os.getenv(f"SERVER{i}_NAME")
		if not server_name:
			continue
		logger.debug(f"Server {i} ({server_name}) found in environment variables")
		servers.append({
			'name': server_name,
			'host': os.getenv(f"SERVER{i}_HOST"),
			'ip': os.getenv(f"SERVER{i}_IP"),
			'username': os.getenv(f"SERVER{i}_USERNAME"),
			'password': os.getenv(f"SERVER{i}_PASSWORD")
		})
	return servers


def cleanup_old_data():
	"""Remove data older than the retention period from the database."""
	try:
		logger.info(f"Starting data retention cleanup (removing data older than {data_retention_days} days)")

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

				logger.info(f"Data retention cleanup completed:")
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

		# Collect data from all servers
		success_count = 0
		for server in server_list:
			if not server_online(server):
				logger.warning(f"Server {server['name']} is offline, skipping")
				continue

			try:
				# Run monitoring script and get output
				monitoring_output = run_monitoring_script(server)
				top_users = get_top_users(server, collect_disk_usage)

				# Parse the monitoring data
				metrics = parse_monitoring_data(monitoring_output)
				metrics['server_name'] = server['name']

				# Store in database
				store_metrics(metrics)
				store_top_users(server['name'], top_users)
				logger.info(f"Successfully collected data for {server['name']}")
				success_count += 1
			except Exception as e:
				logger.error(f"Error processing server {server['name']}: {e}")
				continue

		logger.info(f"Collection cycle completed. Successfully processed {success_count}/{len(server_list)} servers.")
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
		logger.info(f"User disk data collection interval: {user_disk_data_interval} cycles")
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
			logger.debug(f"Starting monitoring cycle (disk data counter: {disk_data_counter}, cleanup counter: {cleanup_counter})")

			# Determine if we should collect disk usage this cycle
			collect_disk_usage = (disk_data_counter >= user_disk_data_interval)
			if collect_disk_usage:
				disk_data_counter = 0
				logger.debug("This cycle will collect disk usage data for users")
			else:
				disk_data_counter += 1

			# Determine if we should run cleanup this cycle
			run_cleanup = (cleanup_counter >= retention_cleanup_interval)
			if run_cleanup:
				cleanup_counter = 0
			else:
				cleanup_counter += 1

			# Run collection cycle
			run_single_collection_cycle(collect_disk_usage=collect_disk_usage, run_cleanup=run_cleanup)

			logger.debug(f"Monitoring cycle completed. Sleeping for {data_collection_interval} minutes...")
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

	logger.info(f"Collection mode: disk_usage={collect_disk_usage}, cleanup={run_cleanup}")

	# Run single collection cycle
	success = run_single_collection_cycle(collect_disk_usage=collect_disk_usage, run_cleanup=run_cleanup)

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
		logger.error(f"Unknown execution mode: {mode}. Valid modes: continuous, scheduled")
		exit(1)
