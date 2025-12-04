"""
Enhanced Graph Configuration for Server Monitoring Dashboard
Provides polished, professional graph styling and UX improvements
"""

from config import KU_COLORS

# Enhanced color palette for graphs with opacity variations
GRAPH_COLORS = {
    "cpu": {
        "line": KU_COLORS["primary"],
        "fill": "rgba(0, 61, 165, 0.1)",  # KU Blue with 10% opacity
        "hover": "rgba(0, 61, 165, 0.2)",
    },
    "ram": {
        "line": KU_COLORS["secondary"],
        "fill": "rgba(111, 80, 145, 0.1)",  # KU Purple with 10% opacity
        "hover": "rgba(111, 80, 145, 0.2)",
    },
    "disk": {
        "line": KU_COLORS["accent"],
        "fill": "rgba(120, 214, 75, 0.1)",  # KU Green with 10% opacity
        "hover": "rgba(120, 214, 75, 0.2)",
    },
    "network": {
        "line": KU_COLORS["undergraduate"],
        "fill": "rgba(0, 169, 206, 0.1)",  # Undergraduate Blue
        "hover": "rgba(0, 169, 206, 0.2)",
    },
    "users": {
        "line": KU_COLORS["orange"],
        "fill": "rgba(245, 127, 41, 0.1)",  # KU Orange
        "hover": "rgba(245, 127, 41, 0.2)",
    },
    "warning": {
        "line": KU_COLORS["warning"],
        "fill": "rgba(245, 127, 41, 0.05)",
    },
    "critical": {
        "line": KU_COLORS["danger"],
        "fill": "rgba(227, 30, 36, 0.05)",
    },
    "grid": "rgba(209, 211, 212, 0.3)",  # Light gray for grid lines
    "zero": "rgba(109, 110, 113, 0.2)",  # Zero line color
}

# Enhanced layout configuration for all graphs
ENHANCED_LAYOUT = {
    "plot_bgcolor": "rgba(255, 255, 255, 0.95)",  # Slight off-white for depth
    "paper_bgcolor": "rgba(0, 0, 0, 0)",  # Transparent paper
    "font": {
        "family": "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        "size": 13,
        "color": KU_COLORS["text_primary"],
    },
    "title": {
        "font": {
            "family": "'Inter', sans-serif",
            "size": 18,
            "weight": 600,
            "color": KU_COLORS["text_primary"],
        },
        "x": 0.5,  # Center align
        "xanchor": "center",
    },
    "margin": dict(l=50, r=30, t=60, b=50),
    "hovermode": "x unified",  # Unified hover for comparing metrics
    "hoverlabel": {
        "bgcolor": "white",
        "font": {
            "family": "'Inter', sans-serif",
            "size": 12,
            "color": KU_COLORS["text_primary"],
        },
        "bordercolor": KU_COLORS["border"],
    },
    "showlegend": True,
    "legend": {
        "orientation": "h",
        "yanchor": "top",
        "y": -0.15,
        "xanchor": "center",
        "x": 0.5,
        "bgcolor": "rgba(255, 255, 255, 0.8)",
        "bordercolor": KU_COLORS["border"],
        "borderwidth": 1,
        "font": {"size": 12},
    },
}

# Enhanced X-axis configuration
ENHANCED_XAXIS = {
    "showgrid": True,
    "gridwidth": 1,
    "gridcolor": GRAPH_COLORS["grid"],
    "showline": True,
    "linewidth": 1,
    "linecolor": KU_COLORS["border"],
    "tickfont": {"size": 11, "color": KU_COLORS["text_secondary"]},
    "title": {
        "font": {"size": 12, "weight": 500, "color": KU_COLORS["text_primary"]},
        "standoff": 10,
    },
    "automargin": True,
}

# Enhanced Y-axis configuration
ENHANCED_YAXIS = {
    "showgrid": True,
    "gridwidth": 1,
    "gridcolor": GRAPH_COLORS["grid"],
    "showline": True,
    "linewidth": 1,
    "linecolor": KU_COLORS["border"],
    "tickfont": {"size": 11, "color": KU_COLORS["text_secondary"]},
    "title": {
        "font": {"size": 12, "weight": 500, "color": KU_COLORS["text_primary"]},
        "standoff": 10,
    },
    "zeroline": True,
    "zerolinewidth": 1,
    "zerolinecolor": GRAPH_COLORS["zero"],
    "automargin": True,
}

# Enhanced trace configuration for smooth, polished lines
def get_enhanced_trace_config(metric_type="cpu", show_fill=True):
    """
    Get enhanced trace configuration for different metric types

    Args:
        metric_type: Type of metric (cpu, ram, disk, network, users)
        show_fill: Whether to show area fill under the line

    Returns:
        dict: Plotly trace configuration
    """
    colors = GRAPH_COLORS.get(metric_type, GRAPH_COLORS["cpu"])

    config = {
        "mode": "lines",
        "line": {
            "color": colors["line"],
            "width": 2.5,
            "shape": "spline",  # Smooth curves instead of sharp angles
            "smoothing": 1.0,  # Maximum smoothing
        },
        "hovertemplate": "%{y:.2f}%<extra></extra>",  # Clean hover text
        "hoverlabel": {
            "bgcolor": colors["hover"],
            "bordercolor": colors["line"],
        },
    }

    if show_fill:
        config["fill"] = "tozeroy"
        config["fillcolor"] = colors["fill"]

    return config


