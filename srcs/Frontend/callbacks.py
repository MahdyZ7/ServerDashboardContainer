# Callback functions for the Server Monitoring Dashboard
from dash import Input, Output, dcc
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime
import logging

from config import KU_COLORS, CHART_CONFIG
from components import (
    create_system_overview,
    create_alert_panel,
    create_enhanced_server_cards,
    create_enhanced_users_table,
    create_network_monitor,
    create_enhanced_historical_graphs,
)
from api_client import get_historical_metrics
from export_utils import generate_export_report, export_to_excel
from graph_config import (
    GRAPH_COLORS,
    ENHANCED_LAYOUT,
    ENHANCED_XAXIS,
    ENHANCED_YAXIS,
)


def register_callbacks(app):
    """Register all dashboard callbacks"""

    @app.callback(
        [
            Output("system-overview", "children"),
            Output("alerts-panel", "children"),
            Output("enhanced-server-cards", "children"),
            Output("last-updated", "children"),
        ],
        [
            Input("interval-component", "n_intervals"),
            Input("refresh-button", "n_clicks"),
            Input("refresh-alerts", "n_clicks"),
        ],
    )
    def update_main_dashboard(n_intervals, refresh_clicks, alert_refresh):
        """Update main dashboard components"""

        return (
            create_system_overview(),
            create_alert_panel(),
            create_enhanced_server_cards(),
            f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        )

    @app.callback(
        Output("enhanced-users-table", "children"),
        [
            Input("interval-component", "n_intervals"),
            Input("refresh-button", "n_clicks"),
        ],
    )
    def update_users_table(n_intervals, n_clicks):
        """Update users table"""
        return create_enhanced_users_table()

    @app.callback(
        Output("network-monitor", "children"),
        [
            Input("interval-component", "n_intervals"),
            Input("refresh-button", "n_clicks"),
        ],
    )
    def update_network_monitor(n_intervals, n_clicks):
        """Update network monitor"""
        return create_network_monitor()

    @app.callback(
        Output("enhanced-historical-graphs", "children"),
        [
            Input("interval-component", "n_intervals"),
            Input("refresh-button", "n_clicks"),
        ],
    )
    def update_historical_graphs(n_intervals, n_clicks):
        """Update historical graphs"""
        return create_enhanced_historical_graphs()

    @app.callback(
        [
            Output("enhanced-analytics-chart", "figure"),
            Output("performance-summary", "children"),
        ],
        [
            Input("enhanced-server-selector", "value"),
            Input("enhanced-time-range-selector", "value"),
            Input("interval-component", "n_intervals"),
        ],
    )
    def update_analytics_chart(server_name, time_range, n_intervals):
        """Update analytics chart based on server and time range selection"""
        if not server_name:
            from dash import html

            return {}, html.Div("No server selected")

        historical_data = get_historical_metrics(
            server_name, time_range or CHART_CONFIG["default_time_range"]
        )

        if not historical_data:
            from dash import html

            return {}, html.Div(f"No data available for {server_name}")

        df = pd.DataFrame(historical_data)
        if not df.empty:
            df["timestamp"] = pd.to_datetime(df["timestamp"])

        # Convert columns to numeric
        for col in [
            "cpu_load_1min",
            "cpu_load_5min",
            "cpu_load_15min",
            "ram_percentage",
            "disk_percentage",
            "logged_users",
            "tcp_connections",
        ]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # Create enhanced comprehensive chart with professional styling
        fig = make_subplots(
            rows=2,
            cols=2,
            subplot_titles=(
                "<b>CPU Load Averages</b>",
                "<b>Memory Usage</b>",
                "<b>Disk Usage</b>",
                "<b>Network Activity</b>",
            ),
            specs=[
                [{"secondary_y": False}, {"secondary_y": False}],
                [{"secondary_y": False}, {"secondary_y": True}],
            ],
            vertical_spacing=0.12,
            horizontal_spacing=0.1,
        )

        # Enhanced CPU Load traces with smooth curves and fills
        fig.add_trace(
            go.Scatter(
                x=df["timestamp"],
                y=df["cpu_load_1min"],
                mode="lines",
                name="1-min Load",
                line=dict(color=KU_COLORS["primary"], width=2.5, shape="spline", smoothing=1.0),
                fill="tozeroy",
                fillcolor=GRAPH_COLORS["cpu"]["fill"],
                hovertemplate="<b>1-min</b>: %{y:.2f}%<extra></extra>",
            ),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=df["timestamp"],
                y=df["cpu_load_5min"],
                mode="lines",
                name="5-min Load",
                line=dict(color=KU_COLORS["secondary"], width=2, shape="spline", smoothing=1.0),
                hovertemplate="<b>5-min</b>: %{y:.2f}%<extra></extra>",
                opacity=0.8,
            ),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=df["timestamp"],
                y=df["cpu_load_15min"],
                mode="lines",
                name="15-min Load",
                line=dict(color=KU_COLORS["accent"], width=1.5, shape="spline", smoothing=1.0, dash="dot"),
                hovertemplate="<b>15-min</b>: %{y:.2f}%<extra></extra>",
                opacity=0.6,
            ),
            row=1,
            col=1,
        )
        fig.update_yaxes(title_text="CPU Load %", range=[0, 100], row=1, col=1)
        fig.update_xaxes(title_text="Time", row=1, col=1, tickformat="%H:%M\n%b %d")

        # Enhanced Memory Usage with smooth curves and area fill
        fig.add_trace(
            go.Scatter(
                x=df["timestamp"],
                y=df["ram_percentage"],
                mode="lines",
                name="RAM Usage",
                line=dict(color=KU_COLORS["secondary"], width=3, shape="spline", smoothing=1.0),
                fill="tozeroy",
                fillcolor=GRAPH_COLORS["ram"]["fill"],
                hovertemplate="<b>RAM</b>: %{y:.1f}%<extra></extra>",
            ),
            row=1,
            col=2,
        )
        # Add threshold lines for memory
        fig.add_hline(
            y=90,
            line_dash="dash",
            line_color=GRAPH_COLORS["critical"]["line"],
            line_width=1.5,
            opacity=0.7,
            annotation_text="Critical (90%)",
            annotation_position="right",
            annotation_font=dict(size=10, color=GRAPH_COLORS["critical"]["line"]),
            row=1,
            col=2,
        )
        fig.add_hline(
            y=75,
            line_dash="dot",
            line_color=GRAPH_COLORS["warning"]["line"],
            line_width=1.5,
            opacity=0.7,
            annotation_text="Warning (75%)",
            annotation_position="right",
            annotation_font=dict(size=10, color=GRAPH_COLORS["warning"]["line"]),
            row=1,
            col=2,
        )
        fig.update_yaxes(title_text="Memory Usage %", range=[0, 100], row=1, col=2)
        fig.update_xaxes(title_text="Time", row=1, col=2, tickformat="%H:%M\n%b %d")

        # Enhanced Disk Usage with gradient fill
        fig.add_trace(
            go.Scatter(
                x=df["timestamp"],
                y=df["disk_percentage"],
                mode="lines",
                name="Disk Usage",
                line=dict(color=KU_COLORS["accent"], width=3, shape="spline", smoothing=1.0),
                fill="tozeroy",
                fillcolor=GRAPH_COLORS["disk"]["fill"],
                hovertemplate="<b>Disk</b>: %{y:.1f}%<extra></extra>",
            ),
            row=2,
            col=1,
        )
        fig.update_yaxes(title_text="Disk Usage %", range=[0, 100], row=2, col=1)
        fig.update_xaxes(title_text="Time", row=2, col=1, tickformat="%H:%M\n%b %d")

        # Enhanced Network Activity with smooth curves
        fig.add_trace(
            go.Scatter(
                x=df["timestamp"],
                y=df["logged_users"],
                mode="lines+markers",
                name="Logged Users",
                line=dict(color=GRAPH_COLORS["users"]["line"], width=2.5, shape="spline", smoothing=0.8),
                marker=dict(size=4, opacity=0.7),
                fill="tozeroy",
                fillcolor=GRAPH_COLORS["users"]["fill"],
                hovertemplate="<b>Users</b>: %{y}<extra></extra>",
            ),
            row=2,
            col=2,
        )
        fig.add_trace(
            go.Scatter(
                x=df["timestamp"],
                y=df["tcp_connections"],
                mode="lines+markers",
                name="TCP Connections",
                line=dict(color=GRAPH_COLORS["network"]["line"], width=2.5, shape="spline", smoothing=0.8),
                marker=dict(size=4, opacity=0.7, symbol="diamond"),
                hovertemplate="<b>Connections</b>: %{y}<extra></extra>",
            ),
            row=2,
            col=2,
            secondary_y=True,
        )
        fig.update_yaxes(
            title_text="No. of Users",
            range=[
                0,
                df["logged_users"].max() * 1.2 if not df["logged_users"].empty else 10,
            ],
            row=2,
            col=2,
            secondary_y=False,
        )
        fig.update_yaxes(
            title_text="TCP Connections",
            range=[
                0,
                df["tcp_connections"].max() * 1.2
                if not df["tcp_connections"].empty
                else 10,
            ],
            row=2,
            col=2,
            secondary_y=True,
        )
        fig.update_xaxes(title_text="Time", row=2, col=2, tickformat="%H:%M\n%b %d")

        # Apply enhanced layout with professional styling
        fig.update_layout(**ENHANCED_LAYOUT)
        fig.update_layout(
            height=CHART_CONFIG["default_height"],
            title={
                "text": f"<b>Performance Analytics</b><br><sub>{server_name}</sub>",
                "font": {"size": 22, "color": KU_COLORS["text_primary"]},
                "x": 0.5,
                "xanchor": "center",
            },
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.08,
                xanchor="center",
                x=0.5,
                bgcolor="rgba(255, 255, 255, 0.9)",
                bordercolor=KU_COLORS["border"],
                borderwidth=1,
                font={"size": 11},
            ),
            hovermode="x unified",
            margin=dict(l=60, r=60, t=100, b=80),
        )

        # Apply enhanced axis styling to all subplots
        fig.update_xaxes(**ENHANCED_XAXIS)
        fig.update_yaxes(**ENHANCED_YAXIS)

        # Performance Summary
        latest_data = df.iloc[-1] if not df.empty else {}
        avg_cpu = df["cpu_load_5min"].mean() if not df.empty else 0
        max_ram = df["ram_percentage"].max() if not df.empty else 0
        avg_disk = df["disk_percentage"].mean() if not df.empty else 0

        from dash import html

        summary = html.Div(
            [
                html.Div(
                    [
                        html.Div(f"{avg_cpu:.2f}", className="stat-value"),
                        html.Div("Avg CPU Load", className="stat-label"),
                    ],
                    className="overview-stat",
                ),
                html.Div(
                    [
                        html.Div(f"{max_ram:.1f}%", className="stat-value"),
                        html.Div("Peak Memory", className="stat-label"),
                    ],
                    className="overview-stat",
                ),
                html.Div(
                    [
                        html.Div(f"{avg_disk:.1f}%", className="stat-value"),
                        html.Div("Avg Disk Usage", className="stat-label"),
                    ],
                    className="overview-stat",
                ),
            ],
            style={"display": "flex", "gap": "20px", "margin": "20px 0"},
        )

        return fig, summary

    @app.callback(
        Output("download-report", "data"),
        Input("export-button", "n_clicks"),
        prevent_initial_call=True,
    )
    def export_report(n_clicks):
        """Handle export button click and generate downloadable report"""
        if n_clicks:
            try:
                # Generate export data
                export_data = generate_export_report()

                if export_data:
                    # Export to Excel
                    filepath = export_to_excel(export_data)

                    if filepath:
                        logging.info(f"Report exported successfully: {filepath}")
                        return dcc.send_file(filepath)
                    else:
                        logging.error("Failed to create Excel file")
                        return None
                else:
                    logging.error("Failed to generate export data")
                    return None

            except Exception as e:
                logging.error(f"Error in export callback: {e}")
                return None

        return None

    @app.callback(
        Output("server-grid", "children"),
        Input("refresh-button", "n_clicks"),
        Input("interval-component", "n_intervals"),
        prevent_initial_call=False,
    )
    def refresh_server_grid(n_clicks, n_intervals):
        """Refresh server grid when refresh button is clicked or interval triggers"""
        from components import create_compact_server_grid

        return create_compact_server_grid()
