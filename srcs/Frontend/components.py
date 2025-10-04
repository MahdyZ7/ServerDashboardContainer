# UI components for the Server Monitoring Dashboard
import dash
from dash import dcc, html, dash_table
import plotly.express as px
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime
import logging

from config import KU_COLORS, TABLE_CONFIG, CHART_CONFIG, LAYOUT_CONFIG
from api_client import get_latest_server_metrics, get_top_users, get_historical_metrics
from utils import (determine_server_status, get_performance_rating, generate_alerts,
                   safe_float, get_status_badge_class, get_performance_badge_class,
                   is_high_usage_user, sanitize_server_name)
from validation import validate_timestamp, safe_get
from data_processing import (safe_create_dataframe, parse_dataframe_timestamps,
                            convert_numeric_columns, prepare_historical_dataframe)

logger = logging.getLogger(__name__)


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

    avg_cpu = np.mean([safe_float(m.get('cpu_load_5min', 0))
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
            ], className="overview-stat"),

            html.Div([
                html.Span(f"{online_servers}", className="stat-value"),
                html.Div("Online Servers", className="stat-label"),
            ], className="overview-stat"),

            html.Div([
                html.Span(f"{warning_servers}",
                          className="stat-value"),
                html.Div("Servers with Warnings",
                         className="stat-label"),
                html.Div(
                    "Requires attention" if warning_servers > 0 else "No action needed", className="stat-change negative" if warning_servers > 0 else "stat-change positive")
            ], className="overview-stat"),

            html.Div([
                html.Span(f"{offline_servers}",
                          className="stat-value"),
                html.Div("Offline Servers", className="stat-label"),
                html.Div(
                    "Check connectivity" if offline_servers > 0 else "No action needed", className="stat-change negative" if offline_servers > 0 else "stat-change positive")
            ], className="overview-stat"),

            html.Div([
                html.Span(f"{avg_cpu:.1f}", className="stat-value"),
                html.Div("Avg CPU Load", className="stat-label"),
                html.Div("5-minute average", className="stat-change")
            ], className="overview-stat"),

            html.Div([
                html.Span(f"{avg_ram:.1f}%", className="stat-value"),
                html.Div("Avg RAM Usage", className="stat-label"),
                html.Div("Across all servers", className="stat-change")
            ], className="overview-stat"),

            html.Div([
                html.Span(f"{total_users}", className="stat-value"),
                html.Div("Users", className="stat-label"),
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
    for alert in alerts[:TABLE_CONFIG['max_alerts']]:  # Show only top 5 alerts
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

def create_compact_server_grid():
    """Create grid of compact server cards with maximum data density"""
    metrics = get_latest_server_metrics()

    if not metrics:
        return html.Div([
            html.Div("No server data available",
                    style={'textAlign': 'center', 'padding': '40px', 'color': '#6C757D'})
        ], className="server-grid")

    server_cards = []

    for metric in metrics:
        server_name = metric.get('server_name', 'Unknown')
        status = determine_server_status(metric)

        # Extract key metrics
        cpu_load = safe_float(metric.get('cpu_load_5min', 0))
        ram_percent = metric.get('ram_percentage', 0)
        disk_percent = metric.get('disk_percentage', 0)
        users = metric.get('logged_users', 0)

        # Determine metric value classes for color coding
        cpu_class = 'critical' if cpu_load > 80 else 'warning' if cpu_load > 50 else ''
        ram_class = 'critical' if ram_percent > 95 else 'warning' if ram_percent > 85 else ''
        disk_class = 'critical' if disk_percent > 95 else 'warning' if disk_percent > 85 else ''

        server_card = html.Div([
            # Server Header
            html.Div([
                html.Div(server_name, className="server-name"),
                html.Div([
                    html.Div(className="status-indicator"),
                    html.Span(status.upper())
                ], className=f"server-status {status}")
            ], className="server-header"),

            # Inline Metrics Row
            html.Div([
                html.Div([
                    html.Div("CPU", className="metric-inline-label"),
                    html.Div(f"{cpu_load:.1f}", className=f"metric-inline-value {cpu_class}")
                ], className="metric-inline"),

                html.Div([
                    html.Div("RAM", className="metric-inline-label"),
                    html.Div(f"{ram_percent:.0f}%", className=f"metric-inline-value {ram_class}")
                ], className="metric-inline"),

                html.Div([
                    html.Div("DISK", className="metric-inline-label"),
                    html.Div(f"{disk_percent:.0f}%", className=f"metric-inline-value {disk_class}")
                ], className="metric-inline"),

                html.Div([
                    html.Div("USERS", className="metric-inline-label"),
                    html.Div(f"{users}", className="metric-inline-value")
                ], className="metric-inline")
            ], className="metrics-row"),

        ], className="server-card", style={'padding': '0px', 'border-radius': '10px'}, **{'data-server': sanitize_server_name(server_name)})

        server_cards.append(server_card)

    return html.Div(server_cards, className="server-grid")


def create_enhanced_server_cards():
    """Create enhanced server cards with detailed information"""
    metrics = get_latest_server_metrics()

    if not metrics:
        return html.Div("No server data available", style={'text-align': 'center', 'margin': '20px'})

    server_cards = []

    for metric in metrics:
        server_name = metric.get('server_name', 'Unknown')
        historical_data = get_historical_metrics(server_name, CHART_CONFIG['default_time_range'])
        status = determine_server_status(metric)

        # Get performance rating
        cpu_load = safe_float(metric.get('cpu_load_5min', 0))
        ram_percentage = metric.get('ram_percentage', 0)
        disk_percentage = metric.get('disk_percentage', 0)

        perf_rating, perf_color = get_performance_rating(
            cpu_load, ram_percentage, disk_percentage)

        # Status badge styling
        status_class = get_status_badge_class(status)
        status_text = status.upper()

        # Format timestamp with error handling
        timestamp_raw = metric.get('timestamp', 'Unknown')
        try:
            timestamp_dt = validate_timestamp(timestamp_raw)
            timestamp_str = timestamp_dt.strftime('%b %d, %Y %H:%M')
        except Exception as e:
            logger.warning(f"Failed to parse timestamp {timestamp_raw}: {e}")
            timestamp_str = str(timestamp_raw) if timestamp_raw != 'Unknown' else 'Unknown'

        # Historical dataframe with improved error handling
        # fig = make_subplots(rows=1, cols=1,
                            # subplot_titles=(f"Load History - {server_name}",))
        fig = go.Figure()
        fig.layout.title = f"24H Load History"
        fig.layout.xaxis.title = "Time"
        fig.layout.yaxis.title = "Load (%)"
        fig.update_layout(title_x=0.5)
        fig.update_yaxes(range=[-5, 110])

        if historical_data and len(historical_data) > 0:
            try:
                # Use the new data processing utility
                df = prepare_historical_dataframe(historical_data, server_name)
                df['cpu_load_15min'] = df['cpu_load_15min'].replace(['', None, 'N/A'], np.nan)
                df['ram_percentage'] = df['ram_percentage'].replace(['', None, 'N/A'], np.nan)
                df['disk_percentage'] = df['disk_percentage'].replace(['', None, 'N/A'], np.nan)

                if not df.empty and 'timestamp' in df.columns:
                    # Add traces only if data exists
                    if 'cpu_load_15min' in df.columns:
                        fig.add_trace(
                            go.Scatter(
                                x=df['timestamp'],
                                y=df['cpu_load_15min'],
                                mode='lines+text',
                                name='CPU Load',
                                line=dict(color=KU_COLORS['primary'], width=2),
                                text=['CPU Load' if i == len(df)-1 else '' for i in range(len(df))],
                                textposition='top left',
                                textfont=dict(size=12, color=KU_COLORS['primary']),
                                showlegend=False
                            ),
                        )

                    if 'ram_percentage' in df.columns:
                        fig.add_trace(
                            go.Scatter(
                                x=df['timestamp'],
                                y=df['ram_percentage'],
                                mode='lines+text',
                                name='RAM Usage',
                                line=dict(color=KU_COLORS['secondary'], width=2),
                                text=['RAM Usage' if i == len(df)-1 else '' for i in range(len(df))],
                                textposition='top left',
                                textfont=dict(size=12, color=KU_COLORS['secondary']),
                                showlegend=False
                            ),
                        )

                    if 'disk_percentage' in df.columns:
                        fig.add_trace(
                            go.Scatter(
                                x=df['timestamp'],
                                y=df['disk_percentage'],
                                mode='lines+text',
                                name='Disk Usage',
                                line=dict(color=KU_COLORS['accent'], width=2),
                                text=['Disk Usage' if i == len(df)-1 else '' for i in range(len(df))],
                                textposition='top left',
                                textfont=dict(size=12, color=KU_COLORS['accent']),
                                showlegend=False
                            ),
                        )
                else:
                    # Data preparation failed
                    fig.add_annotation(
                        text="Historical data processing failed",
                        xref="paper", yref="paper",
                        x=0.5, y=0.5, showarrow=False,
                        font=dict(size=16, color="gray")
                    )
            except Exception as e:
                logger.error(f"Error creating historical graph for {server_name}: {e}")
                # If anything fails, create empty graph with message
                fig.add_annotation(
                    text="Historical data unavailable",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=16, color="gray")
                )
        else:
            # No historical data available
            fig.add_annotation(
                text="No historical data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color="gray")
            )

        fig.update_layout(
            showlegend=False,
            # height=10,
            margin=dict(l=40, r=40, t=40, b=40),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
            
        )
        # Fix y-axis range to be consistent across all server cards
        # fig.update_yaxes(range=[0, 110])
        

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
                        perf_rating.upper(), className=f"performance-indicator {get_performance_badge_class(perf_rating)}")
                ])
            ], className="server-header"),

            # Historical Data Graph
            html.Div([
                dcc.Graph(figure=fig, style={'height': '400px'})
            ], style={'margin': '16px 0'}),

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
                    html.Span("RAM Usage", className="metric-label")
                ], className="metric-item"),

                html.Div([
                    html.Span(f"{disk_percentage}%", className="metric-value", style={
                        'color': KU_COLORS['danger'] if disk_percentage > 85 else KU_COLORS['warning'] if disk_percentage > 70 else KU_COLORS['primary']}),
                    html.Span("Disk Usage", className="metric-label")
                ], className="metric-item"),

                html.Div([
                    html.Span(f"{metric.get('logged_users', 0)}",
                              className="metric-value"),
                    html.Span("Connected Users", className="metric-label")
                ], className="metric-item"),
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
                    html.Div(f"Memory: {metric.get('ram_used', 0):} / {metric.get('ram_total', 0)}", style={
                        'fontSize': '12px', 'marginBottom': '4px', 'fontWeight': '600'}),
                    html.Div([
                        html.Div(className="resource-fill resource-memory",
                                 style={'width': f'{ram_percentage}%'})
                    ], className="resource-bar")
                ]),
                html.Div([
                    html.Div(f"Disk: {metric.get('disk_used', 0)} / {metric.get('disk_total', 0)}", style={
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
                        f"{metric.get('operating_system', 'Unknown')}", className="detail-value")
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
                    html.Span(timestamp_str,
                              className="detail-value")
                ], className="detail-row")
            ], className="server-details")

        ], className="server-card")

        server_cards.append(card)

    # Organize in responsive grid
    return html.Div(server_cards, style={
        'display': 'grid',
        'grid-template-columns': f'repeat(auto-fit, minmax({LAYOUT_CONFIG["server_card_min_width"]}, 1fr))',
        'gap': LAYOUT_CONFIG['card_gap'],
        'margin': '20px 0'
    })


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
                    page_size=TABLE_CONFIG['network_page_size']
                )
            ], className="enhanced-table")
        ])
    ])