# Enhanced trace for percentage metrics (CPU, RAM, Disk)
def get_percentage_trace_config(metric_name, color_key, timestamp, values):
    """
    Get enhanced trace for percentage-based metrics with better tooltips

    Args:
        metric_name: Display name (e.g., "CPU Load", "RAM Usage")
        color_key: Color key from GRAPH_COLORS (e.g., "cpu", "ram")
        timestamp: X-axis data (timestamps)
        values: Y-axis data (percentage values)

    Returns:
        dict: Complete trace configuration
    """
    colors = GRAPH_COLORS.get(color_key, GRAPH_COLORS["cpu"])

    return {
        "x": timestamp,
        "y": values,
        "mode": "lines+text",
        "name": metric_name,
        "line": {
            "color": colors["line"],
            "width": 2.5,
            "shape": "spline",
            "smoothing": 1.0,
        },
        "fill": "tozeroy",
        "fillcolor": colors["fill"],
        "hovertemplate": f"<b>{metric_name}</b><br>" +
                        "Time: %{x|%H:%M}<br>" +
                        "Value: %{y:.1f}%<br>" +
                        "<extra></extra>",
        "hoverlabel": {
            "bgcolor": "white",
            "bordercolor": colors["line"],
            "font": {"size": 12},
        },
        "text": [f"{metric_name}" if i == len(values) - 1 else "" for i in range(len(values))],
        "textfont": {
			"size": 10,
			"color": colors["line"],
			"weight": 500,
		},
        "textposition": "top left",
    }


# Configuration for threshold lines (warning, critical)
def get_threshold_line_config(value, label, line_type="warning"):
    """
    Get configuration for threshold reference lines

    Args:
        value: Y-axis value for the threshold
        label: Label text for the threshold
        line_type: Type of threshold (warning, critical)

    Returns:
        dict: Threshold line configuration
    """
    colors = GRAPH_COLORS.get(line_type, GRAPH_COLORS["warning"])

    return {
        "y": value,
        "line_dash": "dash" if line_type == "warning" else "dot",
        "line_color": colors["line"],
        "line_width": 1.5,
        "annotation": {
            "text": label,
            "font": {
                "size": 10,
                "color": colors["line"],
                "weight": 500,
            },
            "showarrow": False,
            "xref": "paper",
            "x": 1.02,
        },
    }


# Interactive configuration (zoom, pan, etc.)
INTERACTIVE_CONFIG = {
    "displayModeBar": True,
    "modeBarButtonsToRemove": [
        "lasso2d",
        "select2d",
        "autoScale2d",
        "toggleSpikelines",
    ],
    "displaylogo": False,
    "toImageButtonOptions": {
        "format": "png",
        "filename": "server_metrics",
        "height": 800,
        "width": 1400,
        "scale": 2,
    },
    # Mobile-friendly settings
    "scrollZoom": False,  # Prevent accidental zoom on scroll
    "doubleClick": "reset",  # Double-tap to reset view
}

# Mobile-specific interactive config (touch-optimized)
MOBILE_INTERACTIVE_CONFIG = {
    "displayModeBar": True,
    "modeBarButtonsToRemove": [
        "lasso2d",
        "select2d",
        "autoScale2d",
        "toggleSpikelines",
        "zoom2d",  # Remove zoom button on mobile (use pinch instead)
    ],
    "displaylogo": False,
    "scrollZoom": False,  # Disable scroll zoom on mobile
    "doubleClick": "reset",  # Double-tap to reset
    "showTips": False,  # Hide tips on mobile to save space
    "toImageButtonOptions": {
        "format": "png",
        "filename": "server_metrics_mobile",
        "height": 600,
        "width": 800,
        "scale": 2,
    },
}

# Responsive configuration for mobile devices
MOBILE_LAYOUT_OVERRIDES = {
    "margin": dict(l=40, r=15, t=40, b=40),  # Tighter margins for mobile
    "font": {"size": 10, "family": "Inter, sans-serif"},  # Smaller font
    "title": {"font": {"size": 14}},  # Smaller title
    "xaxis": {
        "title": {"font": {"size": 10}},
        "tickfont": {"size": 9},
        "automargin": True,  # Auto-adjust margins
    },
    "yaxis": {
        "title": {"font": {"size": 10}},
        "tickfont": {"size": 9},
        "automargin": True,
    },
    "legend": {
        "orientation": "h",  # Horizontal legend on mobile
        "yanchor": "bottom",
        "y": -0.2,  # Below graph
        "xanchor": "center",
        "x": 0.5,
        "font": {"size": 9},
    },
    "hovermode": "x unified",  # Unified hover for better mobile UX
}

# Animation configuration for smooth updates
ANIMATION_CONFIG = {
    "transition": {
        "duration": 300,
        "easing": "cubic-in-out",
    },
    "frame": {
        "duration": 300,
        "redraw": True,
    },
}