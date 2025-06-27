# Enhanced Server Monitoring Dashboard
import dash
from dash import dcc, html, Input, Output, callback, dash_table, State
import plotly.express as px
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import pandas as pd
import requests
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import logging
import numpy as np

# Load environment variables
load_dotenv()

# Official Khalifa University brand colors per 2020 Brand Guidelines
KU_COLORS = {
	'primary': '#0057B8',		# Official KU Blue (Pantone 2935)
	'secondary': '#6F5091',	  # KU Purple (Pantone 7677)
	'accent': '#78D64B',		 # KU Green (Pantone 7488)
	'undergraduate': '#00A9CE',  # Undergraduate Blue (Pantone 312)
	'graduate': '#6F5091',	   # Graduate Purple (Pantone 7677)
	'postgraduate': '#F8485E',   # Postgraduate Red (Pantone 1785)
	'orange': '#FF8F1C',		 # KU Orange (Pantone 1495)
	'light_gray': '#D0D0CE',	 # Cool Gray 2 (Pantone Cool Gray 2)
	'dark_gray': '#75787B',	  # Cool Gray 9 (Pantone Cool Gray 9)
	'light_brown': '#C5B9AC',  # Light Brown (Pantone 7528)
	'body_text': '#1A1A1A',	  # Body text (K:90 equivalent)
	'white': '#FFFFFF',
	'light': '#F8F9FA',		  # Light background
	'success': '#0057B8',		# Using KU Blue for success
	'warning': '#FF8F1C',		# Using KU Orange for warning
	'danger': '#F8485E',		 # Using KU Red for danger
	'info': '#00A9CE',		   # Using Undergraduate Blue for info
	'muted': '#75787B',		  # Using Cool Gray 9
	'border': '#D0D0CE',		 # Using Cool Gray 2
	'gradient_start': '#0057B8',
	'gradient_end': '#003A7A',
	'card_bg': '#FFFFFF',
	'hover_bg': '#F1F3F4',
	'text_primary': '#1A1A1A',
	'text_secondary': '#75787B',
	'critical': '#F8485E',
	'performance_good': '#0057B8',
	'performance_fair': '#FF8F1C',
	'performance_poor': '#F8485E'
}

