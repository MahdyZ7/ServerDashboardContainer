-- Generated SQL Migration
-- Schema Version: 1.0.0
-- Generated At: 2025-11-05T00:11:46.315719
-- DO NOT EDIT MANUALLY - This file is auto-generated from schema/metrics_schema.yaml

BEGIN;

-- Server Metrics TableCREATE TABLE IF NOT EXISTS server_metrics (
    id SERIAL PRIMARY KEY NOT NULL,
    server_name VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    architecture VARCHAR(255),
    os VARCHAR(100),
    physical_cpus INTEGER,
    virtual_cpus INTEGER,
    ram_used VARCHAR(20),
    ram_total VARCHAR(20),
    ram_percentage INTEGER,
    disk_used VARCHAR(20),
    disk_total VARCHAR(20),
    disk_percentage VARCHAR(10),
    cpu_load_1min VARCHAR(10),
    cpu_load_5min VARCHAR(10),
    cpu_load_15min VARCHAR(10),
    last_boot VARCHAR(50),
    tcp_connections INTEGER,
    logged_users INTEGER,
    active_vnc INTEGER,
    active_ssh INTEGER
);
CREATE INDEX IF NOT EXISTS idx_server_metrics_server_name ON server_metrics(server_name);
CREATE INDEX IF NOT EXISTS idx_server_metrics_timestamp ON server_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_server_metrics_ram_percentage ON server_metrics(ram_percentage);
CREATE INDEX IF NOT EXISTS idx_server_metrics_disk_percentage ON server_metrics(disk_percentage);

-- Top Users TableCREATE TABLE IF NOT EXISTS top_users (
    id SERIAL PRIMARY KEY NOT NULL,
    server_name VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    username VARCHAR(50) NOT NULL,
    cpu_percentage DECIMAL(5,2),
    memory_percentage DECIMAL(5,2),
    disk_usage_gb DECIMAL(10,2),
    process_count INTEGER,
    top_process VARCHAR(255),
    last_login VARCHAR(50),
    full_name VARCHAR(255)
);
CREATE INDEX IF NOT EXISTS idx_top_users_server_name ON top_users(server_name);
CREATE INDEX IF NOT EXISTS idx_top_users_timestamp ON top_users(timestamp);

COMMIT;
