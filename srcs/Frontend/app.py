# Main application file for the Server Monitoring Dashboard
import dash
from dash import dcc, html
import logging

from config import (KU_COLORS, DASHBOARD_CONFIG, FONTS)
from components import (create_system_overview, create_alert_panel, create_enhanced_server_cards,
                       create_enhanced_users_table, create_network_monitor, create_enhanced_historical_graphs)
from callbacks import register_callbacks

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize the Dash app
app = dash.Dash(__name__,
                suppress_callback_exceptions=True,
                meta_tags=DASHBOARD_CONFIG['meta_tags'])

app.title = DASHBOARD_CONFIG['title']

# Enhanced CSS with modern design
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
        <style>
            :root {{
                --ku-primary: {KU_COLORS['primary']};
                --ku-secondary: {KU_COLORS['secondary']};
                --ku-accent: {KU_COLORS['accent']};
                --ku-orange: {KU_COLORS['orange']};
                --ku-red: {KU_COLORS['danger']};
                --ku-light-gray: {KU_COLORS['light_gray']};
                --ku-dark-gray: {KU_COLORS['dark_gray']};
                --ku-light: {KU_COLORS['light']};
                --ku-dark: {KU_COLORS['body_text']};
                --ku-border: {KU_COLORS['border']};
                --ku-success: {KU_COLORS['success']};
                --ku-warning: {KU_COLORS['warning']};
                --ku-danger: {KU_COLORS['danger']};
                --ku-info: {KU_COLORS['info']};
                --ku-muted: {KU_COLORS['muted']};
                --ku-card-shadow: 0 8px 32px rgba(0,87,184,0.1);
                --ku-hover-shadow: 0 12px 40px rgba(0,87,184,0.15);
                --ku-transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            }}
            
            * {{
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }}
            
            body {{
                font-family: {FONTS['primary']};
                background: linear-gradient(135deg, #f8f9fa 0%, #e6ebf0 100%);
                min-height: 100vh;
                color: var(--ku-dark);
                line-height: 1.6;
                font-weight: 400;
            }}
            
            /* Enhanced Header */
            .header {{
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
            }}
            
            .header-left {{
                display: flex;
                align-items: center;
            }}
            
            .header img {{
                height: 60px;
                margin-right: 24px;
                filter: brightness(0) invert(1);
            }}
            
            .header h1 {{
                font-size: 32px;
                font-weight: 600;
                letter-spacing: -0.3px;
                margin: 0;
                font-family: 'DM Sans', sans-serif;
            }}
            
            .header-subtitle {{
                font-size: 14px;
                opacity: 0.9;
                margin-top: 4px;
            }}
            
            .header-right {{
                display: flex;
                align-items: center;
                gap: 20px;
            }}
            
            .system-time, .status-indicator-header {{
                background: rgba(255,255,255,0.1);
                padding: 8px 16px;
                border-radius: 20px;
                font-size: 14px;
                backdrop-filter: blur(10px);
            }}
            
            /* Dashboard Container */
            .dashboard-container {{
                padding: 32px;
                max-width: 1800px;
                margin: 0 auto;
                background: transparent;
            }}
            
            /* Enhanced Cards */
            .card {{
                background: white;
                border-radius: 16px;
                box-shadow: var(--ku-card-shadow);
                padding: 32px;
                margin-bottom: 32px;
                border: 1px solid var(--ku-border);
                transition: var(--ku-transition);
                position: relative;
                overflow: hidden;
            }}
            
            .card::before {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 4px;
                background: linear-gradient(90deg, var(--ku-primary), var(--ku-accent));
            }}
            
            .card:hover {{
                transform: translateY(-4px);
                box-shadow: var(--ku-hover-shadow);
            }}
            
            .card-header {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 24px;
                padding-bottom: 16px;
                border-bottom: 1px solid var(--ku-border);
            }}
            
            .card-title {{
                font-size: 22px;
                font-weight: 600;
                color: var(--ku-dark);
                display: flex;
                align-items: center;
                gap: 12px;
                font-family: 'DM Sans', sans-serif;
            }}
            
            .card-subtitle {{
                font-size: 14px;
                color: var(--ku-muted);
                font-weight: 400;
                line-height: 1.5;
            }}
            
            .card-actions {{
                display: flex;
                gap: 12px;
            }}
            
            /* System Overview Grid */
            .system-overview {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 24px;
                margin-bottom: 32px;
            }}
            
            .overview-stat {{
                background: linear-gradient(135deg, rgba(0,87,184,0.08), rgba(0,87,184,0.12));
                padding: 28px;
                border-radius: 12px;
                text-align: center;
                border: 1px solid rgba(0,87,184,0.15);
                backdrop-filter: blur(10px);
            }}
            
            .stat-value {{
                font-size: 36px;
                font-weight: 700;
                color: var(--ku-primary);
                display: block;
                line-height: 1.2;
                font-family: 'DM Sans', sans-serif;
            }}
            
            .stat-label {{
                font-size: 14px;
                color: var(--ku-muted);
                font-weight: 500;
                margin-top: 8px;
            }}
            
            .stat-change {{
                font-size: 12px;
                margin-top: 4px;
                font-weight: 600;
            }}
            
            .stat-change.positive {{
                color: var(--ku-success);
            }}
            
            .stat-change.negative {{
                color: var(--ku-danger);
            }}
            
            /* Enhanced Server Cards */
            .server-card {{
                background: white;
                border-radius: 20px;
                box-shadow: var(--ku-card-shadow);
                padding: 24px;
                margin: 16px;
                border: 1px solid var(--ku-border);
                transition: var(--ku-transition);
                position: relative;
                overflow: hidden;
            }}
            
            .server-card::before {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 6px;
                background: linear-gradient(90deg, var(--ku-primary), var(--ku-accent));
            }}
            
            .server-header {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 20px;
            }}
            
            .server-name {{
                font-size: 20px;
                font-weight: 600;
                color: var(--ku-dark);
                display: flex;
                align-items: center;
                gap: 12px;
                font-family: 'DM Sans', sans-serif;
            }}
            
            .server-status-badge {{
                padding: 6px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            
            .status-online {{
                background: rgba(0, 87, 184, 0.1);
                color: var(--ku-success);
                border: 1px solid rgba(0, 87, 184, 0.2);
            }}
            
            .status-warning {{
                background: rgba(255, 143, 28, 0.1);
                color: var(--ku-warning);
                border: 1px solid rgba(255, 143, 28, 0.2);
            }}
            
            .status-offline {{
                background: rgba(248, 72, 94, 0.1);
                color: var(--ku-danger);
                border: 1px solid rgba(248, 72, 94, 0.2);
            }}
            
            .server-metrics {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
                gap: 16px;
                margin: 20px 0;
            }}
            
            .metric-item {{
                text-align: center;
                padding: 16px;
                background: var(--ku-light);
                border-radius: 12px;
                border: 1px solid var(--ku-border);
            }}
            
            .metric-value {{
                font-size: 24px;
                font-weight: 600;
                display: block;
                margin-bottom: 4px;
                font-family: 'DM Sans', sans-serif;
            }}
            
            .metric-label {{
                font-size: 12px;
                color: var(--ku-muted);
                font-weight: 500;
            }}
            
            .server-details {{
                background: var(--ku-light);
                padding: 20px;
                border-radius: 12px;
                margin-top: 20px;
            }}
            
            .detail-row {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 8px 0;
                border-bottom: 1px solid var(--ku-border);    
            }}
            
            .detail-row:last-child {{
                border-bottom: none;
            }}
            
            .detail-label {{
                font-weight: 500;
                color: var(--ku-dark);
                font-size: 14px;
            }}
            
            .detail-value {{
                color: var(--ku-muted);
                font-size: 14px;
            }}
            
            /* Alert Panel */
            .alert-panel {{
                background: linear-gradient(135deg, rgba(248, 72, 94, 0.06), rgba(248, 72, 94, 0.12));
                border: 1px solid rgba(248, 72, 94, 0.2);
                border-radius: 12px;
                padding: 24px;
                margin-bottom: 28px;
            }}
            
            .alert-item {{
                display: flex;
                align-items: center;
                padding: 12px;
                background: rgba(255, 255, 255, 0.7);
                border-radius: 8px;
                margin-bottom: 12px;
                border-left: 4px solid var(--ku-primary);
            }}
            
            .alert-icon {{
                margin-right: 12px;
                color: var(--ku-danger);
                font-size: 18px;
            }}
            
            .alert-content {{
                flex: 1;
            }}
            
            .alert-title {{
                font-weight: 500;
                color: var(--ku-dark);
                margin-bottom: 4px;
                font-family: 'DM Sans', sans-serif;
            }}
            
            .alert-description {{
                font-size: 14px;
                color: var(--ku-muted);
            }}
            
            .alert-time {{
                font-size: 12px;
                color: var(--ku-muted);
            }}
            
            /* Performance Indicators */
            .performance-indicator {{
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
            }}
            
            .perf-excellent {{
                background: rgba(39, 174, 96, 0.1);
                color: var(--ku-success);
                border: 1px solid rgba(39, 174, 96, 0.2);
            }}
            
            .perf-good {{
                background: rgba(46, 204, 113, 0.1);
                color: #2ECC71;
                border: 1px solid rgba(46, 204, 113, 0.2);
            }}
            
            .perf-fair {{
                background: rgba(243, 156, 18, 0.1);
                color: var(--ku-warning);
                border: 1px solid rgba(243, 156, 18, 0.2);
            }}
            
            .perf-poor {{
                background: rgba(231, 76, 60, 0.1);
                color: var(--ku-danger);
                border: 1px solid rgba(231, 76, 60, 0.2);
            }}
            
            /* Enhanced Tables */
            .enhanced-table {{
                background: white;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 4px 16px rgba(0,87,184,0.1);
            }}
            
            .table-header {{
                background: linear-gradient(135deg, var(--ku-primary), #003A7A);
                color: white;
                padding: 16px 20px;
                font-weight: 600;
            }}
            
            /* Network Activity */
            .network-activity {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 16px;
                margin: 20px 0;
            }}
            
            .network-stat {{
                background: linear-gradient(135deg, rgba(0, 169, 206, 0.08), rgba(0, 169, 206, 0.12));
                padding: 24px;
                border-radius: 12px;
                text-align: center;
                border: 1px solid rgba(0, 169, 206, 0.2);
                backdrop-filter: blur(5px);
            }}
            
            /* Resource Usage Bars */
            .resource-bar {{
                background: var(--ku-light);
                height: 8px;
                border-radius: 4px;
                overflow: hidden;
                margin: 8px 0;
            }}
            
            .resource-fill {{
                height: 100%;
                border-radius: 4px;
                transition: width 0.3s ease;
            }}
            
            .resource-cpu {{
                background: linear-gradient(90deg, var(--ku-info), #0088CC);
            }}
            
            .resource-memory {{
                background: linear-gradient(90deg, var(--ku-warning), #E6740A);
            }}
            
            .resource-disk {{
                background: linear-gradient(90deg, var(--ku-success), #003A7A);
            }}
            
            /* Responsive Design */
            @media (max-width: 768px) {{
                .dashboard-container {{
                    padding: 16px;
                }}
                
                .server-metrics {{
                    grid-template-columns: repeat(2, 1fr);
                }}
                
                .system-overview {{
                    grid-template-columns: 1fr;
                }}
                
                .header {{
                    padding: 16px 20px;
                }}
                
                .header h1 {{
                    font-size: 24px;
                }}
            }}
            
            /* Custom Scrollbar */
            ::-webkit-scrollbar {{
                width: 8px;
            }}
            
            ::-webkit-scrollbar-track {{
                background: var(--ku-light);
            }}
            
            ::-webkit-scrollbar-thumb {{
                background: var(--ku-muted);
                border-radius: 4px;
            }}
            
            ::-webkit-scrollbar-thumb:hover {{
                background: var(--ku-primary);
            }}
            
            /* Loading Animation */
            .loading-spinner {{
                display: inline-block;
                width: 20px;
                height: 20px;
                border: 3px solid var(--ku-light);
                border-radius: 50%;
                border-top-color: var(--ku-primary);
                animation: spin 1s ease-in-out infinite;
            }}
            
            @keyframes spin {{
                to {{ transform: rotate(360deg); }}
            }}
            
            /* Tab Enhancements */
            .tab-selected {{
                background: linear-gradient(135deg, var(--ku-primary) 0%, #003A7A 100%) !important;
                color: white !important;
                border-radius: 12px 12px 0 0 !important;
                font-weight: 600;
            }}
            
            /* Button Enhancements */
            .btn {{
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
            }}
            
            .btn:hover {{
                transform: translateY(-2px);
                box-shadow: 0 8px 24px rgba(0,87,184,0.3);
                background: linear-gradient(135deg, #003A7A 0%, var(--ku-primary) 100%);
            }}
            
            .btn:active {{
                transform: translateY(0);
            }}
            
            .btn-secondary {{
                background: linear-gradient(135deg, var(--ku-muted) 0%, #5A6C7D 100%);
            }}
            
            .btn-danger {{
                background: linear-gradient(135deg, var(--ku-danger) 0%, #C0392B 100%);
            }}
        </style>
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
                <div class="status-indicator-header">
                    <i class="fas fa-server"></i> <span id="server-count">0 Servers</span>
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
            // Update time every second
            function updateTime() {{
                const now = new Date();
                document.getElementById('current-time').textContent = now.toLocaleString();
            }}
            setInterval(updateTime, 1000);
            updateTime();
        </script>
    </body>
</html>
'''

# Define the main layout
app.layout = html.Div([
    # Auto-refresh component
    dcc.Interval(
        id='interval-component',
        interval=DASHBOARD_CONFIG['refresh_interval'],  # Refresh every 30 seconds
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

# Register callbacks
register_callbacks(app)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3000)