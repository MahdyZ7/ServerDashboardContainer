# Generated Python Model
# Schema Version: 1.0.0
# Generated At: 2025-11-05T00:11:46.315719
# DO NOT EDIT MANUALLY

from dataclasses import dataclass, field
from typing import Optional, Any
from datetime import datetime


@dataclass
class TopUsers:
    """TopUsers data model (auto-generated from schema)."""

    # Primary key
    id: int
    # Server identifier
    server_name: str
    # Collection timestamp
    timestamp: datetime
    # Username
    username: str
    # CPU usage percentage
    cpu_percentage: Optional[float] = None
    # Memory usage percentage
    memory_percentage: Optional[float] = None
    # Disk usage in GB
    disk_usage_gb: Optional[float] = None
    # Number of processes
    process_count: Optional[int] = None
    # Top CPU-consuming process
    top_process: Optional[str] = None
    # Last login timestamp
    last_login: Optional[str] = None
    # User's full name
    full_name: Optional[str] = None

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
