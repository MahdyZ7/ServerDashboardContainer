"""
Dashboard Blueprint
Handles all dashboard page routes
Single Responsibility: Dashboard view rendering
"""
from flask import Blueprint, abort, render_template
import logging

from utils.server_page import configured_servers, resolve_server

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
def index():
    """
    Main dashboard landing page
    Shows usage overview by default
    """
    return render_template('dashboard/index.html', active_tab='overview')


@dashboard_bp.app_context_processor
def inject_servers():
    """Monitored servers for the server-page links in the navigation"""
    return {'monitored_servers': configured_servers()}


@dashboard_bp.route('/server/<server_key>')
def server_page(server_key):
    """One server's status page. server_key: name, hostname, short hostname or IP,
    so a server's port 80 can redirect here."""
    servers = configured_servers()
    server_name = resolve_server(server_key, servers)
    if server_name is None:
        abort(404)
    server = next(s for s in servers if s['name'] == server_name)
    return render_template('server/index.html', server=server, current_server=server)


@dashboard_bp.route('/overview')
def usage_overview():
    """Usage overview tab - compact server grid"""
    return render_template('dashboard/index.html', active_tab='overview')


@dashboard_bp.route('/servers')
def server_details():
    """Server details tab - system overview and enhanced server cards"""
    return render_template('dashboard/index.html', active_tab='servers')


@dashboard_bp.route('/users')
def user_activity():
    """User activity tab - user activity monitor table"""
    return render_template('dashboard/index.html', active_tab='users')


@dashboard_bp.route('/analytics')
def performance_analytics():
    """Performance analytics tab - historical graphs and trends"""
    return render_template('dashboard/index.html', active_tab='analytics')


@dashboard_bp.route('/network')
def network_monitor():
    """Network monitor tab - connection statistics and network health"""
    return render_template('dashboard/index.html', active_tab='network')
