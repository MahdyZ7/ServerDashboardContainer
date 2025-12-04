# Enhanced Server Monitoring Dashboard - Modular Version with External CSS
import dash
from dash import dcc, html
import logging
import os

# Import from local modules
from config import KU_COLORS, DASHBOARD_CONFIG, FONTS
from components import (
    create_system_overview,
    create_enhanced_server_cards,
    create_enhanced_users_table,
    create_network_monitor,
    create_enhanced_historical_graphs,
    create_compact_server_grid,
)
from callbacks_enhanced import register_callbacks

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize the Dash app with external assets
app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    meta_tags=DASHBOARD_CONFIG["meta_tags"],
    assets_folder="assets",
)

app.title = DASHBOARD_CONFIG["title"]

# Minimal index string (CSS is now external in assets/styles.css)
app.index_string = f'''
<!DOCTYPE html>
<html data-theme="light">
    <head>
        {{%metas%}}
        <title>{{%title%}}</title>
        {{%favicon%}}
        {{%css%}}
        <link href="{FONTS["google_fonts"][0]}" rel="stylesheet">
        <link rel="stylesheet" href="{FONTS["fontawesome"]}">
        <link rel="stylesheet" href="./assets/animations.css">
        <link rel="stylesheet" href="./assets/dark-mode.css">
    </head>
    <body>
        <div class="header">
            <div class="header-left">
                <img src="{DASHBOARD_CONFIG["logo_url"]}" alt="{DASHBOARD_CONFIG["logo_alt"]}">
                <div>
                    <h1>{DASHBOARD_CONFIG["header_title"]}</h1>
                </div>
            </div>
            <div class="header-right">
                <button class="theme-toggle-btn" id="theme-toggle" aria-label="Toggle dark mode" title="Toggle dark mode (Ctrl+D)">
                    <i class="fas fa-sun"></i>
                    <i class="fas fa-moon"></i>
                </button>
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
            // Time update function
            function updateTime() {{
                const now = new Date();
                const element = document.getElementById('current-time');
                if (element) {{
                    element.textContent = now.toLocaleString();
                }}
            }}
            setInterval(updateTime, 1000);
            updateTime();

            // Dark mode toggle functionality
            (function() {{
                const themeToggle = document.getElementById('theme-toggle');
                const html = document.documentElement;

                // Check for saved theme preference or default to light mode
                const currentTheme = localStorage.getItem('theme') || 'light';
                html.setAttribute('data-theme', currentTheme);

                // Check system preference if no saved preference
                if (!localStorage.getItem('theme')) {{
                    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
                    if (prefersDark) {{
                        html.setAttribute('data-theme', 'dark');
                        localStorage.setItem('theme', 'dark');
                    }}
                }}

                // Toggle theme on button click
                if (themeToggle) {{
                    themeToggle.addEventListener('click', function() {{
                        const currentTheme = html.getAttribute('data-theme');
                        const newTheme = currentTheme === 'light' ? 'dark' : 'light';

                        html.setAttribute('data-theme', newTheme);
                        localStorage.setItem('theme', newTheme);

                        // Add a subtle animation to the button
                        themeToggle.style.transform = 'scale(0.95)';
                        setTimeout(() => {{
                            themeToggle.style.transform = 'scale(1)';
                        }}, 100);
                    }});

                    // Keyboard shortcut: Ctrl/Cmd + D
                    document.addEventListener('keydown', function(e) {{
                        if ((e.ctrlKey || e.metaKey) && e.key === 'd') {{
                            e.preventDefault();
                            themeToggle.click();
                        }}
                    }});
                }}

                // Listen for system theme changes
                window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {{
                    // Only update if user hasn't explicitly set a preference
                    if (!localStorage.getItem('theme')) {{
                        const newTheme = e.matches ? 'dark' : 'light';
                        html.setAttribute('data-theme', newTheme);
                    }}
                }});
            }})();

            // Mobile-specific enhancements
            (function() {{
                // Detect mobile device
                const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
                const isTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 0;

                if (isMobile || isTouch) {{
                    // Add mobile class to body for CSS targeting
                    document.body.classList.add('mobile-device');

                    // Prevent double-tap zoom on buttons and interactive elements
                    document.addEventListener('touchend', function(e) {{
                        const target = e.target;
                        if (target.tagName === 'BUTTON' ||
                            target.classList.contains('clickable') ||
                            target.closest('button') ||
                            target.closest('.dash-table-container')) {{
                            e.preventDefault();
                            // Trigger click manually
                            target.click();
                        }}
                    }}, {{ passive: false }});

                    // Enhanced scroll performance for tables
                    const tables = document.querySelectorAll('.dash-table-container');
                    tables.forEach(table => {{
                        table.style.webkitOverflowScrolling = 'touch';
                        table.style.overflowX = 'auto';
                    }});

                    // Add touch feedback for interactive elements
                    document.addEventListener('touchstart', function(e) {{
                        const target = e.target;
                        if (target.tagName === 'BUTTON' ||
                            target.classList.contains('clickable') ||
                            target.closest('button')) {{
                            target.style.opacity = '0.7';
                            setTimeout(() => {{ target.style.opacity = '1'; }}, 100);
                        }}
                    }}, {{ passive: true }});

                    // Optimize Plotly graphs for touch
                    if (window.Plotly) {{
                        const plots = document.querySelectorAll('.js-plotly-plot');
                        plots.forEach(plot => {{
                            // Disable scroll zoom by default on mobile
                            if (plot.layout) {{
                                plot.layout.dragmode = 'pan';
                            }}
                        }});
                    }}

                    // Add orientation change handler
                    window.addEventListener('orientationchange', function() {{
                        setTimeout(() => {{
                            // Force re-render of graphs on orientation change
                            if (window.Plotly) {{
                                const plots = document.querySelectorAll('.js-plotly-plot');
                                plots.forEach(plot => {{
                                    Plotly.Plots.resize(plot);
                                }});
                            }}
                        }}, 200);
                    }});

                    // Smooth scroll for navigation
                    document.querySelectorAll('a[href^="#"]').forEach(anchor => {{
                        anchor.addEventListener('click', function(e) {{
                            e.preventDefault();
                            const target = document.querySelector(this.getAttribute('href'));
                            if (target) {{
                                target.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                            }}
                        }});
                    }});
                }}

                // Viewport height fix for mobile browsers (address bar issue)
                function setVHProperty() {{
                    const vh = window.innerHeight * 0.01;
                    document.documentElement.style.setProperty('--vh', `${{vh}}px`);
                }}
                setVHProperty();
                window.addEventListener('resize', setVHProperty);
                window.addEventListener('orientationchange', setVHProperty);
            }})();

        </script>
    </body>
</html>
'''

