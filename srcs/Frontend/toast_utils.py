# Toast notification utilities for user feedback
from dash import html
import logging
from typing import Optional, Literal

logger = logging.getLogger(__name__)

ToastType = Literal['success', 'error', 'warning', 'info']


def create_toast(
    message: str,
    toast_type: ToastType = 'info',
    duration: int = 5000,
    toast_id: Optional[str] = None
) -> html.Div:
    """
    Create a toast notification component

    Args:
        message: Message to display
        toast_type: Type of toast ('success', 'error', 'warning', 'info')
        duration: Duration in milliseconds (0 for persistent)
        toast_id: Optional ID for the toast element

    Returns:
        Dash HTML component for toast
    """
    # Icon mapping
    icons = {
        'success': 'fas fa-check-circle',
        'error': 'fas fa-exclamation-circle',
        'warning': 'fas fa-exclamation-triangle',
        'info': 'fas fa-info-circle'
    }

    # Color mapping
    colors = {
        'success': '#27AE60',
        'error': '#E31E24',
        'warning': '#F57F29',
        'info': '#00A9CE'
    }

    toast_id = toast_id or f"toast-{toast_type}"

    return html.Div([
        html.I(className=icons.get(toast_type, icons['info']),
               style={'marginRight': '12px', 'fontSize': '20px'}),
        html.Span(message, style={'flex': 1}),
    ], id=toast_id, className=f"toast toast-{toast_type}",
        style={
        'display': 'flex',
        'alignItems': 'center',
        'padding': '16px 20px',
        'marginBottom': '12px',
        'borderRadius': '8px',
        'backgroundColor': 'white',
        'border': f'2px solid {colors.get(toast_type, colors["info"])}',
        'boxShadow': '0 4px 12px rgba(0,0,0,0.15)',
        'animation': 'slideInRight 0.3s ease-out',
        'color': colors.get(toast_type, colors['info']),
        'fontWeight': '500',
        'fontSize': '14px',
        'maxWidth': '400px'
    })


def create_toast_container(toasts: list) -> html.Div:
    """
    Create a container for multiple toasts

    Args:
        toasts: List of toast components

    Returns:
        Container div with all toasts
    """
    if not toasts:
        return html.Div(id='toast-container', style={'display': 'none'})

    return html.Div(
        toasts,
        id='toast-container',
        style={
            'position': 'fixed',
            'top': '80px',
            'right': '20px',
            'zIndex': '9999',
            'maxWidth': '400px'
        }
    )


def create_success_toast(message: str) -> html.Div:
    """Create a success toast"""
    logger.info(f"Success: {message}")
    return create_toast(message, 'success')


def create_error_toast(message: str) -> html.Div:
    """Create an error toast"""
    logger.error(f"Error toast: {message}")
    return create_toast(message, 'error', duration=0)  # Persistent


def create_warning_toast(message: str) -> html.Div:
    """Create a warning toast"""
    logger.warning(f"Warning: {message}")
    return create_toast(message, 'warning')


def create_info_toast(message: str) -> html.Div:
    """Create an info toast"""
    logger.info(f"Info: {message}")
    return create_toast(message, 'info')


def format_api_error_message(error: Exception) -> str:
    """
    Format an API error for user-friendly display

    Args:
        error: Exception from API call

    Returns:
        User-friendly error message
    """
    from exceptions import (
        APIConnectionError, APITimeoutError,
        APIResponseError, APIDataError
    )

    if isinstance(error, APIConnectionError):
        return "Unable to connect to the server. Please check your connection."
    elif isinstance(error, APITimeoutError):
        return "Request timed out. The server is taking too long to respond."
    elif isinstance(error, APIResponseError):
        if hasattr(error, 'status_code'):
            if error.status_code == 404:
                return "Data not found. The requested resource doesn't exist."
            elif error.status_code >= 500:
                return "Server error. Please try again later."
        return "The server returned an error. Please try again."
    elif isinstance(error, APIDataError):
        return "Received invalid data from the server."
    else:
        return "An unexpected error occurred. Please try again."


def format_validation_error_message(error: Exception) -> str:
    """
    Format a validation error for user-friendly display

    Args:
        error: ValidationError exception

    Returns:
        User-friendly error message
    """
    from exceptions import ValidationError

    if isinstance(error, ValidationError):
        # Extract the core message without technical details
        message = str(error.message)
        if len(message) > 100:
            message = message[:97] + "..."
        return message
    else:
        return "Invalid input provided."
