# Export utility functions for the Server Monitoring Dashboard
import pandas as pd
from datetime import datetime
import logging
from api_client import (get_latest_server_metrics, get_top_users,
                       get_system_overview, get_server_list, get_historical_metrics)

logging.basicConfig(level=logging.INFO)


def generate_export_report(format='csv'):
    """
    Generate a comprehensive report of all dashboard data

    Args:
        format: Export format ('csv', 'excel', 'json')

    Returns:
        Dictionary with export data or None if failed
    """
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Fetch all data
        server_metrics = get_latest_server_metrics()
        top_users = get_top_users()
        system_overview = get_system_overview()
        server_list = get_server_list()

        # Create DataFrames
        df_servers = pd.DataFrame(server_metrics) if server_metrics else pd.DataFrame()
        df_users = pd.DataFrame(top_users) if top_users else pd.DataFrame()

        # Create system overview DataFrame
        overview_data = []
        if system_overview:
            overview_data = [{
                'metric': 'Total Servers',
                'value': system_overview.get('total_servers', 0)
            }, {
                'metric': 'Active Servers',
                'value': system_overview.get('active_servers', 0)
            }, {
                'metric': 'Total Users',
                'value': system_overview.get('total_users', 0)
            }, {
                'metric': 'Average CPU Load',
                'value': f"{system_overview.get('avg_cpu_load', 0):.2f}"
            }, {
                'metric': 'Average Memory Usage',
                'value': f"{system_overview.get('avg_memory_usage', 0):.2f}%"
            }, {
                'metric': 'Average Disk Usage',
                'value': f"{system_overview.get('avg_disk_usage', 0):.2f}%"
            }]
        df_overview = pd.DataFrame(overview_data)

        # Fetch historical data for all servers (last 24 hours)
        historical_data = []
        for server_name in server_list:
            # server_list returns a list of strings (server names), not dictionaries
            if server_name:
                hist = get_historical_metrics(server_name, hours=24)
                if hist:
                    historical_data.extend(hist)
        df_historical = pd.DataFrame(historical_data) if historical_data else pd.DataFrame()

        export_data = {
            'timestamp': timestamp,
            'server_metrics': df_servers,
            'top_users': df_users,
            'system_overview': df_overview,
            'historical_metrics': df_historical
        }

        logging.info(f"Export report generated successfully at {timestamp}")
        return export_data

    except Exception as e:
        logging.error(f"Error generating export report: {e}")
        return None


def export_to_csv(export_data):
    """
    Export data to CSV files

    Args:
        export_data: Dictionary containing DataFrames and metadata

    Returns:
        List of file paths created
    """
    try:
        timestamp = export_data.get('timestamp', datetime.now().strftime('%Y%m%d_%H%M%S'))
        file_paths = []

        # Export server metrics
        if not export_data['server_metrics'].empty:
            filepath = f"/tmp/server_metrics_{timestamp}.csv"
            export_data['server_metrics'].to_csv(filepath, index=False)
            file_paths.append(filepath)
            logging.info(f"Exported server metrics to {filepath}")

        # Export top users
        if not export_data['top_users'].empty:
            filepath = f"/tmp/top_users_{timestamp}.csv"
            export_data['top_users'].to_csv(filepath, index=False)
            file_paths.append(filepath)
            logging.info(f"Exported top users to {filepath}")

        # Export system overview
        if not export_data['system_overview'].empty:
            filepath = f"/tmp/system_overview_{timestamp}.csv"
            export_data['system_overview'].to_csv(filepath, index=False)
            file_paths.append(filepath)
            logging.info(f"Exported system overview to {filepath}")

        # Export historical metrics
        if not export_data['historical_metrics'].empty:
            filepath = f"/tmp/historical_metrics_{timestamp}.csv"
            export_data['historical_metrics'].to_csv(filepath, index=False)
            file_paths.append(filepath)
            logging.info(f"Exported historical metrics to {filepath}")

        return file_paths

    except Exception as e:
        logging.error(f"Error exporting to CSV: {e}")
        return []


def export_to_excel(export_data):
    """
    Export data to a single Excel file with multiple sheets

    Args:
        export_data: Dictionary containing DataFrames and metadata

    Returns:
        File path of created Excel file or None if failed
    """
    try:
        timestamp = export_data.get('timestamp', datetime.now().strftime('%Y%m%d_%H%M%S'))
        filepath = f"/tmp/dashboard_report_{timestamp}.xlsx"

        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            if not export_data['server_metrics'].empty:
                export_data['server_metrics'].to_excel(writer, sheet_name='Server Metrics', index=False)

            if not export_data['top_users'].empty:
                export_data['top_users'].to_excel(writer, sheet_name='Top Users', index=False)

            if not export_data['system_overview'].empty:
                export_data['system_overview'].to_excel(writer, sheet_name='System Overview', index=False)

            if not export_data['historical_metrics'].empty:
                export_data['historical_metrics'].to_excel(writer, sheet_name='Historical Data', index=False)

        logging.info(f"Exported data to Excel file: {filepath}")
        return filepath

    except Exception as e:
        logging.error(f"Error exporting to Excel: {e}")
        return None


def export_to_json(export_data):
    """
    Export data to JSON files

    Args:
        export_data: Dictionary containing DataFrames and metadata

    Returns:
        List of file paths created
    """
    try:
        timestamp = export_data.get('timestamp', datetime.now().strftime('%Y%m%d_%H%M%S'))
        file_paths = []

        # Export server metrics
        if not export_data['server_metrics'].empty:
            filepath = f"/tmp/server_metrics_{timestamp}.json"
            export_data['server_metrics'].to_json(filepath, orient='records', indent=2)
            file_paths.append(filepath)
            logging.info(f"Exported server metrics to {filepath}")

        # Export top users
        if not export_data['top_users'].empty:
            filepath = f"/tmp/top_users_{timestamp}.json"
            export_data['top_users'].to_json(filepath, orient='records', indent=2)
            file_paths.append(filepath)
            logging.info(f"Exported top users to {filepath}")

        # Export system overview
        if not export_data['system_overview'].empty:
            filepath = f"/tmp/system_overview_{timestamp}.json"
            export_data['system_overview'].to_json(filepath, orient='records', indent=2)
            file_paths.append(filepath)
            logging.info(f"Exported system overview to {filepath}")

        # Export historical metrics
        if not export_data['historical_metrics'].empty:
            filepath = f"/tmp/historical_metrics_{timestamp}.json"
            export_data['historical_metrics'].to_json(filepath, orient='records', indent=2)
            file_paths.append(filepath)
            logging.info(f"Exported historical metrics to {filepath}")

        return file_paths

    except Exception as e:
        logging.error(f"Error exporting to JSON: {e}")
        return []


def create_export_summary(export_data):
    """
    Create a summary of the exported data

    Args:
        export_data: Dictionary containing DataFrames and metadata

    Returns:
        Dictionary with summary statistics
    """
    try:
        summary = {
            'timestamp': export_data.get('timestamp'),
            'server_count': len(export_data['server_metrics']) if not export_data['server_metrics'].empty else 0,
            'user_count': len(export_data['top_users']) if not export_data['top_users'].empty else 0,
            'historical_records': len(export_data['historical_metrics']) if not export_data['historical_metrics'].empty else 0
        }
        return summary
    except Exception as e:
        logging.error(f"Error creating export summary: {e}")
        return {}