# Define the main layout using modular components
app.layout = html.Div(
    [
        # Toast notification container
        html.Div(id="toast-container", className="toast-container"),
        # Auto-refresh component
        dcc.Interval(
            id="interval-component",
            interval=DASHBOARD_CONFIG["refresh_interval"],
            n_intervals=0,
        ),
        # Download component for exporting reports
        dcc.Download(id="download-report"),
        # System Overview Section
        # Main Dashboard Tabs
        dcc.Tabs(
            [
                dcc.Tab(
                    label="Usage Overview",
                    children=[
                        html.Div(
                            id="server-grid", children=create_compact_server_grid()
                        ),
                    ],
                    style={"padding": "20px", "fontSize": "16px", "fontWeight": "600"},
                    selected_style={
                        "padding": "20px",
                        "fontSize": "16px",
                        "fontWeight": "600",
                        "backgroundColor": KU_COLORS["primary"],
                        "color": "white",
                    },
                ),
                dcc.Tab(
                    label="Server Details",
                    children=[
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Div(
                                            [
                                                html.I(
                                                    className="fas fa-tachometer-alt",
                                                    style={
                                                        "marginRight": "12px",
                                                        "fontSize": "20px",
                                                    },
                                                ),
                                                "System Overview",
                                            ],
                                            className="card-title",
                                        ),
                                    ],
                                    className="card-header",
                                ),
                                html.Div(
                                    id="system-overview",
                                    children=create_system_overview(),
                                ),
                            ],
                            className="card",
                        ),
                        html.Div(
                            id="enhanced-server-cards",
                            children=create_enhanced_server_cards(),
                        ),
                    ],
                    style={"padding": "20px", "fontSize": "16px", "fontWeight": "600"},
                    selected_style={
                        "padding": "20px",
                        "fontSize": "16px",
                        "fontWeight": "600",
                        "backgroundColor": KU_COLORS["primary"],
                        "color": "white",
                    },
                ),
                dcc.Tab(
                    label="User Activity",
                    children=[
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Div(
                                            [
                                                html.I(
                                                    className="fas fa-users",
                                                    style={
                                                        "marginRight": "12px",
                                                        "fontSize": "20px",
                                                    },
                                                ),
                                                "User Activity Monitor",
                                            ],
                                            className="card-title",
                                        ),
                                        html.Div(
                                            "Active user sessions and resource consumption",
                                            className="card-subtitle",
                                        ),
                                    ],
                                    className="card-header",
                                ),
                                html.Div(
                                    id="enhanced-users-table",
                                    children=create_enhanced_users_table(),
                                ),
                            ],
                            className="card",
                        )
                    ],
                    style={"padding": "20px", "fontSize": "16px", "fontWeight": "600"},
                    selected_style={
                        "padding": "20px",
                        "fontSize": "16px",
                        "fontWeight": "600",
                        "backgroundColor": KU_COLORS["primary"],
                        "color": "white",
                    },
                ),
                dcc.Tab(
                    label="Performance Analytics",
                    children=[
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Div(
                                            [
                                                html.I(
                                                    className="fas fa-chart-line",
                                                    style={
                                                        "marginRight": "12px",
                                                        "fontSize": "20px",
                                                    },
                                                ),
                                                "Performance Analytics",
                                            ],
                                            className="card-title",
                                        ),
                                        html.Div(
                                            "Historical metrics and trend analysis",
                                            className="card-subtitle",
                                        ),
                                    ],
                                    className="card-header",
                                ),
                                html.Div(
                                    id="enhanced-historical-graphs",
                                    children=create_enhanced_historical_graphs(),
                                ),
                            ],
                            className="card",
                        )
                    ],
                    style={"padding": "20px", "fontSize": "16px", "fontWeight": "600"},
                    selected_style={
                        "padding": "20px",
                        "fontSize": "16px",
                        "fontWeight": "600",
                        "backgroundColor": KU_COLORS["primary"],
                        "color": "white",
                    },
                ),
                dcc.Tab(
                    label="Network Monitor",
                    children=[
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Div(
                                            [
                                                html.I(
                                                    className="fas fa-network-wired",
                                                    style={
                                                        "marginRight": "12px",
                                                        "fontSize": "20px",
                                                    },
                                                ),
                                                "Network Activity Monitor",
                                            ],
                                            className="card-title",
                                        ),
                                        html.Div(
                                            "Connection statistics and network health",
                                            className="card-subtitle",
                                        ),
                                    ],
                                    className="card-header",
                                ),
                                html.Div(
                                    id="network-monitor",
                                    children=create_network_monitor(),
                                ),
                            ],
                            className="card",
                        )
                    ],
                    style={"padding": "20px", "fontSize": "16px", "fontWeight": "600"},
                    selected_style={
                        "padding": "20px",
                        "fontSize": "16px",
                        "fontWeight": "600",
                        "backgroundColor": KU_COLORS["primary"],
                        "color": "white",
                    },
                ),
            ]
        ),
        # Footer with refresh controls
        html.Div(
            [
                html.Button(
                    [
                        html.I(
                            className="fas fa-sync-alt", style={"marginRight": "8px"}
                        ),
                        "Refresh All Data",
                    ],
                    id="refresh-button",
                    className="btn",
                ),
                html.Button(
                    [
                        html.I(
                            className="fas fa-download", style={"marginRight": "8px"}
                        ),
                        "Export Report",
                    ],
                    id="export-button",
                    className="btn btn-secondary",
                    style={"marginLeft": "12px"},
                ),
                html.Div(
                    id="last-updated",
                    style={
                        "display": "inline-block",
                        "marginLeft": "24px",
                        "fontSize": "14px",
                        "color": KU_COLORS["muted"],
                    },
                ),
            ],
            style={
                "margin": "32px 0",
                "textAlign": "right",
                "padding": "20px",
                "borderTop": f"1px solid {KU_COLORS['border']}",
                "backgroundColor": "white",
                "borderRadius": "12px",
            },
        ),
    ]
)

# Register callbacks
register_callbacks(app)

if __name__ == "__main__":
    logger.info("Starting Khalifa University Server Monitoring Dashboard...")
    logger.info(f"Debug mode: {os.getenv('DEBUG') == 'True'}")
    app.run(debug=(os.getenv("DEBUG") == "True"), host="0.0.0.0", port=3000)
