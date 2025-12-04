"""
Enhanced Table and Card Configuration for Server Monitoring Dashboard
Provides modern, polished styling for tables and card components
"""

from config import KU_COLORS

# Enhanced Table Styling Configuration
ENHANCED_TABLE_STYLE = {
    "table": {
        "overflowX": "auto",
        "borderRadius": "12px",
        "boxShadow": "0 2px 8px rgba(0, 61, 165, 0.08)",
        "border": f"1px solid {KU_COLORS['border']}",
    },
    "cell": {
        "textAlign": "left",
        "padding": "14px 16px",
        "fontFamily": "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        "fontSize": "14px",
        "lineHeight": "1.5",
        "color": KU_COLORS["text_primary"],
        "borderBottom": f"1px solid {KU_COLORS['border']}",
        "transition": "background-color 0.2s ease",
    },
    "header": {
        "backgroundColor": KU_COLORS["primary"],
        "color": "white",
        "fontWeight": "600",
        "fontSize": "13px",
        "padding": "16px",
        "textTransform": "uppercase",
        "letterSpacing": "0.5px",
        "fontFamily": "'Inter', sans-serif",
        "borderBottom": "none",
    },
    "data": {
        "backgroundColor": "white",
        "border": "none",
    },
}

# Enhanced conditional styling for table cells
def get_enhanced_table_conditional_styles():
    """
    Get enhanced conditional styles for tables with modern design
    """
    return [
        # Zebra striping with subtle color
        {
            "if": {"row_index": "odd"},
            "backgroundColor": "rgba(248, 249, 250, 0.6)",
        },
        # Hover effect
        {
            "if": {"state": "active"},
            "backgroundColor": "rgba(0, 61, 165, 0.04)",
            "border": f"1px solid {KU_COLORS['primary']}",
        },
        # CPU Warning (50-70%)
        {
            "if": {
                "column_id": "cpu",
                "filter_query": "{cpu} > 50 && {cpu} <= 70"
            },
            "backgroundColor": "rgba(245, 127, 41, 0.08)",
            "color": KU_COLORS["warning"],
            "fontWeight": "600",
            "borderLeft": f"3px solid {KU_COLORS['warning']}",
        },
        # CPU Critical (>70%)
        {
            "if": {
                "column_id": "cpu",
                "filter_query": "{cpu} > 70"
            },
            "backgroundColor": "rgba(227, 30, 36, 0.08)",
            "color": KU_COLORS["danger"],
            "fontWeight": "700",
            "borderLeft": f"3px solid {KU_COLORS['danger']}",
        },
        # Memory Warning (50-70%)
        {
            "if": {
                "column_id": "mem",
                "filter_query": "{mem} > 50 && {mem} <= 70"
            },
            "backgroundColor": "rgba(245, 127, 41, 0.08)",
            "color": KU_COLORS["warning"],
            "fontWeight": "600",
            "borderLeft": f"3px solid {KU_COLORS['warning']}",
        },
        # Memory Critical (>70%)
        {
            "if": {
                "column_id": "mem",
                "filter_query": "{mem} > 70"
            },
            "backgroundColor": "rgba(227, 30, 36, 0.08)",
            "color": KU_COLORS["danger"],
            "fontWeight": "700",
            "borderLeft": f"3px solid {KU_COLORS['danger']}",
        },
        # Disk Warning (>10GB)
        {
            "if": {
                "column_id": "disk",
                "filter_query": "{disk} > 10"
            },
            "backgroundColor": "rgba(245, 127, 41, 0.08)",
            "color": KU_COLORS["warning"],
            "fontWeight": "600",
            "borderLeft": f"3px solid {KU_COLORS['warning']}",
        },
        # Status: Offline
        {
            "if": {
                "column_id": "status",
                "filter_query": "{status} contains Offline"
            },
            "backgroundColor": "rgba(227, 30, 36, 0.08)",
            "color": KU_COLORS["danger"],
            "fontWeight": "600",
        },
        # Status: Warning
        {
            "if": {
                "column_id": "status",
                "filter_query": "{status} contains Warning"
            },
            "backgroundColor": "rgba(245, 127, 41, 0.08)",
            "color": KU_COLORS["warning"],
            "fontWeight": "600",
        },
        # Status: Online/Normal
        {
            "if": {
                "column_id": "status",
                "filter_query": "{status} contains Online"
            },
            "color": KU_COLORS["success"],
            "fontWeight": "500",
        },
        # High Usage Status
        {
            "if": {
                "column_id": "status",
                "filter_query": "{status} contains High"
            },
            "backgroundColor": "rgba(227, 30, 36, 0.08)",
            "color": KU_COLORS["danger"],
            "fontWeight": "600",
            "padding": "8px 12px",
        },
        # TCP Connections Critical (>100)
        {
            "if": {
                "column_id": "tcp_connections",
                "filter_query": "{tcp_connections} > 100"
            },
            "backgroundColor": "rgba(227, 30, 36, 0.08)",
            "color": KU_COLORS["danger"],
            "fontWeight": "600",
            "borderLeft": f"3px solid {KU_COLORS['danger']}",
        },
        # TCP Connections Warning (>50)
        {
            "if": {
                "column_id": "tcp_connections",
                "filter_query": "{tcp_connections} > 50 && {tcp_connections} <= 100"
            },
            "backgroundColor": "rgba(245, 127, 41, 0.08)",
            "color": KU_COLORS["warning"],
            "fontWeight": "600",
            "borderLeft": f"3px solid {KU_COLORS['warning']}",
        },
    ]


