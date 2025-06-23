# app.py
import dash
from dash import dcc, html, Input, Output, callback, dash_table
import plotly.express as px
import plotly.graph_objs as go
from dash.dependencies import Input, Output
import pandas as pd
import psycopg2
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define Khalifa University colors
KU_COLORS = {
    'primary': '#007F3E',  # KU green
    'secondary': '#8C1D40',  # KU burgundy
    'accent': '#FFBF3C',  # KU gold
    'light': '#F0F0F0',  # Light gray
    'dark': '#2C2A29',  # Dark gray
    'white': '#FFFFFF',
    'success': '#007F3E',
    'warning': '#FFC107',
    'danger': '#DC3545',
}

# Database configuration
DB_CONFIG = {
    'host': 'postgres',
    'user': 'postgres',
    'password': os.getenv("POSTGRES_PASSWORD"),
    'database': 'server_db'
}

# Initialize the Dash app
app = dash.Dash(__name__, 
                suppress_callback_exceptions=True,
                meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1.0'}])

# Set the title of the app
app.title = "Khalifa University - Server Monitoring Dashboard"

# Define custom CSS for the dashboard
external_stylesheets = [
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css'
]

# Custom CSS for Khalifa University branding
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            /* Khalifa University Brand Colors and Styles */
            :root {
                --ku-green: #007F3E;
                --ku-burgundy: #8C1D40;
                --ku-gold: #FFBF3C;
                --ku-gray: #F0F0F0;
                --ku-dark: #2C2A29;
            }
            body {
                font-family: 'Roboto', sans-serif;
                margin: 0;
                background-color: var(--ku-gray);
            }
            .header {
                background-color: var(--ku-green);
                padding: 20px;
                color: white;
                display: flex;
                align-items: center;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            .header img {
                height: 60px;
                margin-right: 20px;
            }
            .header h1 {
                margin: 0;
                font-size: 24px;
                font-weight: 500;
            }
            .dashboard-container {
                padding: 20px;
                max-width: 1400px;
                margin: 0 auto;
            }
            .card {
                background-color: white;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                padding: 20px;
                margin-bottom: 20px;
            }
            .card-header {
                border-bottom: 1px solid #eee;
                padding-bottom: 10px;
                margin-bottom: 15px;
                font-weight: 500;
                color: var(--ku-dark);
                font-size: 18px;
            }
            .server-status {
                display: flex;
                align-items: center;
                margin-bottom: 10px;
            }
            .status-indicator {
                width: 12px;
                height: 12px;
                border-radius: 50%;
                margin-right: 10px;
            }
            .status-online {
                background-color: var(--ku-green);
            }
            .status-warning {
                background-color: var(--ku-gold);
            }
            .status-offline {
                background-color: var(--ku-burgundy);
            }
            .tab-selected {
                background-color: var(--ku-green) !important;
                color: white !important;
            }
            .control-panel {
                padding: 10px;
                background-color: white;
                border-radius: 8px;
                margin-bottom: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .Select-control {
                border-color: var(--ku-green) !important;
            }
            .Select-control:hover {
                border-color: var(--ku-gold) !important;
            }
            .btn {
                background-color: var(--ku-green);
                color: white;
                border: none;
                padding: 10px 15px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
            }
            .btn:hover {
                background-color: #006633;
            }
            .footer {
                text-align: center;
                padding: 20px;
                color: var(--ku-dark);
                font-size: 12px;
                border-top: 1px solid #ddd;
                margin-top: 20px;
            }
            .DataTable {
                border-collapse: collapse;
                width: 100%;
            }
            .DataTable td, .DataTable th {
                border: 1px solid #ddd;
                padding: 8px;
            }
            .DataTable th {
                background-color: var(--ku-green);
                color: white;
            }
            /* Resource usage styles */
            .usage-gauge {
                margin: 10px 0;
            }
            .gauge-label {
                font-size: 14px;
                font-weight: 500;
                margin-bottom: 5px;
            }
            /* Critical value highlighting */
            .critical-value {
                color: var(--ku-burgundy);
                font-weight: bold;
            }
            .warning-value {
                color: var(--ku-gold);
                font-weight: bold;
            }
            .good-value {
                color: var(--ku-green);
            }
        </style>
    </head>
    <body>
        <div class="header">
            <img src="https://www.ku.ac.ae/wp-content/themes/khalifa-university/img/logo.svg" alt="Khalifa University Logo">
            <h1>Server Monitoring Dashboard</h1>
        </div>
        <div class="dashboard-container">
            {%app_entry%}
        </div>
        <footer class="footer">
            <p>© Khalifa University - Server Monitoring Dashboard. All rights reserved.</p>
        </footer>
        {%config%}
        {%scripts%}
        {%renderer%}
    </body>
</html>
'''

# Function to fetch the latest server metrics from the database
def get_latest_server_metrics():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Get the most recent record for each server
        query = """
        WITH latest_records AS (
            SELECT server_name, MAX(timestamp) as max_timestamp
            FROM server_metrics
            GROUP BY server_name
        )
        SELECT sm.*
        FROM server_metrics sm
        JOIN latest_records lr ON sm.server_name = lr.server_name AND sm.timestamp = lr.max_timestamp
        ORDER BY sm.server_name
        """
        
        cursor.execute(query)
        columns = [desc[0] for desc in cursor.description]
        metrics = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        return metrics
    except Exception as e:
        print(f"Database error: {e}")
        return []
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# Function to fetch top users data from the database
def get_top_users():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        query = """
        SELECT server_name, username, cpu, mem, disk
        FROM top_users
        ORDER BY server_name, cpu DESC
        """
        
        cursor.execute(query)
        columns = [desc[0] for desc in cursor.description]
        users = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        return users
    except Exception as e:
        print(f"Database error: {e}")
        return []
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# Function to fetch historical metrics for a specific server
def get_historical_metrics(server_name, hours=24):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Get data from the last X hours
        query = """
        SELECT timestamp, ram_percentage, disk_percentage, cpu_load_1min, tcp_connections, logged_users
        FROM server_metrics
        WHERE server_name = %s AND timestamp > NOW() - INTERVAL %s HOUR
        ORDER BY timestamp
        """
        
        cursor.execute(query, (server_name, hours))
        columns = [desc[0] for desc in cursor.description]
        metrics = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        return metrics
    except Exception as e:
        print(f"Database error: {e}")
        return []
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# Function to determine server status based on metrics
def determine_server_status(metrics):
    if not metrics:
        return "offline"
    
    ram_percentage = metrics.get('ram_percentage', 0)
    disk_percentage = metrics.get('disk_percentage', 0)
    cpu_load = float(metrics.get('cpu_load_5min', 0))
    
    if ram_percentage > 90 or disk_percentage > 90 or cpu_load > 5:
        return "warning"
    
    # Check if the timestamp is recent (within the last 15 minutes)
    timestamp = metrics.get('timestamp')
    if timestamp:
        if isinstance(timestamp, str):
            timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S.%f')
        if datetime.now() - timestamp > timedelta(minutes=15):
            return "offline"
    
    return "online"

# Create server status indicators
def create_server_status_cards():
    metrics = get_latest_server_metrics()
    server_cards = []
    
    if not metrics:
        return html.Div("No server data available", style={'text-align': 'center', 'margin': '20px'})
    
    for metric in metrics:
        server_name = metric.get('server_name', 'Unknown')
        status = determine_server_status(metric)
        
        status_color = {
            'online': KU_COLORS['success'],
            'warning': KU_COLORS['warning'],
            'offline': KU_COLORS['danger']
        }.get(status, KU_COLORS['warning'])
        
        # Format metrics for display
        ram_usage = f"{metric.get('ram_percentage', 0)}%"
        disk_usage = f"{metric.get('disk_percentage', 0)}%"
        cpu_load = f"{metric.get('cpu_load_1min', 0)} / {metric.get('cpu_load_5min', 0)} / {metric.get('cpu_load_15min', 0)}"
        
        # Create a card for each server
        card = html.Div([
            html.Div([
                html.Div(className='status-indicator', style={'background-color': status_color}),
                html.H3(server_name, style={'margin': '0', 'font-size': '18px'})
            ], className='server-status'),
            
            html.Div([
                html.Div([
                    html.Div("RAM Usage", className='gauge-label'),
                    dcc.Graph(
                        figure=create_gauge(float(metric.get('ram_percentage', 0)), "RAM"),
                        config={'displayModeBar': False},
                        style={'height': '120px'}
                    )
                ], className='usage-gauge', style={'width': '33%', 'display': 'inline-block'}),
                
                html.Div([
                    html.Div("Disk Usage", className='gauge-label'),
                    dcc.Graph(
                        figure=create_gauge(float(metric.get('disk_percentage', 0)), "Disk"),
                        config={'displayModeBar': False},
                        style={'height': '120px'}
                    )
                ], className='usage-gauge', style={'width': '33%', 'display': 'inline-block'}),
                
                html.Div([
                    html.Div("CPU Load (1/5/15 min)", className='gauge-label'),
                    dcc.Graph(
                        figure=create_gauge(float(metric.get('cpu_load_5min', 0)), "CPU", max_value=10),
                        config={'displayModeBar': False},
                        style={'height': '120px'}
                    )
                ], className='usage-gauge', style={'width': '33%', 'display': 'inline-block'})
            ], style={'display': 'flex', 'justify-content': 'space-between'}),
            
            html.Div([
                html.Div([
                    html.Strong("System: "),
                    html.Span(f"{metric.get('operating_system', 'Unknown')} ({metric.get('architecture', 'Unknown')})")
                ], style={'margin-bottom': '5px'}),
                
                html.Div([
                    html.Strong("CPUs: "),
                    html.Span(f"Physical: {metric.get('physical_cpus', 0)}, Virtual: {metric.get('virtual_cpus', 0)}")
                ], style={'margin-bottom': '5px'}),
                
                html.Div([
                    html.Strong("Last Boot: "),
                    html.Span(metric.get('last_boot', 'Unknown'))
                ], style={'margin-bottom': '5px'}),
                
                html.Div([
                    html.Strong("Users: "),
                    html.Span(f"Logged in: {metric.get('logged_users', 0)}, SSH: {metric.get('active_ssh_users', 0)}, VNC: {metric.get('active_vnc_users', 0)}")
                ], style={'margin-bottom': '5px'}),
                
                html.Div([
                    html.Strong("TCP Connections: "),
                    html.Span(metric.get('tcp_connections', 0))
                ])
            ], style={'margin-top': '15px', 'font-size': '14px'})
        ], className='card', id=f"server-card-{server_name}")
        
        server_cards.append(card)
    
    # Organize cards in rows (3 cards per row)
    rows = []
    for i in range(0, len(server_cards), 3):
        row = html.Div(
            server_cards[i:i+3],
            style={'display': 'flex', 'flex-wrap': 'wrap', 'justify-content': 'space-between'}
        )
        rows.append(row)
    
    return html.Div(rows)

# Create gauge chart for resource usage
def create_gauge(value, metric_type, max_value=100):
    if metric_type == "CPU":
        # For CPU load, different thresholds
        colors = ['#007F3E', '#FFBF3C', '#8C1D40']
        threshold_values = [3, 6, max_value]
    else:
        # For RAM and Disk, standard thresholds
        colors = ['#007F3E', '#FFBF3C', '#8C1D40']
        threshold_values = [70, 85, max_value]
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        gauge={
            'axis': {'range': [None, max_value], 'tickwidth': 1},
            'bar': {'color': "#FFFFFF"},
            'steps': [
                {'range': [0, threshold_values[0]], 'color': colors[0]},
                {'range': [threshold_values[0], threshold_values[1]], 'color': colors[1]},
                {'range': [threshold_values[1], threshold_values[2]], 'color': colors[2]}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': value
            }
        }
    ))
    
    fig.update_layout(
        margin=dict(l=20, r=20, t=30, b=20),
        height=120,
        paper_bgcolor="white",
        font={'size': 12}
    )
    
    return fig

# Create users activity table
def create_users_table():
    users_data = get_top_users()
    
    if not users_data:
        return html.Div("No user data available", style={'text-align': 'center', 'margin': '20px'})
    
    # Group users by server
    servers = {}
    for user in users_data:
        server_name = user['server_name']
        if server_name not in servers:
            servers[server_name] = []
        servers[server_name].append(user)
    
    # Create a tab for each server
    tabs = []
    for server_name, users in servers.items():
        # Convert to DataFrame for easier table creation
        df = pd.DataFrame(users)
        
        # Create a table for this server's users
        table = dash_table.DataTable(
            id=f'table-{server_name}',
            columns=[
                {'name': 'Username', 'id': 'username'},
                {'name': 'CPU Usage (%)', 'id': 'cpu'},
                {'name': 'Memory Usage (%)', 'id': 'mem'},
                {'name': 'Disk Usage (GB)', 'id': 'disk'}
            ],
            data=df.to_dict('records'),
            style_table={'overflowX': 'auto'},
            style_cell={
                'textAlign': 'left',
                'padding': '10px',
                'font-family': 'Roboto, sans-serif'
            },
            style_header={
                'backgroundColor': KU_COLORS['primary'],
                'color': 'white',
                'fontWeight': 'bold',
                'fontSize': '14px'
            },
            style_data_conditional=[
                {
                    'if': {'column_id': 'cpu', 'filter_query': '{cpu} > 50'},
                    'color': KU_COLORS['danger'],
                    'fontWeight': 'bold'
                },
                {
                    'if': {'column_id': 'mem', 'filter_query': '{mem} > 50'},
                    'color': KU_COLORS['danger'],
                    'fontWeight': 'bold'
                },
                {
                    'if': {'column_id': 'disk', 'filter_query': '{disk} > 5'},
                    'color': KU_COLORS['danger'],
                    'fontWeight': 'bold'
                }
            ],
            sort_action='native',
            filter_action='native',
            page_size=10
        )
        
        tab = dcc.Tab(
            label=server_name,
            value=server_name,
            children=[table],
            style={'padding': '15px', 'fontSize': '14px'},
            selected_style={
                'backgroundColor': KU_COLORS['primary'],
                'color': 'white',
                'padding': '15px',
                'fontSize': '14px',
                'borderTop': f'3px solid {KU_COLORS["accent"]}'
            }
        )
        
        tabs.append(tab)
    
    return dcc.Tabs(id='user-tabs', value=list(servers.keys())[0] if servers else '', children=tabs)

# Create historical metrics graphs
def create_historical_graphs(server_name=""):
    if not server_name:
        metrics = get_latest_server_metrics()
        if metrics:
            server_name = metrics[0]['server_name']
        else:
            return html.Div("No server data available for historical metrics", style={'text-align': 'center'})
    
    historical_data = get_historical_metrics(server_name)
    
    if not historical_data:
        return html.Div(f"No historical data available for {server_name}", style={'text-align': 'center'})
    
    # Convert to DataFrame for easier plotting
    df = pd.DataFrame(historical_data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Create CPU Load graph
    cpu_fig = px.line(
        df, 
        x='timestamp', 
        y='cpu_load_1min',
        title=f"CPU Load (1min) - {server_name}",
        labels={'timestamp': 'Time', 'cpu_load_1min': 'Load Average'},
        line_shape='spline'
    )
    cpu_fig.update_layout(
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor="white",
        plot_bgcolor="#f8f9fa",
        font={'size': 12},
        hovermode="x unified"
    )
    cpu_fig.update_traces(line=dict(color=KU_COLORS['primary'], width=2))
    
    # Create Memory Usage graph
    mem_fig = px.line(
        df, 
        x='timestamp', 
        y='ram_percentage',
        title=f"RAM Usage - {server_name}",
        labels={'timestamp': 'Time', 'ram_percentage': 'RAM Usage (%)'},
        line_shape='spline'
    )
    mem_fig.update_layout(
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor="white",
        plot_bgcolor="#f8f9fa",
        font={'size': 12},
        hovermode="x unified"
    )
    mem_fig.update_traces(line=dict(color=KU_COLORS['secondary'], width=2))
    
    # Create Disk Usage graph
    disk_fig = px.line(
        df, 
        x='timestamp', 
        y='disk_percentage',
        title=f"Disk Usage - {server_name}",
        labels={'timestamp': 'Time', 'disk_percentage': 'Disk Usage (%)'},
        line_shape='spline'
    )
    disk_fig.update_layout(
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor="white",
        plot_bgcolor="#f8f9fa",
        font={'size': 12},
        hovermode="x unified"
    )
    disk_fig.update_traces(line=dict(color=KU_COLORS['accent'], width=2))
    
    # Create Users and Connections graph
    users_fig = go.Figure()
    users_fig.add_trace(go.Scatter(
        x=df['timestamp'], 
        y=df['logged_users'],
        mode='lines+markers',
        name='Logged Users',
        line=dict(color=KU_COLORS['primary'], width=2)
    ))
    users_fig.add_trace(go.Scatter(
        x=df['timestamp'], 
        y=df['tcp_connections'],
        mode='lines+markers',
        name='TCP Connections',
        line=dict(color=KU_COLORS['secondary'], width=2),
        yaxis='y2'
    ))
    users_fig.update_layout(
        title=f"Users and Connections - {server_name}",
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor="white",
        plot_bgcolor="#f8f9fa",
        font={'size': 12},
        hovermode="x unified",
        yaxis=dict(title='Logged Users'),
        yaxis2=dict(title='TCP Connections', overlaying='y', side='right'),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return html.Div([
        # Server selector dropdown
        html.Div([
            html.Label("Select Server:", style={'margin-right': '10px', 'font-weight': '500'}),
            dcc.Dropdown(
                id='server-selector',
                options=[{'label': m['server_name'], 'value': m['server_name']} for m in get_latest_server_metrics()],
                value=server_name,
                style={'width': '300px'}
            ),
            html.Label("Time Range:", style={'margin-right': '10px', 'margin-left': '20px', 'font-weight': '500'}),
            dcc.Dropdown(
                id='time-range-selector',
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
        
        # Graphs in a 2x2 grid
        html.Div([
            html.Div([
                dcc.Graph(id='cpu-graph', figure=cpu_fig)
            ], className='card', style={'width': '49%', 'display': 'inline-block'}),
            
            html.Div([
                dcc.Graph(id='memory-graph', figure=mem_fig)
            ], className='card', style={'width': '49%', 'display': 'inline-block', 'float': 'right'}),
            
            html.Div([
                dcc.Graph(id='disk-graph', figure=disk_fig)
            ], className='card', style={'width': '49%', 'display': 'inline-block'}),
            
            html.Div([
                dcc.Graph(id='users-graph', figure=users_fig)
            ], className='card', style={'width': '49%', 'display': 'inline-block', 'float': 'right'}),
        ])
    ])

# Define the main layout
app.layout = html.Div([
    # Auto-refresh component
    dcc.Interval(
        id='interval-component',
        interval=60*1000,  # in milliseconds (1 minute)
        n_intervals=0
    ),
    
    # Dashboard tabs
    dcc.Tabs([
        dcc.Tab(
            label='Servers Overview', 
            children=[
                html.Div(id='server-status-cards', children=create_server_status_cards()),
            ],
            style={'padding': '15px'},
            selected_style={'padding': '15px', 'backgroundColor': KU_COLORS['primary'], 'color': 'white'}
        ),
        dcc.Tab(
            label='User Activity',
            children=[
                html.Div(id='users-table', children=create_users_table()),
            ],
            style={'padding': '15px'},
            selected_style={'padding': '15px', 'backgroundColor': KU_COLORS['primary'], 'color': 'white'}
        ),
        dcc.Tab(
            label='Historical Metrics',
            children=[
                html.Div(id='historical-graphs', children=create_historical_graphs()),
            ],
            style={'padding': '15px'},
            selected_style={'padding': '15px', 'backgroundColor': KU_COLORS['primary'], 'color': 'white'}
        ),
    ]),
    
    # Refresh button and last updated info
    html.Div([
        html.Button('Refresh Data', id='refresh-button', className='btn'),
        html.Div(id='last-updated', style={'display': 'inline-block', 'margin-left': '20px', 'font-size': '14px'})
    ], style={'margin-top': '20px', 'text-align': 'right'})
])

# Callback to update server status cards
@app.callback(
    Output('server-status-cards', 'children'),
    [Input('interval-component', 'n_intervals'),
     Input('refresh-button', 'n_clicks')]
)
def update_server_cards(n_intervals, n_clicks):
    return create_server_status_cards()

# Callback to update users table
@app.callback(
    Output('users-table', 'children'),
    [Input('interval-component', 'n_intervals'),
     Input('refresh-button', 'n_clicks')]
)
def update_users_table(n_intervals, n_clicks):
    return create_users_table()

# Callback to update historical graphs based on server selection
@app.callback(
    Output('historical-graphs', 'children'),
    [Input('server-selector', 'value'),
     Input('time-range-selector', 'value'),
     Input('interval-component', 'n_intervals'),
     Input('refresh-button', 'n_clicks')]
)
def update_historical_graphs(server_name, time_range, n_intervals, n_clicks):
    if not server_name:
        metrics = get_latest_server_metrics()
        if metrics:
            server_name = metrics[0]['server_name']
    
    historical_data = get_historical_metrics(server_name, time_range)
    
    if not historical_data:
        return html.Div(f"No historical data available for {server_name}", style={'text-align': 'center'})
    
    # Convert to DataFrame for easier plotting
    df = pd.DataFrame(historical_data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Create CPU Load graph
    cpu_fig = px.line(
        df, 
        x='timestamp', 
        y='cpu_load_1min',
        title=f"CPU Load (1min) - {server_name}",
        labels={'timestamp': 'Time', 'cpu_load_1min': 'Load Average'},
        line_shape='spline'
    )
    cpu_fig.update_layout(
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor="white",
        plot_bgcolor="#f8f9fa",
        font={'size': 12},
        hovermode="x unified"
    )
    cpu_fig.update_traces(line=dict(color=KU_COLORS['primary'], width=2))
    
    # Create Memory Usage graph
    mem_fig = px.line(
        df, 
        x='timestamp', 
        y='ram_percentage',
        title=f"RAM Usage - {server_name}",
        labels={'timestamp': 'Time', 'ram_percentage': 'RAM Usage (%)'},
        line_shape='spline'
    )
    mem_fig.update_layout(
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor="white",
        plot_bgcolor="#f8f9fa",
        font={'size': 12},
        hovermode="x unified"
    )
    mem_fig.update_traces(line=dict(color=KU_COLORS['secondary'], width=2))
    
    # Create Disk Usage graph
    disk_fig = px.line(
        df, 
        x='timestamp', 
        y='disk_percentage',
        title=f"Disk Usage - {server_name}",
        labels={'timestamp': 'Time', 'disk_percentage': 'Disk Usage (%)'},
        line_shape='spline'
    )
    disk_fig.update_layout(
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor="white",
        plot_bgcolor="#f8f9fa",
        font={'size': 12},
        hovermode="x unified"
    )
    disk_fig.update_traces(line=dict(color=KU_COLORS['accent'], width=2))
    
    # Create Users and Connections graph
    users_fig = go.Figure()
    users_fig.add_trace(go.Scatter(
        x=df['timestamp'], 
        y=df['logged_users'],
        mode='lines+markers',
        name='Logged Users',
        line=dict(color=KU_COLORS['primary'], width=2)
    ))
    users_fig.add_trace(go.Scatter(
        x=df['timestamp'], 
        y=df['tcp_connections'],
        mode='lines+markers',
        name='TCP Connections',
        line=dict(color=KU_COLORS['secondary'], width=2),
        yaxis='y2'
    ))
    users_fig.update_layout(
        title=f"Users and Connections - {server_name}",
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor="white",
        plot_bgcolor="#f8f9fa",
        font={'size': 12},
        hovermode="x unified",
        yaxis=dict(title='Logged Users'),
        yaxis2=dict(title='TCP Connections', overlaying='y', side='right'),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    # Create server selector dropdown component
    server_selector = html.Div([
        html.Label("Select Server:", style={'margin-right': '10px', 'font-weight': '500'}),
        dcc.Dropdown(
            id='server-selector',
            options=[{'label': m['server_name'], 'value': m['server_name']} for m in get_latest_server_metrics()],
            value=server_name,
            style={'width': '300px'}
        ),
        html.Label("Time Range:", style={'margin-right': '10px', 'margin-left': '20px', 'font-weight': '500'}),
        dcc.Dropdown(
            id='time-range-selector',
            options=[
                {'label': 'Last 6 Hours', 'value': 6},
                {'label': 'Last 12 Hours', 'value': 12},
                {'label': 'Last 24 Hours', 'value': 24},
                {'label': 'Last 3 Days', 'value': 72},
                {'label': 'Last Week', 'value': 168}
            ],
            value=time_range,
            style={'width': '200px'}
        )
    ], style={'display': 'flex', 'align-items': 'center', 'margin-bottom': '20px'})
    
    # Return complete layout for historical metrics tab
    return html.Div([
        server_selector,
        
        # Graphs in a 2x2 grid
        html.Div([
            html.Div([
                dcc.Graph(id='cpu-graph', figure=cpu_fig)
            ], className='card', style={'width': '49%', 'display': 'inline-block'}),
            
            html.Div([
                dcc.Graph(id='memory-graph', figure=mem_fig)
            ], className='card', style={'width': '49%', 'display': 'inline-block', 'float': 'right'}),
            
            html.Div([
                dcc.Graph(id='disk-graph', figure=disk_fig)
            ], className='card', style={'width': '49%', 'display': 'inline-block'}),
            
            html.Div([
                dcc.Graph(id='users-graph', figure=users_fig)
            ], className='card', style={'width': '49%', 'display': 'inline-block', 'float': 'right'}),
        ])
    ])

# Callback to update last updated time
@app.callback(
    Output('last-updated', 'children'),
    [Input('interval-component', 'n_intervals'),
     Input('refresh-button', 'n_clicks')]
)
def update_last_updated(n_intervals, n_clicks):
    now = datetime.now()
    return f"Last updated: {now.strftime('%Y-%m-%d %H:%M:%S')}"

# Main entry point
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3000)