# Configuration file for the Server Monitoring Dashboard
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Official Khalifa University brand colors per 2020 Brand Guidelines
KU_COLORS = {
    'primary': '#0057B8',        # Official KU Blue (Pantone 2935)
    'secondary': '#6F5091',      # KU Purple (Pantone 7677)
    'accent': '#78D64B',         # KU Green (Pantone 7488)
    'undergraduate': '#00A9CE',  # Undergraduate Blue (Pantone 312)
    'graduate': '#6F5091',       # Graduate Purple (Pantone 7677)
    'postgraduate': '#F8485E',   # Postgraduate Red (Pantone 1785)
    'orange': '#FF8F1C',         # KU Orange (Pantone 1495)
    'light_gray': '#D0D0CE',     # Cool Gray 2 (Pantone Cool Gray 2)
    'dark_gray': '#75787B',      # Cool Gray 9 (Pantone Cool Gray 9)
    'light_brown': '#C5B9AC',    # Light Brown (Pantone 7528)
    'body_text': '#1A1A1A',      # Body text (K:90 equivalent)
    'white': '#FFFFFF',
    'light': '#F8F9FA',          # Light background
    'success': '#0057B8',        # Using KU Blue for success
    'warning': '#FF8F1C',        # Using KU Orange for warning
    'danger': '#F8485E',         # Using KU Red for danger
    'info': '#00A9CE',           # Using Undergraduate Blue for info
    'muted': '#75787B',          # Using Cool Gray 9
    'border': '#D0D0CE',         # Using Cool Gray 2
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

# API Configuration
API_BASE_URL = os.getenv('API_BASE_URL', 'http://API:5000/api')

# Dashboard Configuration
DASHBOARD_CONFIG = {
    'title': 'Khalifa University - KSRC Server Monitoring Dashboard',
    'refresh_interval': 900000,  # 15 minutes in milliseconds
    'logo_url': './assets/KU_logo.png',
    'logo_alt': 'Khalifa University Logo',
    'header_title': 'KSRC Server Monitoring',
    'meta_tags': [{'name': 'viewport', 'content': 'width=device-width, initial-scale=1.0'}]
}

# Performance Thresholds
PERFORMANCE_THRESHOLDS = {
    'cpu_warning': 5.0,
    'cpu_critical': 8.0,
    'memory_warning': 85,
    'memory_critical': 95,
    'disk_warning': 85,
    'disk_critical': 95,
    'high_connections': 50,
    'high_cpu_usage': 50,
    'high_memory_usage': 50,
    'high_disk_usage': 10
}

# Chart Configuration
CHART_CONFIG = {
    'default_height': 800,
    'time_ranges': [
        {'label': 'Last 6 Hours', 'value': 6},
        {'label': 'Last 12 Hours', 'value': 12},
        {'label': 'Last 24 Hours', 'value': 24},
        {'label': 'Last 3 Days', 'value': 72},
        {'label': 'Last Week', 'value': 168}
    ],
    'default_time_range': 24
}

# Table Configuration
TABLE_CONFIG = {
    'page_size': 15,
    'users_page_size': 30,
    'network_page_size': 10,
    'max_alerts': 5
}

# Font Configuration
FONTS = {
    'primary': "'DM Sans', 'Inter', 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif",
    'secondary': "'Inter', 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif",
    'google_fonts': [
        "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap",
        "https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap"
    ],
    'fontawesome': "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"
}

# Status Configuration
STATUS_CONFIG = {
    'offline_timeout_minutes': 15,
    'status_classes': {
        'online': 'status-online',
        'warning': 'status-warning',
        'offline': 'status-offline'
    },
    'performance_classes': {
        'excellent': 'perf-excellent',
        'good': 'perf-good',
        'fair': 'perf-fair',
        'poor': 'perf-poor'
    }
}

# Grid and Layout Configuration
LAYOUT_CONFIG = {
    'dashboard_padding': '32px',
    'card_gap': '24px',
    'server_card_min_width': '400px',
    'overview_stat_min_width': '300px',
    'network_stat_min_width': '200px',
    'metric_item_min_width': '120px'
}