# API configuration
API_BASE_URL = os.getenv('API_BASE_URL', 'http://api:5000/api')

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize the Dash app
app = dash.Dash(__name__,
				suppress_callback_exceptions=True,
				meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1.0'}])

app.title = "Khalifa University - Advanced Server Monitoring Dashboard"

# Enhanced CSS with modern design
app.index_string = '''
<!DOCTYPE html>
<html>
	<head>
		{%metas%}
		<title>{%title%}</title>
		{%favicon%}
		{%css%}
		<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
		<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
		<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
		<style>
			:root {
				--ku-primary: #0057B8;	  /* Official KU Blue */
				--ku-secondary: #6F5091;	/* KU Purple */
				--ku-accent: #78D64B;	   /* KU Green */
				--ku-orange: #FF8F1C;	   /* KU Orange */
				--ku-red: #F8485E;		  /* KU Red */
				--ku-light-gray: #D0D0CE;   /* Cool Gray 2 */
				--ku-dark-gray: #75787B;	/* Cool Gray 9 */
				--ku-light: #F8F9FA;
				--ku-dark: #1A1A1A;
				--ku-border: #D0D0CE;
				--ku-success: #78D64B;
				--ku-warning: #FF8F1C;
				--ku-danger: #F8485E;
				--ku-info: #00A9CE;
				--ku-muted: #75787B;
				--ku-card-shadow: 0 8px 32px rgba(0,87,184,0.1);
				--ku-hover-shadow: 0 12px 40px rgba(0,87,184,0.15);
				--ku-transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
			}
			
			* {
				box-sizing: border-box;
				margin: 0;
				padding: 0;
			}
			
			body {
				font-family: 'DM Sans', 'Inter', 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
				background: linear-gradient(135deg, #f8f9fa 0%, #e6ebf0 100%);
				min-height: 100vh;
				color: var(--ku-dark);
				line-height: 1.6;
				font-weight: 400;
			}
			
			/* Enhanced Header */
			.header {
				background: linear-gradient(135deg, var(--ku-primary) 0%, #003A7A 100%);
				padding: 20px 40px;
				color: white;
				display: flex;
				align-items: center;
				justify-content: space-between;
				box-shadow: 0 4px 20px rgba(0,87,184,0.25);
				position: sticky;
				top: 0;
				z-index: 1000;
			}
			
			.header-left {
				display: flex;
				align-items: center;
			}
			
			.header img {
				height: 60px;
				margin-right: 24px;
				filter: brightness(0) invert(1);
			}
			
			.header h1 {
				font-size: 32px;
				font-weight: 600;
				letter-spacing: -0.3px;
				margin: 0;
				font-family: 'DM Sans', sans-serif;
			}
			
			.header-subtitle {
				font-size: 14px;
				opacity: 0.9;
				margin-top: 4px;
			}
			
			.header-right {
				display: flex;
				align-items: center;
				gap: 20px;
			}
			
			.system-time, .status-indicator-header {
				background: rgba(255,255,255,0.1);
				padding: 8px 16px;
				border-radius: 20px;
				font-size: 14px;
				backdrop-filter: blur(10px);
			}
			
			/* Dashboard Container */
			.dashboard-container {
				padding: 32px;
				max-width: 1800px;
				margin: 0 auto;
				background: transparent;
			}
			
			/* Enhanced Cards */
			.card {
				background: white;
				border-radius: 16px;
				box-shadow: var(--ku-card-shadow);
				padding: 32px;
				margin-bottom: 32px;
				border: 1px solid var(--ku-border);
				transition: var(--ku-transition);
				position: relative;
				overflow: hidden;
			}
			
			.card::before {
				content: '';
				position: absolute;
				top: 0;
				left: 0;
				right: 0;
				height: 4px;
				background: linear-gradient(90deg, var(--ku-primary), var(--ku-accent));
			}
			
			.card:hover {
				transform: translateY(-4px);
				box-shadow: var(--ku-hover-shadow);
			}
			
			.card-header {
				display: flex;
				align-items: center;
				justify-content: space-between;
				margin-bottom: 24px;
				padding-bottom: 16px;
				border-bottom: 1px solid var(--ku-border);
			}
			
			.card-title {
				font-size: 22px;
				font-weight: 600;
				color: var(--ku-dark);
				display: flex;
				align-items: center;
				gap: 12px;
				font-family: 'DM Sans', sans-serif;
			}
			
			.card-subtitle {
				font-size: 14px;
				color: var(--ku-muted);
				font-weight: 400;
				line-height: 1.5;
			}
			
			.card-actions {
				display: flex;
				gap: 12px;
			}
			
			/* System Overview Grid */
			.system-overview {
				display: grid;
				grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
				gap: 24px;
				margin-bottom: 32px;
			}
			
			.overview-stat {
				background: linear-gradient(135deg, rgba(0,87,184,0.08), rgba(0,87,184,0.12));
				padding: 28px;
				border-radius: 12px;
				text-align: center;
				border: 1px solid rgba(0,87,184,0.15);
				backdrop-filter: blur(10px);
			}
			
			.stat-value {
				font-size: 36px;
				font-weight: 700;
				color: var(--ku-primary);
				display: block;
				line-height: 1.2;
				font-family: 'DM Sans', sans-serif;
			}
			
			.stat-label {
				font-size: 14px;
				color: var(--ku-muted);
				font-weight: 500;
				margin-top: 8px;
			}
			
			.stat-change {
				font-size: 12px;
				margin-top: 4px;
				font-weight: 600;
			}
			
			.stat-change.positive {
				color: var(--ku-success);
			}
			
			.stat-change.negative {
				color: var(--ku-danger);
			}
			
			/* Enhanced Server Cards */
			.server-card {
				background: white;
				border-radius: 20px;
				box-shadow: var(--ku-card-shadow);
				padding: 24px;
				margin: 16px;
				border: 1px solid var(--ku-border);
				transition: var(--ku-transition);
				position: relative;
				overflow: hidden;
			}
			
			.server-card::before {
				content: '';
				position: absolute;
				top: 0;
				left: 0;
				right: 0;
				height: 6px;
				background: linear-gradient(90deg, var(--ku-primary), var(--ku-accent));
			}
			
			.server-header {
				display: flex;
				align-items: center;
				justify-content: space-between;
				margin-bottom: 20px;
			}
			
			.server-name {
				font-size: 20px;
				font-weight: 600;
				color: var(--ku-dark);
				display: flex;
				align-items: center;
				gap: 12px;
				font-family: 'DM Sans', sans-serif;
			}
			
			.server-status-badge {
				padding: 6px 12px;
				border-radius: 20px;
				font-size: 12px;
				font-weight: 600;
				text-transform: uppercase;
				letter-spacing: 0.5px;
			}
			
			.status-online {
				background: rgba(0, 87, 184, 0.1);
				color: var(--ku-success);
				border: 1px solid rgba(0, 87, 184, 0.2);
			}
			
			.status-warning {
				background: rgba(255, 143, 28, 0.1);
				color: var(--ku-warning);
				border: 1px solid rgba(255, 143, 28, 0.2);
			}
			
			.status-offline {
				background: rgba(248, 72, 94, 0.1);
				color: var(--ku-danger);
				border: 1px solid rgba(248, 72, 94, 0.2);
			}
			
			.server-metrics {
				display: grid;
				grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
				gap: 16px;
				margin: 20px 0;
			}
			
			.metric-item {
				text-align: center;
				padding: 16px;
				background: var(--ku-light);
				border-radius: 12px;
				border: 1px solid var(--ku-border);
			}
			
			.metric-value {
				font-size: 24px;
				font-weight: 600;
				display: block;
				margin-bottom: 4px;
				font-family: 'DM Sans', sans-serif;
			}
			
			.metric-label {
				font-size: 12px;
				color: var(--ku-muted);
				font-weight: 500;
			}
			
			.server-details {
				background: var(--ku-light);
				padding: 20px;
				border-radius: 12px;
				margin-top: 20px;
			}
			
			.detail-row {
				display: flex;
				justify-content: space-between;
				align-items: center;
				padding: 8px 0;
				border-bottom: 1px solid var(--ku-border);	
			}
			
			.detail-row:last-child {
				border-bottom: none;
			}
			
			.detail-label {
				font-weight: 500;
				color: var(--ku-dark);
				font-size: 14px;
			}
			
			.detail-value {
				color: var(--ku-muted);
				font-size: 14px;
			}
			
			/* Alert Panel */
			.alert-panel {
				background: linear-gradient(135deg, rgba(248, 72, 94, 0.06), rgba(248, 72, 94, 0.12));
				border: 1px solid rgba(248, 72, 94, 0.2);
				border-radius: 12px;
				padding: 24px;
				margin-bottom: 28px;
			}
			
			.alert-item {
				display: flex;
				align-items: center;
				padding: 12px;
				background: rgba(255, 255, 255, 0.7);
				border-radius: 8px;
				margin-bottom: 12px;
				border-left: 4px solid var(--ku-primary);
			}
			
			.alert-icon {
				margin-right: 12px;
				color: var(--ku-danger);
				font-size: 18px;
			}
			
			.alert-content {
				flex: 1;
			}
			
			.alert-title {
				font-weight: 500;
				color: var(--ku-dark);
				margin-bottom: 4px;
				font-family: 'DM Sans', sans-serif;
			}
			
			.alert-description {
				font-size: 14px;
				color: var(--ku-muted);
			}
			
			.alert-time {
				font-size: 12px;
				color: var(--ku-muted);
			}
			
			/* Performance Indicators */
			.performance-indicator {
				display: flex;
				align-items: center;
				gap: 8px;
				padding: 8px 12px;
				border-radius: 20px;
				font-size: 12px;
				font-weight: 500;
				font-family: 'DM Sans', sans-serif;
				text-transform: uppercase;
				letter-spacing: 0.5px;
			}
			
			.perf-excellent {
				background: rgba(39, 174, 96, 0.1);
				color: var(--ku-success);
				border: 1px solid rgba(39, 174, 96, 0.2);
			}
			
			.perf-good {
				background: rgba(46, 204, 113, 0.1);
				color: #2ECC71;
				border: 1px solid rgba(46, 204, 113, 0.2);
			}
			
			.perf-fair {
				background: rgba(243, 156, 18, 0.1);
				color: var(--ku-warning);
				border: 1px solid rgba(243, 156, 18, 0.2);
			}
			
			.perf-poor {
				background: rgba(231, 76, 60, 0.1);
				color: var(--ku-danger);
				border: 1px solid rgba(231, 76, 60, 0.2);
			}
			
			/* Enhanced Tables */
			.enhanced-table {
				background: white;
				border-radius: 12px;
				overflow: hidden;
				box-shadow: 0 4px 16px rgba(0,87,184,0.1);
			}
			
			.table-header {
				background: linear-gradient(135deg, var(--ku-primary), #003A7A);
				color: white;
				padding: 16px 20px;
				font-weight: 600;
			}
			
			/* Network Activity */
			.network-activity {
				display: grid;
				grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
				gap: 16px;
				margin: 20px 0;
			}
			
			.network-stat {
				background: linear-gradient(135deg, rgba(0, 169, 206, 0.08), rgba(0, 169, 206, 0.12));
				padding: 24px;
				border-radius: 12px;
				text-align: center;
				border: 1px solid rgba(0, 169, 206, 0.2);
				backdrop-filter: blur(5px);
			}
			
			/* Resource Usage Bars */
			.resource-bar {
				background: var(--ku-light);
				height: 8px;
				border-radius: 4px;
				overflow: hidden;
				margin: 8px 0;
			}
			
			.resource-fill {
				height: 100%;
				border-radius: 4px;
				transition: width 0.3s ease;
			}
			
			.resource-cpu {
				background: linear-gradient(90deg, var(--ku-info), #0088CC);
			}
			
			.resource-memory {
				background: linear-gradient(90deg, var(--ku-warning), #E6740A);
			}
			
			.resource-disk {
				background: linear-gradient(90deg, var(--ku-success), #003A7A);
			}
			
			/* Responsive Design */
			@media (max-width: 768px) {
				.dashboard-container {
					padding: 16px;
				}
				
				.server-metrics {
					grid-template-columns: repeat(2, 1fr);
				}
				
				.system-overview {
					grid-template-columns: 1fr;
				}
				
				.header {
					padding: 16px 20px;
				}
				
				.header h1 {
					font-size: 24px;
				}
			}
			
			/* Custom Scrollbar */
			::-webkit-scrollbar {
				width: 8px;
			}
			
			::-webkit-scrollbar-track {
				background: var(--ku-light);
			}
			
			::-webkit-scrollbar-thumb {
				background: var(--ku-muted);
				border-radius: 4px;
			}
			
			::-webkit-scrollbar-thumb:hover {
				background: var(--ku-primary);
			}
			
			/* Loading Animation */
			.loading-spinner {
				display: inline-block;
				width: 20px;
				height: 20px;
				border: 3px solid var(--ku-light);
				border-radius: 50%;
				border-top-color: var(--ku-primary);
				animation: spin 1s ease-in-out infinite;
			}
			
			@keyframes spin {
				to { transform: rotate(360deg); }
			}
			
			/* Tab Enhancements */
			.tab-selected {
				background: linear-gradient(135deg, var(--ku-primary) 0%, #003A7A 100%) !important;
				color: white !important;
				border-radius: 12px 12px 0 0 !important;
				font-weight: 600;
			}
			
			/* Button Enhancements */
			.btn {
				background: linear-gradient(135deg, var(--ku-primary) 0%, #003A7A 100%);
				color: white;
				border: none;
				padding: 12px 24px;
				border-radius: 25px;
				cursor: pointer;
				font-size: 14px;
				font-weight: 600;
				font-family: 'DM Sans', sans-serif;
				transition: var(--ku-transition);
				box-shadow: 0 4px 16px rgba(0,87,184,0.2);
				display: inline-flex;
				align-items: center;
				gap: 8px;
			}
			
			.btn:hover {
				transform: translateY(-2px);
				box-shadow: 0 8px 24px rgba(0,87,184,0.3);
				background: linear-gradient(135deg, #003A7A 0%, var(--ku-primary) 100%);
			}
			
			.btn:active {
				transform: translateY(0);
			}
			
			.btn-secondary {
				background: linear-gradient(135deg, var(--ku-muted) 0%, #5A6C7D 100%);
			}
			
			.btn-danger {
				background: linear-gradient(135deg, var(--ku-danger) 0%, #C0392B 100%);
			}
		</style>
	</head>
	<body>
		<div class="header">
			<div class="header-left">
				<img src="https://www.ku.ac.ae/wp-content/themes/khalifa-university/img/logo.svg" alt="Khalifa University Logo">
				<div>
					<h1>Advanced Server Monitoring</h1>
					<div class="header-subtitle">Real-time Infrastructure Dashboard</div>
				</div>
			</div>
			<div class="header-right">
				<div class="system-time" id="system-time">
					<i class="fas fa-clock"></i> <span id="current-time"></span>
				</div>
				<div class="status-indicator-header">
					<i class="fas fa-server"></i> <span id="server-count">0 Servers</span>
				</div>
			</div>
		</div>
		<div class="dashboard-container">
			{%app_entry%}
		</div>
		{%config%}
		{%scripts%}
		{%renderer%}
		<script>
			// Update time every second
			function updateTime() {
				const now = new Date();
				document.getElementById('current-time').textContent = now.toLocaleString();
			}
			setInterval(updateTime, 1000);
			updateTime();
		</script>
	</body>
</html>
'''

# API Functions (keeping existing ones and adding new ones)


def get_latest_server_metrics():
	try:
		response = requests.get(
			f"{API_BASE_URL}/servers/metrics/latest", timeout=10)
		if response.status_code == 200:
			data = response.json()
			if data.get('success'):
				return data.get('data', [])
		return []
	except Exception as e:
		logging.error(f"API error fetching server metrics: {e}")
		return []


def get_top_users():
	try:
		response = requests.get(f"{API_BASE_URL}/users/top", timeout=10)
		if response.status_code == 200:
			data = response.json()
			if data.get('success'):
				return data.get('data', [])
		return []
	except Exception as e:
		logging.error(f"API error fetching top users: {e}")
		return []


def get_historical_metrics(server_name, hours=24):
	try:
		response = requests.get(
			f"{API_BASE_URL}/servers/{server_name}/metrics/historical/{hours}", timeout=10)
		if response.status_code == 200:
			data = response.json()
			if data.get('success'):
				return data.get('data', [])
		return []
	except Exception as e:
		logging.error(
			f"API error fetching historical metrics for {server_name}: {e}")
		return []


def determine_server_status(metrics):
	if not metrics:
		return "offline"

	ram_percentage = metrics.get('ram_percentage', 0)
	disk_percentage = metrics.get('disk_percentage', 0)
	cpu_load = float(metrics.get('cpu_load_5min', 0))

	if ram_percentage > 90 or disk_percentage > 90 or cpu_load > 5:
		return "warning"

	timestamp = metrics.get('timestamp')
	if timestamp:
		if isinstance(timestamp, str):
			try:
				timestamp = datetime.fromisoformat(
					timestamp.replace('Z', '+00:00'))
			except:
				try:
					timestamp = datetime.strptime(
						timestamp, '%Y-%m-%d %H:%M:%S.%f')
				except:
					timestamp = datetime.strptime(
						timestamp, '%Y-%m-%dT%H:%M:%S.%f')
		if datetime.now() - timestamp.replace(tzinfo=None) > timedelta(minutes=15):
			return "offline"

	return "online"


def get_performance_rating(cpu_load, ram_percentage, disk_percentage):
	"""Calculate overall performance rating"""
	cpu_score = 100 - min(cpu_load * 10, 100)  # CPU load of 10 = 0 score
	ram_score = 100 - ram_percentage
	disk_score = 100 - disk_percentage

	overall_score = (cpu_score + ram_score + disk_score) / 3

	if overall_score >= 85:
		return "excellent", "#0057B8"
	elif overall_score >= 70:
		return "good", "#0057B8"
	elif overall_score >= 50:
		return "fair", "#F39C12"
	else:
		return "poor", "#E74C3C"


def generate_alerts(metrics_list):
	"""Generate system alerts based on metrics"""
	alerts = []

	for metric in metrics_list:
		server_name = metric.get('server_name', 'Unknown')

		# CPU Alert
		cpu_load = float(metric.get('cpu_load_5min', 0))
		if cpu_load > 8:
			alerts.append({
				'type': 'critical',
				'title': f'Critical CPU Load - {server_name}',
				'description': f'CPU load is {cpu_load:.2f}, exceeding critical threshold',
				'icon': 'fas fa-exclamation-triangle',
				'time': 'Now'
			})
		elif cpu_load > 5:
			alerts.append({
				'type': 'warning',
				'title': f'High CPU Load - {server_name}',
				'description': f'CPU load is {cpu_load:.2f}, monitor closely',
				'icon': 'fas fa-exclamation-circle',
				'time': 'Now'
			})

		# Memory Alert
		ram_percentage = metric.get('ram_percentage', 0)
		if ram_percentage > 95:
			alerts.append({
				'type': 'critical',
				'title': f'Critical Memory Usage - {server_name}',
				'description': f'Memory usage at {ram_percentage}%, immediate attention required',
				'icon': 'fas fa-memory',
				'time': 'Now'
			})
		elif ram_percentage > 85:
			alerts.append({
				'type': 'warning',
				'title': f'High Memory Usage - {server_name}',
				'description': f'Memory usage at {ram_percentage}%',
				'icon': 'fas fa-memory',
				'time': 'Now'
			})

		# Disk Alert
		disk_percentage = metric.get('disk_percentage', 0)
		if disk_percentage > 95:
			alerts.append({
				'type': 'critical',
				'title': f'Critical Disk Usage - {server_name}',
				'description': f'Disk usage at {disk_percentage}%, cleanup required',
				'icon': 'fas fa-hdd',
				'time': 'Now'
			})
		elif disk_percentage > 85:
			alerts.append({
				'type': 'warning',
				'title': f'High Disk Usage - {server_name}',
				'description': f'Disk usage at {disk_percentage}%',
				'icon': 'fas fa-hdd',
				'time': 'Now'
			})

	return alerts

# Enhanced Dashboard Components


def create_system_overview():
	"""Create system overview cards"""
	metrics = get_latest_server_metrics()

	total_servers = len(metrics)
	online_servers = len(
		[m for m in metrics if determine_server_status(m) == "online"])
	warning_servers = len(
		[m for m in metrics if determine_server_status(m) == "warning"])
	offline_servers = len(
		[m for m in metrics if determine_server_status(m) == "offline"])

	avg_cpu = np.mean([float(m.get('cpu_load_5min', 0))
					  for m in metrics]) if metrics else 0
	avg_ram = np.mean([m.get('ram_percentage', 0)
					  for m in metrics]) if metrics else 0
	avg_disk = np.mean([m.get('disk_percentage', 0)
					   for m in metrics]) if metrics else 0

	total_users = sum([m.get('logged_users', 0) for m in metrics])

	return html.Div([
		html.Div([
					html.Div([
						html.Span(f"{total_servers}", className="stat-value"),
						html.Div("Total Servers", className="stat-label"),
						html.Div("↑ 2 new this month",
								 className="stat-change positive")
					], className="overview-stat"),

					html.Div([
						html.Span(f"{online_servers}", className="stat-value"),
						html.Div("Online Servers", className="stat-label"),
						html.Div(f"{(online_servers/total_servers*100):.1f}% uptime" if total_servers > 0 else "0% uptime",
								 className="stat-change positive")
					], className="overview-stat"),

					html.Div([
						html.Span(f"{warning_servers}",
								  className="stat-value"),
						html.Div("Servers with Warnings",
								 className="stat-label"),
						html.Div(
							"Requires attention", className="stat-change negative" if warning_servers > 0 else "stat-change positive")
					], className="overview-stat"),

					html.Div([
						html.Span(f"{offline_servers}",
								  className="stat-value"),
						html.Div("Offline Servers", className="stat-label"),
						html.Div(
							"Check connectivity", className="stat-change negative" if offline_servers > 0 else "stat-change positive")
					], className="overview-stat"),

					html.Div([
						html.Span(f"{avg_cpu:.1f}", className="stat-value"),
						html.Div("Avg CPU Load", className="stat-label"),
						html.Div("5-minute average", className="stat-change")
					], className="overview-stat"),

					html.Div([
						html.Span(f"{avg_ram:.1f}%", className="stat-value"),
						html.Div("Avg Memory Usage", className="stat-label"),
						html.Div("Across all servers", className="stat-change")
					], className="overview-stat"),

					html.Div([
						html.Span(f"{total_users}", className="stat-value"),
						html.Div("Active Users", className="stat-label"),
						html.Div("Currently logged in",
								 className="stat-change")
					], className="overview-stat"),

					html.Div([
						html.Span(f"{avg_disk:.1f}%", className="stat-value"),
						html.Div("Avg Disk Usage", className="stat-label"),
						html.Div("Storage utilization",
								 className="stat-change")
					], className="overview-stat"),
					], className="system-overview")
	])


def create_alert_panel():
	"""Create alerts panel"""
	metrics = get_latest_server_metrics()
	alerts = generate_alerts(metrics)

	if not alerts:
		return html.Div([
			html.Div([
						html.I(className="fas fa-check-circle",
							   style={'color': KU_COLORS['primary'], 'fontSize': '24px'}),
						html.Div([
							html.Div("All Systems Normal",
									 className="alert-title"),
							html.Div("No alerts at this time",
									 className="alert-description")
						], className="alert-content")
						], className="alert-item", style={'border-left-color': KU_COLORS['success']})
		], className="alert-panel", style={'background': 'linear-gradient(135deg, rgba(0, 87, 184, 0.05), rgba(0, 87, 184, 0.1))', 'border-color': 'rgba(0, 87, 184, 0.2)'})

	alert_items = []
	for alert in alerts[:5]:  # Show only top 5 alerts
		alert_items.append(
			html.Div([
				html.I(className=alert['icon'] + " alert-icon"),
				html.Div([
					html.Div(alert['title'], className="alert-title"),
					html.Div(alert['description'],
							 className="alert-description")
				], className="alert-content"),
				html.Div(alert['time'], className="alert-time")
			], className="alert-item")
		)

	return html.Div(alert_items, className="alert-panel")


def create_enhanced_server_cards():
	"""Create enhanced server cards with detailed information"""
	metrics = get_latest_server_metrics()

	if not metrics:
		return html.Div("No server data available", style={'text-align': 'center', 'margin': '20px'})

	server_cards = []

	for metric in metrics:
		server_name = metric.get('server_name', 'Unknown')
		status = determine_server_status(metric)

		# Get performance rating
		cpu_load = float(metric.get('cpu_load_5min', 0))
		ram_percentage = metric.get('ram_percentage', 0)
		disk_percentage = metric.get('disk_percentage', 0)

		perf_rating, perf_color = get_performance_rating(
			cpu_load, ram_percentage, disk_percentage)

		# Status badge styling
		status_class = f"status-{status}"
		status_text = status.upper()

		card = html.Div([
			# Server Header
			html.Div([
						html.Div([
							html.I(className="fas fa-server",
								   style={'marginRight': '8px'}),
							server_name
						], className="server-name"),
						html.Div([
							html.Span(
								status_text, className=f"server-status-badge {status_class}"),
							html.Span(
								perf_rating.upper(), className=f"performance-indicator perf-{perf_rating}")
						])
						], className="server-header"),

			# Key Metrics Grid
			html.Div([
				html.Div([
					html.Span(f"{cpu_load:.1f}", className="metric-value", style={
						'color': perf_color if cpu_load > 5 else KU_COLORS['primary']}),
					html.Span("CPU Load", className="metric-label")
				], className="metric-item"),

				html.Div([
					html.Span(f"{ram_percentage}%", className="metric-value", style={
						'color': KU_COLORS['danger'] if ram_percentage > 85 else KU_COLORS['warning'] if ram_percentage > 70 else KU_COLORS['primary']}),
					html.Span("Memory", className="metric-label")
				], className="metric-item"),

				html.Div([
					html.Span(f"{disk_percentage}%", className="metric-value", style={
						'color': KU_COLORS['danger'] if disk_percentage > 85 else KU_COLORS['warning'] if disk_percentage > 70 else KU_COLORS['primary']}),
					html.Span("Disk", className="metric-label")
				], className="metric-item"),

				html.Div([
					html.Span(f"{metric.get('logged_users', 0)}",
							  className="metric-value"),
					html.Span("Users", className="metric-label")
				], className="metric-item"),

				html.Div([
					html.Span(f"{metric.get('tcp_connections', 0)}",
							  className="metric-value"),
					html.Span("Connections", className="metric-label")
				], className="metric-item"),

				html.Div([
					html.Span(f"{metric.get('physical_cpus', 0)}",
							  className="metric-value"),
					html.Span("CPUs", className="metric-label")
				], className="metric-item")
			], className="server-metrics"),

			# Resource Usage Bars
			html.Div([
				html.Div([
					html.Div(f"CPU Load: {cpu_load:.1f}", style={
						'fontSize': '12px', 'marginBottom': '4px', 'fontWeight': '600'}),
					html.Div([
						html.Div(className="resource-fill resource-cpu",
								 style={'width': f'{min(cpu_load*10, 100)}%'})
					], className="resource-bar")
				]),
				html.Div([
					html.Div(f"Memory: {ram_percentage}%", style={
						'fontSize': '12px', 'marginBottom': '4px', 'fontWeight': '600'}),
					html.Div([
						html.Div(className="resource-fill resource-memory",
								 style={'width': f'{ram_percentage}%'})
					], className="resource-bar")
				]),
				html.Div([
					html.Div(f"Disk: {disk_percentage}%", style={
						'fontSize': '12px', 'marginBottom': '4px', 'fontWeight': '600'}),
					html.Div([
						html.Div(className="resource-fill resource-disk",
								 style={'width': f'{disk_percentage}%'})
					], className="resource-bar")
				])
			], style={'margin': '16px 0'}),

			# Detailed Information
			html.Div([
				html.Div([
					html.Span("Operating System",
							  className="detail-label"),
					html.Span(
						f"{metric.get('operating_system', 'Unknown')} ({metric.get('architecture', 'Unknown')})", className="detail-value")
				], className="detail-row"),

				html.Div([
					html.Span("CPU Configuration",
							  className="detail-label"),
					html.Span(
						f"Physical: {metric.get('physical_cpus', 0)}, Virtual: {metric.get('virtual_cpus', 0)}", className="detail-value")
				], className="detail-row"),

				html.Div([
					html.Span("Last Boot Time", className="detail-label"),
					html.Span(metric.get('last_boot', 'Unknown'),
							  className="detail-value")
				], className="detail-row"),

				html.Div([
					html.Span("User Sessions", className="detail-label"),
					html.Span(
						f"SSH: {metric.get('active_ssh_users', 0)}, VNC: {metric.get('active_vnc_users', 0)}", className="detail-value")
				], className="detail-row"),

				html.Div([
					html.Span("Load Averages", className="detail-label"),
					html.Span(
						f"1m: {metric.get('cpu_load_1min', 0)} | 5m: {metric.get('cpu_load_5min', 0)} | 15m: {metric.get('cpu_load_15min', 0)}", className="detail-value")
				], className="detail-row"),

				html.Div([
					html.Span("Last Updated", className="detail-label"),
					html.Span(metric.get('timestamp', 'Unknown'),
							  className="detail-value")
				], className="detail-row")
			], className="server-details")

		], className="server-card")

		server_cards.append(card)

	# Organize in responsive grid
	return html.Div(server_cards, style={
		'display': 'grid',
		'grid-template-columns': 'repeat(auto-fit, minmax(400px, 1fr))',
		'gap': '24px',
		'margin': '20px 0'
	})


# Define the main layout
app.layout = html.Div([
	# Auto-refresh component
	dcc.Interval(
		id='interval-component',
		interval=30*1000,  # Refresh every 30 seconds
		n_intervals=0
	),

	# System Overview Section
	html.Div([
		html.Div([
			html.Div([
				html.I(className="fas fa-tachometer-alt",
					   style={'marginRight': '12px', 'fontSize': '20px'}),
				"System Overview"
			], className="card-title"),
			html.Div("Real-time infrastructure status",
					 className="card-subtitle")
		], className="card-header"),
		html.Div(id='system-overview', children=create_system_overview())
	], className="card"),

	# Alerts Panel
	html.Div([
		html.Div([
			html.Div([
				html.I(className="fas fa-exclamation-triangle",
					   style={'marginRight': '12px', 'fontSize': '20px'}),
				"System Alerts"
			], className="card-title"),
			html.Button([
				html.I(className="fas fa-sync-alt",
					   style={'marginRight': '8px'}),
				"Refresh"
			], id='refresh-alerts', className='btn')
		], className="card-header"),
		html.Div(id='alerts-panel', children=create_alert_panel())
	], className="card"),

	# Main Dashboard Tabs
	dcc.Tabs([
		dcc.Tab(
			label='Server Details',
			children=[
				html.Div(id='enhanced-server-cards',
						 children=create_enhanced_server_cards()),
			],
			style={'padding': '20px',
				   'fontSize': '16px', 'fontWeight': '600'},
			selected_style={'padding': '20px', 'fontSize': '16px', 'fontWeight': '600',
							'backgroundColor': KU_COLORS['primary'], 'color': 'white'}
		),
		dcc.Tab(
			label='User Activity',
			children=[
				html.Div([
					html.Div([
						html.Div([
							html.I(
								className="fas fa-users", style={'marginRight': '12px', 'fontSize': '20px'}),
							"User Activity Monitor"
						], className="card-title"),
						html.Div(
							"Active user sessions and resource consumption", className="card-subtitle")
					], className="card-header"),
					html.Div(id='enhanced-users-table')
				], className="card")
			],
			style={'padding': '20px',
				   'fontSize': '16px', 'fontWeight': '600'},
			selected_style={'padding': '20px', 'fontSize': '16px', 'fontWeight': '600',
							'backgroundColor': KU_COLORS['primary'], 'color': 'white'}
		),
		dcc.Tab(
			label='Performance Analytics',
			children=[
				html.Div([
					html.Div([
						html.Div([
							html.I(className="fas fa-chart-line",
								   style={'marginRight': '12px', 'fontSize': '20px'}),
							"Performance Analytics"
						], className="card-title"),
						html.Div(
							"Historical metrics and trend analysis", className="card-subtitle")
					], className="card-header"),
					html.Div(id='enhanced-historical-graphs')
				], className="card")
			],
			style={'padding': '20px',
				   'fontSize': '16px', 'fontWeight': '600'},
			selected_style={'padding': '20px', 'fontSize': '16px', 'fontWeight': '600',
							'backgroundColor': KU_COLORS['primary'], 'color': 'white'}
		),
		dcc.Tab(
			label='Network Monitor',
			children=[
				html.Div([
					html.Div([
						html.Div([
							html.I(className="fas fa-network-wired",
								   style={'marginRight': '12px', 'fontSize': '20px'}),
							"Network Activity Monitor"
						], className="card-title"),
						html.Div(
							"Connection statistics and network health", className="card-subtitle")
					], className="card-header"),
					html.Div(id='network-monitor')
				], className="card")
			],
			style={'padding': '20px',
				   'fontSize': '16px', 'fontWeight': '600'},
			selected_style={'padding': '20px', 'fontSize': '16px', 'fontWeight': '600',
							'backgroundColor': KU_COLORS['primary'], 'color': 'white'}
		)
	]),

	# Footer with refresh controls
	html.Div([
		html.Button([
			html.I(className="fas fa-sync-alt",
				   style={'marginRight': '8px'}),
			"Refresh All Data"
		], id='refresh-button', className='btn'),
		html.Button([
			html.I(className="fas fa-download",
				   style={'marginRight': '8px'}),
			"Export Report"
		], id='export-button', className='btn btn-secondary', style={'marginLeft': '12px'}),
		html.Div(id='last-updated', style={'display': 'inline-block',
										   'marginLeft': '24px', 'fontSize': '14px', 'color': KU_COLORS['muted']})
	], style={'margin': '32px 0', 'textAlign': 'right', 'padding': '20px', 'borderTop': f'1px solid {KU_COLORS["border"]}', 'backgroundColor': 'white', 'borderRadius': '12px'})
])


def create_network_monitor():
	"""Create network monitoring component"""
	metrics = get_latest_server_metrics()

	if not metrics:
		return html.Div("No network data available", style={'text-align': 'center', 'margin': '20px'})

	total_connections = sum([m.get('tcp_connections', 0) for m in metrics])
	total_ssh_users = sum([m.get('active_ssh_users', 0) for m in metrics])
	total_vnc_users = sum([m.get('active_vnc_users', 0) for m in metrics])

	return html.Div([
		# Network Statistics
		html.Div([
					html.Div([
						html.Span(f"{total_connections}",
								  className="stat-value"),
						html.Div("Total TCP Connections",
								 className="stat-label"),
					], className="network-stat"),

					html.Div([
						html.Span(f"{total_ssh_users}",
								  className="stat-value"),
						html.Div("Active SSH Sessions",
								 className="stat-label"),
					], className="network-stat"),

					html.Div([
						html.Span(f"{total_vnc_users}",
								  className="stat-value"),
						html.Div("Active VNC Sessions",
								 className="stat-label"),
					], className="network-stat"),

					html.Div([
						html.Span(
							f"{len([m for m in metrics if m.get('tcp_connections', 0) > 50])}", className="stat-value"),
						html.Div("High Traffic Servers",
								 className="stat-label"),
					], className="network-stat"),
					], className="network-activity"),

		# Per-server network details
		html.Div([
			html.H4("Server Network Details", style={
				'margin': '20px 0 16px 0', 'color': KU_COLORS['text_primary']}),
			html.Div([
				dash_table.DataTable(
					id='network-table',
					columns=[
						{'name': 'Server', 'id': 'server_name'},
						{'name': 'TCP Connections',
						 'id': 'tcp_connections', 'type': 'numeric'},
						{'name': 'SSH Users', 'id': 'active_ssh_users',
						 'type': 'numeric'},
						{'name': 'VNC Users', 'id': 'active_vnc_users',
						 'type': 'numeric'},
						{'name': 'Status', 'id': 'status'},
					],
					data=[{
						'server_name': m.get('server_name', 'Unknown'),
						'tcp_connections': m.get('tcp_connections', 0),
						'active_ssh_users': m.get('active_ssh_users', 0),
						'active_vnc_users': m.get('active_vnc_users', 0),
						'status': determine_server_status(m).title()
					} for m in metrics],
					style_table={'overflowX': 'auto'},
					style_cell={
						'textAlign': 'left',
						'padding': '12px',
						'font-family': 'DM Sans, Inter, sans-serif',
						'fontSize': '14px'
					},
					style_header={
						'backgroundColor': KU_COLORS['primary'],
						'color': 'white',
						'fontWeight': '600',
						'fontSize': '14px',
						'padding': '16px 12px'
					},
					style_data_conditional=[
						{
							'if': {'column_id': 'tcp_connections', 'filter_query': '{tcp_connections} > 100'},
							'backgroundColor': 'rgba(248, 72, 94, 0.1)',
							'color': KU_COLORS['danger'],
							'fontWeight': '600'
						},
						{
							'if': {'column_id': 'status', 'filter_query': '{status} = Offline'},
							'backgroundColor': 'rgba(248, 72, 94, 0.1)',
							'color': KU_COLORS['danger']
						},
						{
							'if': {'column_id': 'status', 'filter_query': '{status} = Warning'},
							'backgroundColor': 'rgba(255, 143, 28, 0.1)',
							'color': KU_COLORS['warning']
						}
					],
					sort_action='native',
					filter_action='native',
					page_size=10
				)
			], className="enhanced-table")
		])
	])


def safe_float(val):
	try:
		return float(val)
	except (ValueError, TypeError):
		return 0

def create_enhanced_users_table():
	"""Create enhanced users table with more details"""
	users_data = get_top_users()

	if not users_data:
		return html.Div("No user data available", style={'text-align': 'center', 'margin': '20px'})

	# Group users by server
	servers = {}
	total_users = len(users_data)

	high_usage_users = len([
		u for u in users_data
		if safe_float(u.get('cpu', 0)) > 50 or safe_float(u.get('mem', 0)) > 50
	])

	for user in users_data:
		server_name = user['server_name']
		if server_name not in servers:
			servers[server_name] = []
		servers[server_name].append(user)

	# Summary statistics
	summary = html.Div([
		html.Div([
			html.Span(f"{total_users}", className="stat-value"),
			html.Div("Total Active Users", className="stat-label"),
		], className="overview-stat"),

		html.Div([
			html.Span(f"{len(servers)}", className="stat-value"),
			html.Div("Servers with Users", className="stat-label"),
		], className="overview-stat"),

		html.Div([
			html.Span(f"{high_usage_users}", className="stat-value"),
			html.Div("High Resource Users", className="stat-label"),
		], className="overview-stat"),
	], style={'display': 'flex', 'gap': '20px', 'margin': '20px 0'})

	# Create tabs for each server
	tabs = []
	for server_name, users in servers.items():
		df = pd.DataFrame(users)

		table = dash_table.DataTable(
			id=f'users-table-{server_name}',
			columns=[
				{'name': 'Username', 'id': 'username'},
				{'name': 'CPU Usage (%)', 'id': 'cpu', 'type': 'numeric'},
				{'name': 'Memory Usage (%)', 'id': 'mem', 'type': 'numeric'},
				{'name': 'Disk Usage (GB)', 'id': 'disk', 'type': 'numeric'},
				{'name': 'Status', 'id': 'status'},
			],
			data=[{
				**user,
				'status': 'High Usage' if safe_float(user.get('cpu', 0)) > 50 or safe_float(user.get('mem', 0)) > 50 else 'Normal'
			} for user in users],
			style_table={'overflowX': 'auto'},
			style_cell={
				'textAlign': 'left',
				'padding': '12px',
				'font-family': 'DM Sans, Inter, sans-serif',
				'fontSize': '14px'
			},
			style_header={
				'backgroundColor': KU_COLORS['primary'],
				'color': 'white',
				'fontWeight': '600',
				'fontSize': '14px',
				'padding': '16px 12px',
				'fontFamily': 'DM Sans, sans-serif'
			},
			style_data_conditional=[
				{
					'if': {'column_id': 'cpu', 'filter_query': '{cpu} > 70'},
					'backgroundColor': 'rgba(248, 72, 94, 0.1)',
					'color': KU_COLORS['danger'],
					'fontWeight': '600'
				},
				{
					'if': {'column_id': 'cpu', 'filter_query': '{cpu} > 50 && {cpu} <= 70'},
					'backgroundColor': 'rgba(255, 143, 28, 0.1)',
					'color': KU_COLORS['warning'],
					'fontWeight': '600'
				},
				{
					'if': {'column_id': 'mem', 'filter_query': '{mem} > 70'},
					'backgroundColor': 'rgba(248, 72, 94, 0.1)',
					'color': KU_COLORS['danger'],
					'fontWeight': '600'
				},
				{
					'if': {'column_id': 'mem', 'filter_query': '{mem} > 50 && {mem} <= 70'},
					'backgroundColor': 'rgba(255, 143, 28, 0.1)',
					'color': KU_COLORS['warning'],
					'fontWeight': '600'
				},
				{
					'if': {'column_id': 'disk', 'filter_query': '{disk} > 10'},
					'backgroundColor': 'rgba(255, 143, 28, 0.1)',
					'color': KU_COLORS['warning'],
					'fontWeight': '600'
				}
			],
			sort_action='native',
			filter_action='native',
			page_size=15
		)

		tab = dcc.Tab(
			label=f"{server_name} ({len(users)})",
			value=server_name,
			children=[table],
			style={'padding': '15px', 'fontSize': '14px'},
			selected_style={
				'backgroundColor': KU_COLORS['primary'],
				'color': 'white',
				'padding': '15px',
				'fontSize': '14px',
				'fontWeight': '600'
			}
		)
		tabs.append(tab)

	return html.Div([
		summary,
		dcc.Tabs(id='enhanced-user-tabs', value=list(servers.keys())
				 [0] if servers else '', children=tabs)
	])


def create_enhanced_historical_graphs():
	"""Create enhanced historical graphs with better visualizations"""
	metrics = get_latest_server_metrics()

	if not metrics:
		return html.Div("No server data available", style={'text-align': 'center', 'margin': '20px'})

	server_name = metrics[0]['server_name']
	historical_data = get_historical_metrics(server_name, 24)


	if not historical_data:
		return html.Div(f"No historical data available for {server_name}", style={'text-align': 'center'})

	df = pd.DataFrame(historical_data)
	if not df.empty:
		df['timestamp'] = pd.to_datetime(df['timestamp'])

	# Create comprehensive multi-metric dashboard
	fig = make_subplots(
		rows=2, cols=2,
		subplot_titles=('CPU Load', 'Memory Usage',
						'Disk Usage', 'User Activity'),
		specs=[[{'secondary_y': False}, {'secondary_y': False}],
			   [{'secondary_y': False}, {'secondary_y': True}]]
	)

	# CPU Load with multiple averages
	fig.add_trace(
		go.Scatter(
			x=df['timestamp'],
			y=df['cpu_load_1min'],
			mode='lines',
			name='1-min Load',
			line=dict(color=KU_COLORS['primary'], width=2)
		),
		row=1, col=1
	)
	fig.add_trace(
		go.Scatter(
			x=df['timestamp'],
			y=df['cpu_load_5min'],
			mode='lines',
			name='5-min Load',
			line=dict(color=KU_COLORS['secondary'], width=2)
		),
		row=1, col=1
	)

	# Memory Usage with threshold lines
	fig.add_trace(
		go.Scatter(
			x=df['timestamp'],
			y=df['ram_percentage'],
			mode='lines+markers',
			name='RAM %',
			line=dict(color=KU_COLORS['warning'], width=3),
			marker=dict(size=4)
		),
		row=1, col=2
	)
	# Add critical threshold line
	fig.add_hline(y=90, line_dash="dash", line_color=KU_COLORS['danger'],
				  annotation_text="Critical", row=1, col=2)
	fig.add_hline(y=75, line_dash="dot", line_color=KU_COLORS['warning'],
				  annotation_text="Warning", row=1, col=2)

	# Disk Usage
	fig.add_trace(
		go.Scatter(
			x=df['timestamp'],
			y=df['disk_percentage'],
			mode='lines+markers',
			name='Disk %',
			line=dict(color=KU_COLORS['primary'], width=3),
			marker=dict(size=4),
			fill='tonexty'
		),
		row=2, col=1
	)

	# User Activity (dual y-axis)
	fig.add_trace(
		go.Scatter(
			x=df['timestamp'],
			y=df['logged_users'],
			mode='lines+markers',
			name='Logged Users',
			line=dict(color=KU_COLORS['info'], width=2)
		),
		row=2, col=2
	)
	fig.add_trace(
		go.Scatter(
			x=df['timestamp'],
			y=df['tcp_connections'],
			mode='lines+markers',
			name='TCP Connections',
			line=dict(color=KU_COLORS['accent'], width=2),
			yaxis='y4'
		),
		row=2, col=2, secondary_y=True
	)

	fig.update_layout(
		height=800,
		showlegend=True,
		title_text=f"Comprehensive Performance Analytics - {server_name}",
		title_x=0.5,
		title_font_size=20,
		legend=dict(
			orientation="h",
			yanchor="bottom",
			y=1.02,
			xanchor="right",
			x=1
		)
	)

	return html.Div([
		# Server and time range selectors
		html.Div([
					html.Label("Select Server:", style={
							   'margin-right': '10px', 'font-weight': '600'}),
					dcc.Dropdown(
						id='enhanced-server-selector',
						options=[{'label': m['server_name'],
								  'value': m['server_name']} for m in metrics],
						value=server_name,
						style={'width': '300px', 'marginRight': '20px'}
					),
					html.Label("Time Range:", style={
							   'margin-right': '10px', 'font-weight': '600'}),
					dcc.Dropdown(
						id='enhanced-time-range-selector',
						options=[
							{'label': 'Last 6 Hours', 'value': 6},
							{'label': 'Last 12 Hours', 'value': 12},
							{'label': 'Last 24 Hours', 'value': 24},
							{'label': 'Last 3 Days', 'value': 72},
							{'label': 'Last Week', 'value': 168}
						],
						value=24,
						style={'width': '200px'}
					)
					], style={'display': 'flex', 'align-items': 'center', 'margin-bottom': '20px'}),

		# Main analytics chart
		dcc.Graph(id='enhanced-analytics-chart', figure=fig),

		# Performance summary
		html.Div([
			html.H4("Performance Summary", style={
				'margin': '20px 0 16px 0', 'color': KU_COLORS['text_primary']}),
			html.Div(id='performance-summary')
		])
	])

# Callbacks


@app.callback(
	[Output('system-overview', 'children'),
	 Output('alerts-panel', 'children'),
	 Output('enhanced-server-cards', 'children'),
	 Output('last-updated', 'children')],
	[Input('interval-component', 'n_intervals'),
	 Input('refresh-button', 'n_clicks'),
	 Input('refresh-alerts', 'n_clicks')]
)
def update_main_dashboard(n_intervals, refresh_clicks, alert_refresh):
	return (
		create_system_overview(),
		create_alert_panel(),
		create_enhanced_server_cards(),
		f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
	)


@app.callback(
	Output('enhanced-users-table', 'children'),
	[Input('interval-component', 'n_intervals'),
	 Input('refresh-button', 'n_clicks')]
)
def update_users_table(n_intervals, n_clicks):
	return create_enhanced_users_table()


@app.callback(
	Output('network-monitor', 'children'),
	[Input('interval-component', 'n_intervals'),
	 Input('refresh-button', 'n_clicks')]
)
def update_network_monitor(n_intervals, n_clicks):
	return create_network_monitor()


@app.callback(
	Output('enhanced-historical-graphs', 'children'),
	[Input('interval-component', 'n_intervals'),
	 Input('refresh-button', 'n_clicks')]
)
def update_historical_graphs(n_intervals, n_clicks):
	return create_enhanced_historical_graphs()


@app.callback(
	[Output('enhanced-analytics-chart', 'figure'),
	 Output('performance-summary', 'children')],
	[Input('enhanced-server-selector', 'value'),
	 Input('enhanced-time-range-selector', 'value'),
	 Input('interval-component', 'n_intervals')]
)
def update_analytics_chart(server_name, time_range, n_intervals):
	if not server_name:
		return {}, html.Div("No server selected")

	historical_data = get_historical_metrics(server_name, time_range or 24)

	if not historical_data:
		return {}, html.Div(f"No data available for {server_name}")

	df = pd.DataFrame(historical_data)
	if not df.empty:
		df['timestamp'] = pd.to_datetime(df['timestamp'])

	for col in ['cpu_load_1min', 'cpu_load_5min', 'cpu_load_15min', 'ram_percentage', 'disk_percentage', 'logged_users', 'tcp_connections']:
		if col in df.columns:
			df[col] = pd.to_numeric(df[col], errors='coerce')

	# Create the comprehensive chart
	fig = make_subplots(
		rows=2, cols=2,
		subplot_titles=('CPU Load Averages', 'Memory Usage',
						'Disk Usage', 'Network Activity'),
		specs=[[{'secondary_y': False}, {'secondary_y': False}],
			   [{'secondary_y': False}, {'secondary_y': True}]]
	)

	# CPU Load
	fig.add_trace(go.Scatter(x=df['timestamp'], y=df['cpu_load_1min'],
							 mode='lines', name='1-min Load',
							 line=dict(color=KU_COLORS['primary'], width=2)), row=1, col=1)
	fig.add_trace(go.Scatter(x=df['timestamp'], y=df['cpu_load_5min'],
							 mode='lines', name='5-min Load',
							 line=dict(color=KU_COLORS['secondary'], width=2)), row=1, col=1)

	# Memory Usage
	fig.add_trace(go.Scatter(x=df['timestamp'], y=df['ram_percentage'],
							 mode='lines+markers', name='RAM %',
							 line=dict(color=KU_COLORS['warning'], width=3)), row=1, col=2)

	# Disk Usage
	fig.add_trace(go.Scatter(x=df['timestamp'], y=df['disk_percentage'],
							 mode='lines+markers', name='Disk %',
							 line=dict(color=KU_COLORS['primary'], width=3)), row=2, col=1)

	# Network Activity
	fig.add_trace(go.Scatter(x=df['timestamp'], y=df['logged_users'],
							 mode='lines+markers', name='Users',
							 line=dict(color=KU_COLORS['info'], width=2)), row=2, col=2)
	fig.add_trace(go.Scatter(x=df['timestamp'], y=df['tcp_connections'],
							 mode='lines+markers', name='Connections',
							 line=dict(color=KU_COLORS['accent'], width=2)), row=2, col=2, secondary_y=True)

	fig.update_layout(height=800, showlegend=True,
					  title_text=f"Performance Analytics - {server_name}")

	# Performance Summary
	latest_data = df.iloc[-1] if not df.empty else {}
	avg_cpu = df['cpu_load_5min'].mean() if not df.empty else 0
	max_ram = df['ram_percentage'].max() if not df.empty else 0
	avg_disk = df['disk_percentage'].mean() if not df.empty else 0

	summary = html.Div([
		html.Div([
			html.Div(f"{avg_cpu:.2f}", className="stat-value"),
			html.Div("Avg CPU Load", className="stat-label")
		], className="overview-stat"),
		html.Div([
			html.Div(f"{max_ram:.1f}%", className="stat-value"),
			html.Div("Peak Memory", className="stat-label")
		], className="overview-stat"),
		html.Div([
			html.Div(f"{avg_disk:.1f}%", className="stat-value"),
			html.Div("Avg Disk Usage", className="stat-label")
		], className="overview-stat")
	], style={'display': 'flex', 'gap': '20px', 'margin': '20px 0'})

	return fig, summary


if __name__ == '__main__':
	app.run(debug=True, host='0.0.0.0', port=3000)
