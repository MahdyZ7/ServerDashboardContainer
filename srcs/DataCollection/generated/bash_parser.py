# Generated Bash Output Parser
# Schema Version: 1.0.0
# Generated At: 2025-11-05T00:11:46.315719
# DO NOT EDIT MANUALLY

from typing import Dict, Optional, List


def parse_server_metrics(bash_output: str) -> dict:
    """
    Parse mini_monitering.sh output (--line-format).
    Auto-generated from schema definition.
    """
    parts = bash_output.strip().split(',')

    result = {}

    result['architecture'] = parts[0].strip() if len(parts) > 0 else None
    result['os'] = parts[1].strip() if len(parts) > 1 else None
    result['physical_cpus'] = parts[2].strip() if len(parts) > 2 else None
    result['virtual_cpus'] = parts[3].strip() if len(parts) > 3 else None
    if len(parts) > 4:
        result['ram_used'] = parts[4].split('/')[0].strip() if '/' in parts[4] else parts[4].strip()
    if len(parts) > 4:
        result['ram_total'] = parts[4].split('/')[1].strip() if '/' in parts[4] else parts[4].strip()
    result['ram_percentage'] = parts[5].strip() if len(parts) > 5 else None
    if len(parts) > 6:
        result['disk_used'] = parts[6].split('/')[0].strip() if '/' in parts[6] else parts[6].strip()
    if len(parts) > 6:
        result['disk_total'] = parts[6].split('/')[1].strip() if '/' in parts[6] else parts[6].strip()
    if len(parts) > 7:
        result['disk_percentage'] = parts[7].rstrip('%').strip()
    if len(parts) > 8:
        csv_parts = parts[8].split(',')
        result['cpu_load_1min'] = csv_parts[0].strip() if len(csv_parts) > 0 else None
    if len(parts) > 8:
        csv_parts = parts[8].split(',')
        result['cpu_load_5min'] = csv_parts[1].strip() if len(csv_parts) > 1 else None
    if len(parts) > 8:
        csv_parts = parts[8].split(',')
        result['cpu_load_15min'] = csv_parts[2].strip() if len(csv_parts) > 2 else None
    result['last_boot'] = parts[9].strip() if len(parts) > 9 else None
    result['tcp_connections'] = parts[10].strip() if len(parts) > 10 else None
    result['logged_users'] = parts[11].strip() if len(parts) > 11 else None
    result['active_vnc'] = parts[12].strip() if len(parts) > 12 else None
    result['active_ssh'] = parts[13].strip() if len(parts) > 13 else None

    return result

def parse_top_users_line(bash_line: str) -> dict:
    """
    Parse single line from TopUsers.sh output.
    Auto-generated from schema definition.
    """
    parts = bash_line.strip().split()

    if not parts:
        return {}

    result = {}

    result['username'] = parts[0].strip() if len(parts) > 0 else None
    result['cpu_percentage'] = parts[1].strip() if len(parts) > 1 else None
    result['memory_percentage'] = parts[2].strip() if len(parts) > 2 else None
    result['disk_usage_gb'] = parts[3].strip() if len(parts) > 3 else None
    result['process_count'] = parts[4].strip() if len(parts) > 4 else None
    result['top_process'] = parts[5].strip() if len(parts) > 5 else None
    result['last_login'] = parts[6].strip() if len(parts) > 6 else None
    result['full_name'] = parts[7].strip() if len(parts) > 7 else None

    return result

def parse_top_users(bash_output: str) -> list:
    """Parse complete TopUsers.sh output."""
    lines = [line for line in bash_output.split('\n') if line.strip()]

    # Skip header lines (first 2 lines with "USERNAME" and "----")
    data_lines = []
    for i, line in enumerate(lines):
        if i < 2:  # Skip first two lines (headers)
            continue
        if '----' in line:  # Skip separator lines
            continue
        data_lines.append(line)

    return [parse_top_users_line(line) for line in data_lines if line.strip()]

