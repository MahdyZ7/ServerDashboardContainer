#!/usr/bin/env python3
"""
Generate SQL migration scripts from schema definition.
"""

from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime


def generate_create_table(table_name: str, fields: List[Dict[str, Any]]) -> str:
    """Generate CREATE TABLE statement."""
    lines = [f"CREATE TABLE IF NOT EXISTS {table_name} ("]

    field_defs = []
    for field in fields:
        parts = [f"    {field['name']}"]

        # Type
        sql_type = field["type"].upper()
        parts.append(sql_type)

        # Constraints
        if field.get("primary_key"):
            parts.append("PRIMARY KEY")
        if not field.get("nullable", True):
            parts.append("NOT NULL")
        if "default" in field:
            default = field["default"]
            if default == "CURRENT_TIMESTAMP":
                parts.append("DEFAULT CURRENT_TIMESTAMP")
            else:
                parts.append(f"DEFAULT '{default}'")

        field_defs.append(" ".join(parts))

    lines.append(",\n".join(field_defs))
    lines.append(");")

    return "\n".join(lines)


def generate_indexes(table_name: str, fields: List[Dict[str, Any]]) -> str:
    """Generate CREATE INDEX statements for fields that should be indexed."""
    indexes = []

    # Common fields to index
    index_fields = ["server_name", "timestamp"]

    # Index fields with thresholds (for quick filtering)
    for field in fields:
        if "visualization" in field and "thresholds" in field["visualization"]:
            if field["name"] not in index_fields:
                index_fields.append(field["name"])

    for field_name in index_fields:
        if any(f["name"] == field_name for f in fields):
            index_name = f"idx_{table_name}_{field_name}"
            indexes.append(
                f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name}({field_name});"
            )

    return "\n".join(indexes)


def generate_sql_migration(schema: Dict[str, Any]) -> str:
    """Generate complete SQL migration script."""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create migrations directory relative to this script
    migrations_dir = (
        Path(__file__).parent.parent.parent / "srcs" / "Backend" / "migrations"
    )
    migrations_dir.mkdir(parents=True, exist_ok=True)

    output_file = migrations_dir / f"{timestamp}_schema_migration.sql"

    sql_parts = []

    # Header
    sql_parts.append(f"""-- Generated SQL Migration
-- Schema Version: {schema["version"]}
-- Generated At: {schema["generated_at"]}
-- DO NOT EDIT MANUALLY - This file is auto-generated from schema/metrics_schema.yaml

BEGIN;

""")

    # Generate server_metrics table
    if "server_metrics" in schema:
        sql_parts.append("-- Server Metrics Table")
        sql_parts.append(
            generate_create_table(
                schema["server_metrics"]["table_name"],
                schema["server_metrics"]["fields"],
            )
        )
        sql_parts.append("\n")
        sql_parts.append(
            generate_indexes(
                schema["server_metrics"]["table_name"],
                schema["server_metrics"]["fields"],
            )
        )
        sql_parts.append("\n\n")

    # Generate top_users table
    if "top_users" in schema:
        sql_parts.append("-- Top Users Table")
        sql_parts.append(
            generate_create_table(
                schema["top_users"]["table_name"], schema["top_users"]["fields"]
            )
        )
        sql_parts.append("\n")
        sql_parts.append(
            generate_indexes(
                schema["top_users"]["table_name"], schema["top_users"]["fields"]
            )
        )
        sql_parts.append("\n\n")

    sql_parts.append("COMMIT;\n")

    # Write to file
    sql_content = "".join(sql_parts)
    with open(output_file, "w") as f:
        f.write(sql_content)

    return str(output_file)


if __name__ == "__main__":
    # Test
    import yaml

    with open("../metrics_schema.yaml") as f:
        schema = yaml.safe_load(f)

    schema["generated_at"] = datetime.now().isoformat()
    output = generate_sql_migration(schema)
    print(f"Generated: {output}")
