"""
Loading Components for Server Monitoring Dashboard
Provides skeleton screens, loaders, and empty states for better UX
"""

from dash import html
from config import KU_COLORS


def create_skeleton_card():
    """
    Create a skeleton loading card for server cards

    Returns:
        html.Div: Skeleton card component
    """
    return html.Div(
        [
            html.Div(className="skeleton skeleton-header"),
            html.Div(className="skeleton skeleton-badge"),
            html.Div(
                [
                    html.Div(className="skeleton skeleton-metric"),
                    html.Div(className="skeleton skeleton-metric"),
                    html.Div(className="skeleton skeleton-metric"),
                    html.Div(className="skeleton skeleton-metric"),
                ],
                className="skeleton-metrics-row",
            ),
        ],
        className="server-card skeleton-card",
    )


def create_skeleton_table(rows=5):
    """
    Create a skeleton loading table

    Args:
        rows (int): Number of skeleton rows to display

    Returns:
        html.Div: Skeleton table component
    """
    skeleton_rows = []
    for i in range(rows):
        skeleton_rows.append(
            html.Div(
                [
                    html.Div(className="skeleton skeleton-cell"),
                    html.Div(className="skeleton skeleton-cell"),
                    html.Div(className="skeleton skeleton-cell"),
                    html.Div(className="skeleton skeleton-cell"),
                ],
                className="skeleton-row",
            )
        )

    return html.Div(
        [
            html.Div(className="skeleton skeleton-table-header"),
            html.Div(skeleton_rows, className="skeleton-table-body"),
        ],
        className="skeleton-table",
    )


def create_skeleton_graph():
    """
    Create a skeleton loading graph

    Returns:
        html.Div: Skeleton graph component
    """
    return html.Div(
        [
            html.Div(className="skeleton skeleton-graph-title"),
            html.Div(className="skeleton skeleton-graph-chart"),
            html.Div(className="skeleton skeleton-graph-legend"),
        ],
        className="skeleton-graph",
    )


def create_loading_spinner(size="medium", message="Loading..."):
    """
    Create a KU-branded loading spinner

    Args:
        size (str): Size of spinner (small, medium, large)
        message (str): Loading message to display

    Returns:
        html.Div: Loading spinner component
    """
    size_classes = {
        "small": "spinner-small",
        "medium": "spinner-medium",
        "large": "spinner-large",
    }

    return html.Div(
        [
            html.Div(
                [
                    html.Div(className="spinner-ring"),
                    html.Div(className="spinner-ring"),
                    html.Div(className="spinner-ring"),
                    html.Div(className="spinner-ring"),
                ],
                className=f"spinner {size_classes.get(size, 'spinner-medium')}",
            ),
            html.P(message, className="spinner-message")
            if message
            else None,
        ],
        className="loading-container",
    )


def create_empty_state(icon="fas fa-database", title="No Data Available", message="", action_button=None):
    """
    Create an enhanced empty state component

    Args:
        icon (str): FontAwesome icon class
        title (str): Main title for empty state
        message (str): Descriptive message
        action_button (html.Button): Optional action button

    Returns:
        html.Div: Empty state component
    """
    return html.Div(
        [
            html.Div(
                [
                    html.I(className=icon, style={"fontSize": "64px", "marginBottom": "20px"}),
                    html.H3(title, className="empty-state-title"),
                    html.P(message, className="empty-state-message") if message else None,
                    action_button if action_button else None,
                ],
                className="empty-state-content",
            )
        ],
        className="empty-state",
    )


def create_empty_server_state():
    """Create empty state for server data"""
    return create_empty_state(
        icon="fas fa-server",
        title="No Server Data Available",
        message="Server metrics are currently unavailable. This could be due to network issues or the data collection service being offline.",
        action_button=html.Button(
            [html.I(className="fas fa-sync-alt", style={"marginRight": "8px"}), "Refresh Data"],
            id="refresh-empty-state",
            className="btn btn-primary",
        ),
    )


def create_empty_user_state():
    """Create empty state for user data"""
    return create_empty_state(
        icon="fas fa-users",
        title="No Active Users",
        message="There are currently no logged-in users on any servers.",
    )


def create_empty_network_state():
    """Create empty state for network data"""
    return create_empty_state(
        icon="fas fa-network-wired",
        title="No Network Data",
        message="Network statistics are currently unavailable.",
    )


def create_progress_bar(percentage, label="", show_percentage=True):
    """
    Create an animated progress bar

    Args:
        percentage (float): Progress percentage (0-100)
        label (str): Label for the progress bar
        show_percentage (bool): Whether to show percentage text

    Returns:
        html.Div: Progress bar component
    """
    # Determine color based on percentage
    if percentage < 50:
        color_class = "progress-success"
    elif percentage < 85:
        color_class = "progress-warning"
    else:
        color_class = "progress-danger"

    return html.Div(
        [
            html.Div(
                [
                    html.Span(label, className="progress-label") if label else None,
                    html.Span(f"{percentage:.0f}%", className="progress-percentage")
                    if show_percentage
                    else None,
                ],
                className="progress-header",
            )
            if label or show_percentage
            else None,
            html.Div(
                [
                    html.Div(
                        className=f"progress-fill {color_class}",
                        style={"width": f"{min(percentage, 100)}%"},
                        **{"data-percentage": f"{percentage:.0f}"},
                    )
                ],
                className="progress-bar",
            ),
        ],
        className="progress-container",
    )