# Network table specific conditional styles
def get_network_table_conditional_styles():
    """Get conditional styles specifically for network monitoring table"""
    return [
        {
            "if": {"row_index": "odd"},
            "backgroundColor": "rgba(248, 249, 250, 0.6)",
        },
        {
            "if": {"state": "active"},
            "backgroundColor": "rgba(0, 61, 165, 0.04)",
        },
        {
            "if": {
                "column_id": "tcp_connections",
                "filter_query": "{tcp_connections} > 100"
            },
            "backgroundColor": "rgba(227, 30, 36, 0.08)",
            "color": KU_COLORS["danger"],
            "fontWeight": "600",
            "borderLeft": f"3px solid {KU_COLORS['danger']}",
        },
        {
            "if": {
                "column_id": "tcp_connections",
                "filter_query": "{tcp_connections} > 50 && {tcp_connections} <= 100"
            },
            "backgroundColor": "rgba(245, 127, 41, 0.08)",
            "color": KU_COLORS["warning"],
            "fontWeight": "600",
        },
        {
            "if": {
                "column_id": "status",
                "filter_query": "{status} = Offline"
            },
            "backgroundColor": "rgba(227, 30, 36, 0.08)",
            "color": KU_COLORS["danger"],
            "fontWeight": "600",
        },
        {
            "if": {
                "column_id": "status",
                "filter_query": "{status} = Warning"
            },
            "backgroundColor": "rgba(245, 127, 41, 0.08)",
            "color": KU_COLORS["warning"],
            "fontWeight": "600",
        },
        {
            "if": {
                "column_id": "status",
                "filter_query": "{status} = Online"
            },
            "color": KU_COLORS["success"],
            "fontWeight": "500",
        },
    ]


# Enhanced Card Styling
ENHANCED_CARD_STYLE = {
    "default": {
        "backgroundColor": "white",
        "borderRadius": "16px",
        "boxShadow": "0 4px 12px rgba(0, 61, 165, 0.08)",
        "padding": "28px",
        "marginBottom": "24px",
        "border": f"1px solid {KU_COLORS['border']}",
        "transition": "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
        "position": "relative",
        "overflow": "hidden",
    },
    "hover": {
        "boxShadow": "0 8px 24px rgba(0, 61, 165, 0.12)",
        "transform": "translateY(-2px)",
    },
    "header": {
        "display": "flex",
        "alignItems": "center",
        "justifyContent": "space-between",
        "marginBottom": "20px",
        "paddingBottom": "16px",
        "borderBottom": f"2px solid {KU_COLORS['border']}",
    },
    "title": {
        "fontSize": "20px",
        "fontWeight": "600",
        "color": KU_COLORS["text_primary"],
        "fontFamily": "'Inter', sans-serif",
        "display": "flex",
        "alignItems": "center",
        "gap": "12px",
    },
    "subtitle": {
        "fontSize": "14px",
        "color": KU_COLORS["text_secondary"],
        "fontWeight": "400",
        "marginTop": "4px",
    },
}

