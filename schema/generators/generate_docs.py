#!/usr/bin/env python3
"""
Generate comprehensive documentation from schema definition.
Creates markdown files for database schema, API endpoints, and field reference.
"""

from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime


def generate_database_schema_docs(schema: Dict[str, Any]) -> str:
    """Generate database schema documentation."""

    lines = [
        "# Database Schema Documentation",
        "",
        f"**Schema Version:** {schema['version']}  ",
        f"**Generated:** {schema['generated_at']}  ",
        "",
        "This documentation is auto-generated from `schema/metrics_schema.yaml`.",
        "",
        "---",
        "",
    ]

    # Server Metrics Table
    if "server_metrics" in schema:
        table = schema["server_metrics"]
        lines.extend(
            [
                f"## Table: `{table['table_name']}`",
                "",
                table.get("description", "Server monitoring metrics"),
                "",
                "### Columns",
                "",
                "| Column | Type | Nullable | Description |",
                "|--------|------|----------|-------------|",
            ]
        )

        for field in table["fields"]:
            name = field["name"]
            ftype = field["type"]
            nullable = "Yes" if field.get("nullable", True) else "No"
            desc = field.get("description", "-")

            lines.append(f"| `{name}` | {ftype} | {nullable} | {desc} |")

        lines.append("")

    # Top Users Table
    if "top_users" in schema:
        table = schema["top_users"]
        lines.extend(
            [
                "---",
                "",
                f"## Table: `{table['table_name']}`",
                "",
                table.get("description", "Per-user resource usage metrics"),
                "",
                "### Columns",
                "",
                "| Column | Type | Nullable | Description |",
                "|--------|------|----------|-------------|",
            ]
        )

        for field in table["fields"]:
            name = field["name"]
            ftype = field["type"]
            nullable = "Yes" if field.get("nullable", True) else "No"
            desc = field.get("description", "-")

            lines.append(f"| `{name}` | {ftype} | {nullable} | {desc} |")

        lines.append("")

    return "\n".join(lines)


def generate_api_docs(schema: Dict[str, Any]) -> str:
    """Generate API endpoint documentation."""

    lines = [
        "# API Documentation",
        "",
        f"**Schema Version:** {schema['version']}  ",
        f"**Generated:** {schema['generated_at']}  ",
        "",
        "This documentation is auto-generated from `schema/metrics_schema.yaml`.",
        "",
        "---",
        "",
        "## Base URL",
        "",
        "```",
        "http://localhost:5000",
        "```",
        "",
        "## Endpoints",
        "",
    ]

    if "api_endpoints" in schema:
        for endpoint in schema["api_endpoints"]:
            path = endpoint["path"]
            method = endpoint["method"]
            description = endpoint.get("description", "")

            lines.extend([f"### `{method} {path}`", "", description, "", "---", ""])

    return "\n".join(lines)


def generate_quick_reference(schema: Dict[str, Any]) -> str:
    """Generate quick reference guide."""

    return f"""# Quick Reference Guide

**Schema Version:** {schema["version"]}
**Generated:** {schema["generated_at"]}

## Adding a New Metric

1. Edit `schema/metrics_schema.yaml`
2. Run `python schema/generators/generate_all.py`
3. Apply migration: `docker exec -i postgres psql -U postgres server_db < srcs/Backend/migrations/LATEST.sql`
4. Restart services: `make restart`

## Field Format Options

- `raw` - Use value as-is
- `part_before_slash` - Extract before `/` (e.g., "2.5G/16G" → "2.5G")
- `part_after_slash` - Extract after `/` (e.g., "2.5G/16G" → "16G")
- `csv_split_0` - First part of comma-separated (e.g., "1,2,3" → "1")
- `strip_percent` - Remove `%` sign (e.g., "45%" → "45")

## Validation Types

- `percentage` - Float 0-100
- `integer` - Whole number (supports min/max)
- `float` - Decimal number (supports min/max)
- `string` - Text (supports max_length)

## Generated Files

- `srcs/Backend/migrations/*.sql` - Database migrations
- `srcs/Backend/generated/models/*.py` - Python dataclasses
- `srcs/DataCollection/generated/bash_parser.py` - Bash parsers
- `srcs/Frontend/generated/validators.py` - Validators
- `srcs/Frontend/generated/types.ts` - TypeScript types
- `docs/generated/*.md` - Documentation
"""


def generate_documentation(schema: Dict[str, Any]) -> List[str]:
    """Generate all documentation files."""

    # Base path relative to this script
    base_path = Path(__file__).parent.parent.parent / "Docs" / "generated"
    base_path.mkdir(parents=True, exist_ok=True)

    output_files = []

    # Database schema docs
    db_docs_file = base_path / "DATABASE_SCHEMA.md"
    with open(db_docs_file, "w") as f:
        f.write(generate_database_schema_docs(schema))
    output_files.append(str(db_docs_file))

    # API docs
    api_docs_file = base_path / "API_DOCUMENTATION.md"
    with open(api_docs_file, "w") as f:
        f.write(generate_api_docs(schema))
    output_files.append(str(api_docs_file))

    # Quick reference
    quick_ref_file = base_path / "QUICK_REFERENCE.md"
    with open(quick_ref_file, "w") as f:
        f.write(generate_quick_reference(schema))
    output_files.append(str(quick_ref_file))

    return output_files


if __name__ == "__main__":
    # Test
    import yaml

    with open("../metrics_schema.yaml") as f:
        schema = yaml.safe_load(f)

    schema["generated_at"] = datetime.now().isoformat()
    outputs = generate_documentation(schema)
    print(f"Generated {len(outputs)} files:")
    for output in outputs:
        print(f"  - {output}")
