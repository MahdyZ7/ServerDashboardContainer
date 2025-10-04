# Enhanced callback functions with toast notifications
from dash import Input, Output, State, callback, dcc, html
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime
import logging

from config import KU_COLORS, CHART_CONFIG
from components import (create_system_overview, create_alert_panel, create_enhanced_server_cards,
                       create_enhanced_users_table, create_network_monitor, create_enhanced_historical_graphs,
                       create_compact_server_grid)
from api_client import get_historical_metrics, invalidate_all_caches, get_cache_stats
from utils import safe_float
from export_utils import generate_export_report, export_to_excel
from refresh_utils import trigger_dashboard_refresh, get_refresh_status_message
from toast_utils import (create_success_toast, create_error_toast, create_warning_toast,
                        create_info_toast, create_toast_container, format_api_error_message)

logger = logging.getLogger(__name__)


def register_callbacks(app):
    """Register all dashboard callbacks with toast notifications"""

    @app.callback(
        [Output('system-overview', 'children'),
         Output('enhanced-server-cards', 'children'),
         Output('last-updated', 'children'),
         Output('toast-container', 'children')],
        [Input('interval-component', 'n_intervals'),
         Input('refresh-button', 'n_clicks')],
        prevent_initial_call=False
    )
    def update_main_dashboard(n_intervals, refresh_clicks):
        """Update main dashboard components with toast feedback"""
        toasts = []

        try:
            # Trigger refresh if manual button clicked
            if refresh_clicks and refresh_clicks > 0:
                logger.info("Manual refresh triggered")
                invalidate_all_caches()
                toasts.append(create_info_toast("Refreshing data..."))

            # Update components
            system_overview = create_system_overview()
            server_cards = create_enhanced_server_cards()
            timestamp = f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

            # Add success toast on manual refresh
            if refresh_clicks and refresh_clicks > 0:
                cache_stats = get_cache_stats()
                toasts = [create_success_toast(
                    f"Dashboard refreshed successfully! Cache hit rate: {cache_stats.get('hit_rate', 0):.1f}%"
                )]

            return (
                system_overview,
                server_cards,
                timestamp,
                create_toast_container(toasts).children if toasts else []
            )

        except Exception as e:
            logger.error(f"Error updating main dashboard: {e}", exc_info=True)
            toasts = [create_error_toast("Failed to update dashboard. Please try again.")]
            return (
                html.Div("Error loading data"),
                html.Div("Error loading data"),
                f"Error at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                create_toast_container(toasts).children
            )

    @app.callback(
        Output('enhanced-users-table', 'children'),
        [Input('interval-component', 'n_intervals'),
         Input('refresh-button', 'n_clicks')]
    )
    def update_users_table(n_intervals, n_clicks):
        """Update users table with error handling"""
        try:
            return create_enhanced_users_table()
        except Exception as e:
            logger.error(f"Error updating users table: {e}", exc_info=True)
            return html.Div("Error loading user data",
                          style={'textAlign': 'center', 'padding': '20px', 'color': KU_COLORS['danger']})

    @app.callback(
        Output('network-monitor', 'children'),
        [Input('interval-component', 'n_intervals'),
         Input('refresh-button', 'n_clicks')]
    )
    def update_network_monitor(n_intervals, n_clicks):
        """Update network monitor with error handling"""
        try:
            return create_network_monitor()
        except Exception as e:
            logger.error(f"Error updating network monitor: {e}", exc_info=True)
            return html.Div("Error loading network data",
                          style={'textAlign': 'center', 'padding': '20px', 'color': KU_COLORS['danger']})

    @app.callback(
        Output('enhanced-historical-graphs', 'children'),
        [Input('interval-component', 'n_intervals'),
         Input('refresh-button', 'n_clicks')]
    )
    def update_historical_graphs(n_intervals, n_clicks):
        """Update historical graphs with error handling"""
        try:
            return create_enhanced_historical_graphs()
        except Exception as e:
            logger.error(f"Error updating historical graphs: {e}", exc_info=True)
            return html.Div("Error loading historical data",
                          style={'textAlign': 'center', 'padding': '20px', 'color': KU_COLORS['danger']})

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
            return {}, html.Div("No server selected")

        try:
            historical_data = get_historical_metrics(server_name, time_range or CHART_CONFIG['default_time_range'])

            if not historical_data:
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
                                    mode='lines', name='1-min Load', line_shape='spline',
                                    line=dict(color=KU_COLORS['primary'], width=2)), row=1, col=1)
            fig.add_trace(go.Scatter(x=df['timestamp'], y=df['cpu_load_5min'],
                                    mode='lines', name='5-min Load', line_shape='spline',
                                    line=dict(color=KU_COLORS['secondary'], width=2)), row=1, col=1)
            fig.add_trace(go.Scatter(x=df['timestamp'], y=df['cpu_load_15min'],
                                    mode='lines', name='15-min Load', line_shape='spline',
                                    line=dict(color=KU_COLORS['accent'], width=2)), row=1, col=1)
            fig.update_yaxes(title_text="CPU Load %", range=[0,100], row=1, col=1)
            fig.update_xaxes(title_text="Time", row=1, col=1, tickformat="%H:%M\n%b %d")

            # Memory Usage
            fig.add_trace(go.Scatter(x=df['timestamp'], y=df['ram_percentage'],
                                    mode='lines+markers', name='RAM %',
                                    line=dict(color=KU_COLORS['warning'], width=3)), row=1, col=2)
            fig.update_yaxes(title_text="Memory Usage %", range=[0,100], row=1, col=2)
            fig.update_xaxes(title_text="Time", row=1, col=2, tickformat="%H:%M\n%b %d")

            # Disk Usage
            fig.add_trace(go.Scatter(x=df['timestamp'], y=df['disk_percentage'],
                                    mode='lines+markers', name='Disk %',
                                    line=dict(color=KU_COLORS['primary'], width=3)), row=2, col=1)
            fig.update_yaxes(title_text="Disk Usage %", range=[0,100], row=2, col=1)
            fig.update_xaxes(title_text="Time", row=2, col=1, tickformat="%H:%M\n%b %d")

            # Network Activity
            fig.add_trace(go.Scatter(x=df['timestamp'], y=df['logged_users'],
                                    mode='lines+markers', name='Users', line_shape='hv',
                                    line=dict(color=KU_COLORS['info'], width=2)), row=2, col=2)
            fig.add_trace(go.Scatter(x=df['timestamp'], y=df['tcp_connections'],
                                    mode='lines+markers', name='TCP Connections',
                                    line=dict(color=KU_COLORS['accent'], width=2)), row=2, col=2, secondary_y=True)
            fig.update_yaxes(title_text="No. of Users", range=[0, df['logged_users'].max()*1.2 if not df['logged_users'].empty else 10], row=2, col=2,
                             secondary_y=False)
            fig.update_yaxes(title_text="TCP Connections", range=[0, df['tcp_connections'].max()*1.2 if not df['tcp_connections'].empty else 10], row=2, col=2,
                             secondary_y=True)
            fig.update_xaxes(title_text="Time", row=2, col=2, tickformat="%H:%M\n%b %d")
            fig.update_layout(height=CHART_CONFIG['default_height'], showlegend=True,
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

        except Exception as e:
            logger.error(f"Error updating analytics chart: {e}", exc_info=True)
            return {}, html.Div(f"Error loading analytics for {server_name}",
                              style={'color': KU_COLORS['danger']})

    @app.callback(
        [Output('download-report', 'data'),
         Output('toast-container', 'children', allow_duplicate=True)],
        Input('export-button', 'n_clicks'),
        prevent_initial_call=True
    )
    def export_report(n_clicks):
        """Handle export button click with toast feedback"""
        if n_clicks:
            try:
                logger.info("Export report requested")
                # Generate export data
                export_data = generate_export_report()

                if export_data:
                    # Export to Excel
                    filepath = export_to_excel(export_data)

                    if filepath:
                        logger.info(f"Report exported successfully: {filepath}")
                        toast = create_success_toast("Report exported successfully!")
                        return dcc.send_file(filepath), create_toast_container([toast]).children
                    else:
                        logger.error("Failed to create Excel file")
                        toast = create_error_toast("Failed to create export file")
                        return None, create_toast_container([toast]).children
                else:
                    logger.error("Failed to generate export data")
                    toast = create_warning_toast("No data available to export")
                    return None, create_toast_container([toast]).children

            except Exception as e:
                logger.error(f"Error in export callback: {e}", exc_info=True)
                toast = create_error_toast("Export failed. Please try again.")
                return None, create_toast_container([toast]).children

        return None, []

    @app.callback(
        Output('server-grid', 'children'),
        [Input('refresh-button', 'n_clicks'),
         Input('interval-component', 'n_intervals')],
        prevent_initial_call=False
    )
    def refresh_server_grid(n_clicks, n_intervals):
        """Refresh server grid when refresh button is clicked or interval triggers"""
        try:
            return create_compact_server_grid()
        except Exception as e:
            logger.error(f"Error refreshing server grid: {e}", exc_info=True)
            return html.Div("Error loading server grid",
                          style={'textAlign': 'center', 'padding': '20px', 'color': KU_COLORS['danger']})
