# Enhanced Server Monitoring Dashboard - Modular Version with External CSS
import dash
from dash import dcc, html
import logging
from datetime import datetime
import os

# Import from local modules
from config import KU_COLORS, DASHBOARD_CONFIG, FONTS
from components import (create_system_overview, create_alert_panel, create_enhanced_server_cards,
                       create_enhanced_users_table, create_network_monitor, create_enhanced_historical_graphs,
                       create_compact_server_grid,)
from callbacks_enhanced import register_callbacks
from export_utils import generate_export_report, export_to_excel
from refresh_utils import trigger_dashboard_refresh
from toast_utils import create_toast_container

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize the Dash app with external assets
app = dash.Dash(__name__,
                suppress_callback_exceptions=True,
                meta_tags=DASHBOARD_CONFIG['meta_tags'],
                assets_folder='assets')

app.title = DASHBOARD_CONFIG['title']

# Minimal index string (CSS is now external in assets/styles.css)
app.index_string = f'''
<!DOCTYPE html>
<html>
    <head>
        {{%metas%}}
        <title>{{%title%}}</title>
        {{%favicon%}}
        {{%css%}}
        <link href="{FONTS['google_fonts'][0]}" rel="stylesheet">
        <link href="{FONTS['google_fonts'][1]}" rel="stylesheet">
        <link rel="stylesheet" href="{FONTS['fontawesome']}">
    </head>
    <body>
        <div class="header">
            <div class="header-left">
                <img src="{DASHBOARD_CONFIG['logo_url']}" alt="{DASHBOARD_CONFIG['logo_alt']}">
                <div>
                    <h1>{DASHBOARD_CONFIG['header_title']}</h1>
                </div>
            </div>
            <div class="header-right">
                <div class="system-time" id="system-time">
                    <i class="fas fa-clock"></i> <span id="current-time"></span>
                </div>
            </div>
        </div>
        <div class="dashboard-container">
            {{%app_entry%}}
        </div>
        {{%config%}}
        {{%scripts%}}
        {{%renderer%}}
        <script>
            function updateTime() {{
                const now = new Date();
                const element = document.getElementById('current-time');
                if (element) {{
                    element.textContent = now.toLocaleString();
                }}
            }}
            setInterval(updateTime, 1000);
            updateTime();
        </script>
    </body>
</html>
'''

# Define the main layout using modular components
app.layout = html.Div([
    # Toast notification container
    html.Div(id='toast-container', className='toast-container'),

    # Auto-refresh component
    dcc.Interval(
        id='interval-component',
        interval=DASHBOARD_CONFIG['refresh_interval'],
        n_intervals=0
    ),

    # Download component for exporting reports
    dcc.Download(id='download-report'),

    # System Overview Section


    # Main Dashboard Tabs
    dcc.Tabs([
        dcc.Tab(
            label='Usage Overview',
            children=[
                html.Div(id='server-grid', children=create_compact_server_grid()),
            ],
            style={'padding': '20px',
                   'fontSize': '16px', 'fontWeight': '600'},
            selected_style={'padding': '20px', 'fontSize': '16px', 'fontWeight': '600',
                            'backgroundColor': KU_COLORS['primary'], 'color': 'white'}
        ),
        dcc.Tab(
            label='Server Details',
            children=[
				html.Div([
					html.Div([
						html.Div([
							html.I(className="fas fa-tachometer-alt",
								style={'marginRight': '12px', 'fontSize': '20px'}),
							"System Overview"
						], className="card-title"),
					], className="card-header"),
					html.Div(id='system-overview', children=create_system_overview())
				], className="card"),
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
                    html.Div(id='enhanced-users-table'
                             , children=create_enhanced_users_table())
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
                    html.Div(id='enhanced-historical-graphs'
                             , children=create_enhanced_historical_graphs()
                            )
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
                    html.Div(id='network-monitor'
                             , children=create_network_monitor()
                            )
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

# Register callbacks
register_callbacks(app)

if __name__ == '__main__':
    logger.info("Starting Khalifa University Server Monitoring Dashboard...")
    logger.info(f"Debug mode: {os.getenv('DEBUG') == 'True'}")
    app.run(debug=(os.getenv("DEBUG") == "True"), host='0.0.0.0', port=3000)