# Stat Card Styling (for overview statistics)
STAT_CARD_STYLE = {
    "container": {
        "backgroundColor": "white",
        "borderRadius": "12px",
        "padding": "20px 24px",
        "boxShadow": "0 2px 8px rgba(0, 61, 165, 0.06)",
        "border": f"1px solid {KU_COLORS['border']}",
        "transition": "all 0.2s ease",
        "cursor": "default",
        "minWidth": "180px",
    },
    "hover": {
        "boxShadow": "0 4px 12px rgba(0, 61, 165, 0.1)",
        "transform": "translateY(-2px)",
        "borderColor": KU_COLORS["primary"],
    },
    "value": {
        "fontSize": "32px",
        "fontWeight": "700",
        "color": KU_COLORS["primary"],
        "lineHeight": "1.2",
        "fontFamily": "'Inter', sans-serif",
        "marginBottom": "8px",
    },
    "label": {
        "fontSize": "13px",
        "color": KU_COLORS["text_secondary"],
        "fontWeight": "500",
        "textTransform": "uppercase",
        "letterSpacing": "0.5px",
    },
    "icon": {
        "fontSize": "40px",
        "color": KU_COLORS["primary"],
        "opacity": "0.15",
        "position": "absolute",
        "right": "20px",
        "top": "20px",
    },
}

# Alert/Badge Styling
BADGE_STYLES = {
    "success": {
        "backgroundColor": "rgba(0, 61, 165, 0.1)",
        "color": KU_COLORS["success"],
        "padding": "6px 12px",
        "borderRadius": "20px",
        "fontSize": "12px",
        "fontWeight": "600",
        "display": "inline-block",
        "textTransform": "uppercase",
        "letterSpacing": "0.5px",
    },
    "warning": {
        "backgroundColor": "rgba(245, 127, 41, 0.1)",
        "color": KU_COLORS["warning"],
        "padding": "6px 12px",
        "borderRadius": "20px",
        "fontSize": "12px",
        "fontWeight": "600",
        "display": "inline-block",
        "textTransform": "uppercase",
        "letterSpacing": "0.5px",
    },
    "danger": {
        "backgroundColor": "rgba(227, 30, 36, 0.1)",
        "color": KU_COLORS["danger"],
        "padding": "6px 12px",
        "borderRadius": "20px",
        "fontSize": "12px",
        "fontWeight": "600",
        "display": "inline-block",
        "textTransform": "uppercase",
        "letterSpacing": "0.5px",
    },
    "info": {
        "backgroundColor": "rgba(0, 169, 206, 0.1)",
        "color": KU_COLORS["info"],
        "padding": "6px 12px",
        "borderRadius": "20px",
        "fontSize": "12px",
        "fontWeight": "600",
        "display": "inline-block",
        "textTransform": "uppercase",
        "letterSpacing": "0.5px",
    },
}

# Button/Action Styling
BUTTON_STYLES = {
    "primary": {
        "backgroundColor": KU_COLORS["primary"],
        "color": "white",
        "padding": "10px 20px",
        "borderRadius": "8px",
        "border": "none",
        "fontSize": "14px",
        "fontWeight": "600",
        "cursor": "pointer",
        "transition": "all 0.2s ease",
        "boxShadow": "0 2px 4px rgba(0, 61, 165, 0.2)",
    },
    "secondary": {
        "backgroundColor": "white",
        "color": KU_COLORS["primary"],
        "padding": "10px 20px",
        "borderRadius": "8px",
        "border": f"2px solid {KU_COLORS['primary']}",
        "fontSize": "14px",
        "fontWeight": "600",
        "cursor": "pointer",
        "transition": "all 0.2s ease",
    },
}

