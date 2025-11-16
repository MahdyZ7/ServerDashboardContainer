# Generated Python Model
# Schema Version: 1.0.0
# Generated At: 2025-11-05T00:11:46.315719
# DO NOT EDIT MANUALLY

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class ServerMetrics:
    """ServerMetrics data model (auto-generated from schema)."""

    # Primary key
    id: int
    # Server identifier
    server_name: str
    # Collection timestamp
    timestamp: datetime
    # System architecture (kernel, release, machine)
    architecture: Optional[str] = None
    # Operating system name and version
    os: Optional[str] = None
    # Number of physical CPU sockets
    physical_cpus: Optional[int] = None
    # Number of virtual CPU cores (threads)
    virtual_cpus: Optional[int] = None
    # RAM currently in use
    ram_used: Optional[str] = None
    # Total RAM available
    ram_total: Optional[str] = None
    # RAM usage percentage
    ram_percentage: Optional[int] = None
    # Disk space used
    disk_used: Optional[str] = None
    # Total disk space
    disk_total: Optional[str] = None
    # Disk usage percentage
    disk_percentage: Optional[str] = None
    # CPU load average (1 minute)
    cpu_load_1min: Optional[str] = None
    # CPU load average (5 minutes)
    cpu_load_5min: Optional[str] = None
    # CPU load average (15 minutes)
    cpu_load_15min: Optional[str] = None
    # Last system boot time
    last_boot: Optional[str] = None
    # Number of TCP connections
    tcp_connections: Optional[int] = None
    # Number of logged-in users
    logged_users: Optional[int] = None
    # Active VNC sessions
    active_vnc: Optional[int] = None
    # Active SSH sessions
    active_ssh: Optional[int] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            k: v.isoformat() if isinstance(v, datetime) else v
            for k, v in self.__dict__.items()
        }

    @classmethod
    def from_dict(cls, data: dict):
        """Create instance from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})
