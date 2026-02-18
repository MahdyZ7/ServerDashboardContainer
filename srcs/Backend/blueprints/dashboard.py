"""
Dashboard Blueprint
Handles all dashboard page routes
Single Responsibility: Dashboard view rendering
"""
from flask import Blueprint, render_template, request
import logging

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
def index():
    """
    Main dashboard landing page
    Shows usage overview by default
    """
    return render_template('dashboard/index.html', active_tab='overview')


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