# Enhanced Table Pagination Styling
PAGINATION_STYLE = {
    "previous-next-container": {
        "display": "flex",
        "justifyContent": "space-between",
        "padding": "12px 16px",
        "backgroundColor": "rgba(248, 249, 250, 0.6)",
        "borderTop": f"1px solid {KU_COLORS['border']}",
    },
    "button": {
        "backgroundColor": KU_COLORS["primary"],
        "color": "white",
        "border": "none",
        "padding": "8px 16px",
        "borderRadius": "6px",
        "fontSize": "13px",
        "fontWeight": "600",
        "cursor": "pointer",
        "transition": "all 0.2s ease",
    },
}

# Mobile-Responsive Table Styling
MOBILE_TABLE_STYLE = {
    "table": {
        "overflowX": "auto",
        "borderRadius": "8px",
        "boxShadow": "0 1px 4px rgba(0, 61, 165, 0.06)",
        "border": f"1px solid {KU_COLORS['border']}",
        "minWidth": "100%",
    },
    "cell": {
        "textAlign": "left",
        "padding": "10px 8px",
        "fontFamily": "'Inter', sans-serif",
        "fontSize": "12px",
        "lineHeight": "1.4",
        "color": KU_COLORS["text_primary"],
        "borderBottom": f"1px solid {KU_COLORS['border']}",
        "whiteSpace": "normal",  # Allow text wrapping on mobile
        "wordBreak": "break-word",  # Break long words
    },
    "header": {
        "backgroundColor": KU_COLORS["primary"],
        "color": "white",
        "fontWeight": "600",
        "fontSize": "11px",
        "padding": "12px 8px",
        "textTransform": "uppercase",
        "letterSpacing": "0.3px",
        "fontFamily": "'Inter', sans-serif",
        "borderBottom": "none",
        "position": "sticky",  # Sticky header on mobile
        "top": 0,
        "zIndex": 10,
    },
    "data": {
        "backgroundColor": "white",
        "border": "none",
    },
}

# Mobile-specific conditional styles (simplified for better performance)
def get_mobile_table_conditional_styles():
    """Get simplified conditional styles for mobile tables"""
    return [
        # Zebra striping
        {
            "if": {"row_index": "odd"},
            "backgroundColor": "rgba(248, 249, 250, 0.5)",
        },
        # Critical values (simplified - no border accent for mobile)
        {
            "if": {
                "column_id": "cpu",
                "filter_query": "{cpu} > 70"
            },
            "backgroundColor": "rgba(227, 30, 36, 0.1)",
            "color": KU_COLORS["danger"],
            "fontWeight": "700",
        },
        {
            "if": {
                "column_id": "mem",
                "filter_query": "{mem} > 70"
            },
            "backgroundColor": "rgba(227, 30, 36, 0.1)",
            "color": KU_COLORS["danger"],
            "fontWeight": "700",
        },
        # Warning values
        {
            "if": {
                "column_id": "cpu",
                "filter_query": "{cpu} > 50 && {cpu} <= 70"
            },
            "backgroundColor": "rgba(245, 127, 41, 0.1)",
            "color": KU_COLORS["warning"],
            "fontWeight": "600",
        },
        {
            "if": {
                "column_id": "mem",
                "filter_query": "{mem} > 50 && {mem} <= 70"
            },
            "backgroundColor": "rgba(245, 127, 41, 0.1)",
            "color": KU_COLORS["warning"],
            "fontWeight": "600",
        },
    ]

# Touch-Friendly Table Configuration
TOUCH_FRIENDLY_TABLE_CONFIG = {
    "page_size": 10,  # Fewer rows per page on mobile
    "style_table": {
        "overflowX": "auto",
        "WebkitOverflowScrolling": "touch",  # Smooth scrolling on iOS
    },
    "style_cell": {
        "minWidth": "80px",  # Minimum column width
        "maxWidth": "200px",  # Maximum column width
        "overflow": "hidden",
        "textOverflow": "ellipsis",
    },
    "tooltip_delay": 0,  # Instant tooltips on touch
    "tooltip_duration": None,  # Keep tooltip until dismissed
}
