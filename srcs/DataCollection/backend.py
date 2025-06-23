#!/usr/bin/env python3
import subprocess
import psycopg2
import logging
from typing import Dict, List
import os
from dotenv import load_dotenv
import time

load_dotenv(".env")

print("ASDASDASDASDASDASD")
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
			last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			full_Name VARCHAR(255) DEFAULT NULL
		)
	'''
	with psycopg2.connect(**DB_CONFIG) as conn:
		with conn.cursor() as cursor:
			logging.info("Initializing database")
			cursor.execute(create_table_query)
			cursor.execute(create_table_query_2)
			conn.commit()


# Configure logging
logging.basicConfig(
	level=logging.INFO,
	format='%(asctime)s - %(levelname)s - %(message)s'
)


def server_online(server: Dict) -> bool:
	"""Check if the server is online by pinging it."""
	try:
		# Run a simple command to check if the server is online
		command_string = ['ping', '-c', '1', '-w', '5', server['host']]
		result = subprocess.run(
			command_string, capture_output=True, text=True, check=True)
		return True
	except subprocess.CalledProcessError:
		logging.error(f"Server {server['host']} is offline")
		return False


def run_monitoring_script(server: Dict) -> str:
	"""Execute the bash monitoring script and return its output."""
	try:
		# Get the directory of the current script
		current_dir = os.path.dirname(os.path.abspath(__file__))
		script_path = os.path.join(current_dir, 'BashGetInfo.sh')
		command_string = [script_path, server['host'], server['username'],
						  server['password'], "mini_monitering.sh", "--line-format"]
		# Make sure the script is executable
		os.chmod(script_path, 0o755)

		# Run the script
		result = subprocess.run(command_string,
								capture_output=True,
								text=True,
								check=True)
		return result.stdout.strip()
	except subprocess.CalledProcessError as e:
		logging.error(
			f"Failed to run monitoring script for {server['host']}: {e}")
		raise


def get_top_users(server: Dict, get_storage_usage: bool = False) -> Dict:
	"""Get the top CPU and memory users on the server."""
	try:
		# Get the directory of the current script
		current_dir = os.path.dirname(os.path.abspath(__file__))
		script_path = os.path.join(current_dir, 'BashGetInfo.sh')
		command_string = [script_path, server['host'], server['username'],
						  server['password'], "TopUsers.sh", "--no-headers"]
		# Make sure the script is executable
		os.chmod(script_path, 0o755)

		# Run the script
		result = subprocess.run(command_string,
								capture_output=True,
								text=True,
								check=True)
		return parse_top_users(result.stdout)
	except subprocess.CalledProcessError as e:
		logging.error(f"Failed to get top users for {server['host']}: {e}")
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
		logging.error(f"Failed to parse top users data: {e}")
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
		logging.error(f"Failed to parse monitoring data: {e}")
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
		logging.info(
			f"Successfully stored metrics in database for {metrics['server_name']}")
	except Exception as e:
		logging.error(f"Database error for {metrics['server_name']}: {e}")
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
		logging.info(
			f"Successfully stored top users in database for {server_name}")
	except Exception as e:
		logging.error(f"Database error in {server_name}: {e}")
		raise


def readServerList() -> List[Dict]:
	"""Read server configurations from environment variables."""
	servers = []
	for i in range(1, 8):
		server_name = os.getenv(f"SERVER{i}_NAME")
		if not server_name:
			continue
		logging.info(f"Server {i} found in environment variables")
		servers.append({
			'name': server_name,
			'host': os.getenv(f"SERVER{i}_HOST"),
			'username': os.getenv(f"SERVER{i}_USERNAME"),
			'password': os.getenv(f"SERVER{i}_PASSWORD")
		})
	return servers


def main():
	try:
		# Initialize the database
		init_db()
		logging.info("Database initialized successfully")
		# Set up a counter for disk usage checks
		server_list = readServerList()
		if not server_list:
			logging.error(
				"No servers found in environment variables. Exiting.")
			return
		while True:
			# Loop through the servers
			for server in server_list:

				if not server_online(server):
					logging.info(f"Server {server['name']} is offline")
					continue
				try:
					# Run monitoring script and get output
					monitoring_output = run_monitoring_script(server)
					top_users = get_top_users(server)

					# Parse the monitoring data
					metrics = parse_monitoring_data(monitoring_output)
					metrics['server_name'] = server['name']

					# Store in database
					store_metrics(metrics)
					store_top_users(server['name'], top_users)
				except Exception as e:
					logging.error(
						f"Error processing server {server['name']}: {e}")
					continue
			# Wait for 5 minutes
			time.sleep(60 * 5)

	except Exception as e:
		logging.error(f"Error in main execution: {e}")
		raise


if __name__ == "__main__":
	main()