def create_loading_overlay(message="Loading..."):
    """
    Create a full-screen loading overlay

    Args:
        message (str): Loading message

    Returns:
        html.Div: Loading overlay component
    """
    return html.Div(
        [
            html.Div(
                [
                    create_loading_spinner(size="large", message=message),
                ],
                className="loading-overlay-content",
            )
        ],
        id="loading-overlay",
        className="loading-overlay",
        style={"display": "none"},  # Hidden by default
    )


def create_pulse_indicator(status="online", size="small"):
    """
    Create a pulsing status indicator

    Args:
        status (str): Status type (online, warning, offline)
        size (str): Size (small, medium, large)

    Returns:
        html.Div: Pulse indicator component
    """
    status_colors = {
        "online": KU_COLORS["success"],
        "warning": KU_COLORS["warning"],
        "offline": KU_COLORS["danger"],
        "unknown": KU_COLORS["muted"],
    }

    size_classes = {
        "small": "pulse-small",
        "medium": "pulse-medium",
        "large": "pulse-large",
    }

    return html.Div(
        [
            html.Div(className=f"pulse-dot {status}", **{"data-status": status}),
            html.Div(className=f"pulse-ring {status}", **{"data-status": status}),
        ],
        className=f"pulse-indicator {size_classes.get(size, 'pulse-small')}",
        style={"--pulse-color": status_colors.get(status, KU_COLORS["muted"])},
    )


def create_number_counter(value, label="", prefix="", suffix="", animate=True):
    """
    Create an animated number counter

    Args:
        value (float): The number to display
        label (str): Label for the counter
        prefix (str): Prefix (e.g., "$")
        suffix (str): Suffix (e.g., "%", "GB")
        animate (bool): Whether to animate the count-up

    Returns:
        html.Div: Number counter component
    """
    return html.Div(
        [
            html.Div(
                [
                    html.Span(prefix, className="counter-prefix") if prefix else None,
                    html.Span(
                        f"{value:.1f}" if isinstance(value, float) else str(value),
                        className="counter-value" + (" animated" if animate else ""),
                        **{"data-target": str(value)},
                    ),
                    html.Span(suffix, className="counter-suffix") if suffix else None,
                ],
                className="counter-number",
            ),
            html.Div(label, className="counter-label") if label else None,
        ],
        className="number-counter",
    )


def create_trend_indicator(current, previous, metric_name="", reverse_colors=False):
    """
    Create a trend indicator showing change from previous value

    Args:
        current (float): Current value
        previous (float): Previous value
        metric_name (str): Name of metric (for context)
        reverse_colors (bool): Reverse color logic (up=bad, down=good) for resources

    Returns:
        html.Div: Trend indicator component
    """
    if previous == 0 or previous is None:
        return html.Span("—", className="trend-neutral")

    change = ((current - previous) / previous) * 100
    abs_change = abs(change)

    # Determine arrow and color
    if abs_change < 1:
        arrow = "→"
        color_class = "trend-neutral"
        icon_class = "fas fa-minus"
    elif change > 0:
        arrow = "↑"
        # For resource metrics (CPU, RAM, Disk), up is bad
        color_class = "trend-danger" if reverse_colors else "trend-success"
        icon_class = "fas fa-arrow-up"
    else:
        arrow = "↓"
        # For resource metrics (CPU, RAM, Disk), down is good
        color_class = "trend-success" if reverse_colors else "trend-danger"
        icon_class = "fas fa-arrow-down"

    return html.Div(
        [
            html.I(className=f"{icon_class} trend-icon"),
            html.Span(f"{abs_change:.1f}%", className="trend-value"),
        ],
        className=f"trend-indicator {color_class}",
        **{
            "aria-label": f"{metric_name} changed by {change:.1f}% "
            + ("increase" if change > 0 else "decrease"),
            "title": "vs previous period",
        },
    )


def create_badge(text, badge_type="info", icon=None):
    """
    Create a status badge

    Args:
        text (str): Badge text
        badge_type (str): Type (success, warning, danger, info)
        icon (str): Optional icon class

    Returns:
        html.Span: Badge component
    """
    return html.Span(
        [
            html.I(className=icon, style={"marginRight": "6px"}) if icon else None,
            text,
        ],
        className=f"badge badge-{badge_type}",
    )


def create_tooltip(content, tooltip_text, position="top"):
    """
    Create a component with a tooltip

    Args:
        content: The content to wrap
        tooltip_text (str): Tooltip text
        position (str): Tooltip position (top, bottom, left, right)

    Returns:
        html.Div: Component with tooltip
    """
    return html.Div(
        [
            content,
            html.Span(tooltip_text, className=f"tooltip-text tooltip-{position}"),
        ],
        className="tooltip-container",
    )
