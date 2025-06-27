# Callback functions for the Server Monitoring Dashboard
from dash import Input, Output, callback
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime

from config import KU_COLORS, CHART_CONFIG
from components import (create_system_overview, create_alert_panel, create_enhanced_server_cards,
                       create_enhanced_users_table, create_network_monitor, create_enhanced_historical_graphs)
from api_client import get_historical_metrics
from utils import safe_float


def register_callbacks(app):
    """Register all dashboard callbacks"""
    
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
        """Update main dashboard components"""
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
        """Update users table"""
        return create_enhanced_users_table()

    @app.callback(
        Output('network-monitor', 'children'),
        [Input('interval-component', 'n_intervals'),
         Input('refresh-button', 'n_clicks')]
    )
    def update_network_monitor(n_intervals, n_clicks):
        """Update network monitor"""
        return create_network_monitor()

    @app.callback(
        Output('enhanced-historical-graphs', 'children'),
        [Input('interval-component', 'n_intervals'),
         Input('refresh-button', 'n_clicks')]
    )
    def update_historical_graphs(n_intervals, n_clicks):
        """Update historical graphs"""
        return create_enhanced_historical_graphs()

    @app.callback(
        [Output('enhanced-analytics-chart', 'figure'),
         Output('performance-summary', 'children')],
        [Input('enhanced-server-selector', 'value'),
         Input('enhanced-time-range-selector', 'value'),
         Input('interval-component', 'n_intervals')]
    )
    def update_analytics_chart(server_name, time_range, n_intervals):
        """Update analytics chart based on server and time range selection"""
        if not server_name:
            from dash import html
            return {}, html.Div("No server selected")

        historical_data = get_historical_metrics(server_name, time_range or CHART_CONFIG['default_time_range'])

        if not historical_data:
            from dash import html
            return {}, html.Div(f"No data available for {server_name}")

        df = pd.DataFrame(historical_data)
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])

        # Convert columns to numeric
        for col in ['cpu_load_1min', 'cpu_load_5min', 'cpu_load_15min', 'ram_percentage', 
                   'disk_percentage', 'logged_users', 'tcp_connections']:
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

        fig.update_layout(height=CHART_CONFIG['default_height'], showlegend=True,
                          title_text=f"Performance Analytics - {server_name}")

        # Performance Summary
        latest_data = df.iloc[-1] if not df.empty else {}
        avg_cpu = df['cpu_load_5min'].mean() if not df.empty else 0
        max_ram = df['ram_percentage'].max() if not df.empty else 0
        avg_disk = df['disk_percentage'].mean() if not df.empty else 0

        from dash import html
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