def create_enhanced_users_table():
    """Create enhanced users table with more details"""
    users_data = get_top_users()

    if not users_data:
        return html.Div("No user data available", style={'text-align': 'center', 'margin': '20px', 'padding': '20px', 'background': '#f8f9fa', 'border-radius': '8px'})

    # Group users by server
    servers = {}
    total_users = len(users_data)

    high_usage_users = len([
        u for u in users_data
        if is_high_usage_user(u)
    ])


    for user in users_data:
        server_name = user['server_name']
        if server_name not in servers:
            servers[server_name] = []
        servers[server_name].append(user)

        # Format last_login for display while keeping it sortable
        if user['last_login']:
            try:
                dt = datetime.strptime(user['last_login'], '%Y-%m-%dT%H:%M:%S')
                user['last_login'] = dt.strftime('%Y-%m-%d')
            except Exception:
                pass  # Keep original format if parsing fails

    # Summary statistics
    summary = html.Div([
        html.Div([
            html.Span(f"{total_users}", className="stat-value"),
            html.Div("Total Users", className="stat-label"),
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
        table = dash_table.DataTable(
            id=f'users-table-{sanitize_server_name(server_name)}',
            columns=[
                {'name': 'Username', 'id': 'username'},
                {'name': 'CPU Usage (%)', 'id': 'cpu', 'type': 'numeric'},
                {'name': 'Memory Usage (%)', 'id': 'mem', 'type': 'numeric'},
                {'name': 'Disk Usage (GB)', 'id': 'disk', 'type': 'numeric'},
                {'name': 'Processes', 'id': 'process_count', 'type': 'numeric'},
                {'name': 'Top Process', 'id': 'top_process'},
                {'name': 'Last Login', 'id': 'last_login', 'type': 'datetime'},
                {'name': 'Full Name', 'id': 'full_name'},
                {'name': 'Status', 'id': 'status'},
            ],
            data=[{
                **user,
                'cpu': float(user['cpu']),
                'mem': float(user['mem']),
                'disk': float(user['disk']),
                'process_count': int(user['process_count']),
                'last_login': user['last_login'],
                'status': 'High Usage' if is_high_usage_user(user) else 'Normal'
            } for user in users],
            style_table={
                'overflowX': 'auto',
                'borderRadius': '10px'
            },
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
                    'if': {'row_index': 'odd'},
                    'backgroundColor': '#f7f7fa'
                },
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
            page_size=TABLE_CONFIG['users_page_size']
        )

        tab = dcc.Tab(
            label=f"{server_name} ({len(users)})",
            value=server_name,
            children=[table],
            style={'padding': '15px', 'fontSize': '14px',
                   'borderRadius': '60px'},
            selected_style={
                'backgroundColor': KU_COLORS['primary'],
                'color': 'white',
                'padding': '15px',
                'fontSize': '14px',
                'fontWeight': '600',
                'borderRadius': '60px',
            }
        )
        tabs.append(tab)

    return html.Div([
        summary,
        dcc.Tabs(id='enhanced-user-tabs', value=list(servers.keys())[0] if servers else '',
                 children=tabs, style={'margin': '20px 0'})
    ])


def create_enhanced_historical_graphs():
    """Create enhanced historical graphs with better visualizations"""
    metrics = get_latest_server_metrics()

    if not metrics:
        return html.Div("No server data available", style={'text-align': 'center', 'margin': '20px'})

    server_name = metrics[0]['server_name']
    historical_data = get_historical_metrics(
        server_name, CHART_CONFIG['default_time_range'])

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
    fig.add_trace(
        go.Scatter(
            x=df['timestamp'],
            y=df['cpu_load_15min'],
            mode='lines',
            name='15-min Load',
            line=dict(color=KU_COLORS['primary'], width=2)
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
        height=CHART_CONFIG['default_height'],
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
                options=CHART_CONFIG['time_ranges'],
                value=CHART_CONFIG['default_time_range'],
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
