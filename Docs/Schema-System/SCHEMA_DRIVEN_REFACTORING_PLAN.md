# Schema-Driven Architecture Refactoring Plan

## Executive Summary

**Current Problem:** Adding 1 new metric requires changes in 10+ places across the codebase
**Proposed Solution:** Single source of truth (schema definition) with automatic code generation
**Estimated Effort:** 5-7 days
**Risk Level:** Medium (requires careful migration)
**Impact:** Future changes reduced from 10+ places to 1-2 places

---

## Current Architecture Problems

### Problem 1: Scattered Schema Definitions
Schema is defined in **7 different places**:
1. `mini_monitering.sh` - Bash output format (lines 45-60)
2. `backend.py` - Column parsing logic (lines 25-145)
3. `backend.py` - SQL CREATE TABLE (lines 147-180)
4. `api.py` - SQL SELECT queries (lines 50-200)
5. `validation.py` - Field ranges (lines 10-50)
6. `data_processing.py` - Column lists (lines 15-80)
7. Frontend components - Hardcoded field names throughout

### Problem 2: Manual Synchronization
No automated way to ensure all layers stay in sync with schema changes.

### Problem 3: No Type Safety
Python code lacks type hints, JavaScript has no TypeScript definitions.

### Problem 4: Fragile Parsing
Bash output parsed with brittle regex and hardcoded indices.

---

## Proposed Architecture: Schema-Driven Design

### Core Concept
Define the entire data model in **ONE central schema file**, then generate:
- Database migrations
- API models
- Frontend types
- Parsing logic
- Validation rules
- Documentation

### Architecture Diagram
```
┌─────────────────────────────────────────────────────────────┐
│                    schema.yaml (SINGLE SOURCE OF TRUTH)      │
│  - Field definitions                                         │
│  - Data types                                                │
│  - Validation rules                                          │
│  - Display metadata                                          │
└───────────────┬─────────────────────────────────────────────┘
                │
                ├──────────────────────────────────────────────┐
                │                                              │
    ┌───────────▼──────────┐                    ┌─────────────▼──────────┐
    │  Code Generators     │                    │  Runtime Libraries     │
    │  (Build Time)        │                    │  (Imported by apps)    │
    ├──────────────────────┤                    ├────────────────────────┤
    │ • SQL migrations     │                    │ • Validators           │
    │ • Python dataclasses │                    │ • Type checkers        │
    │ • API schemas        │                    │ • Parsers              │
    │ • TypeScript types   │                    │ • Formatters           │
    │ • Documentation      │                    └────────────────────────┘
    └──────────────────────┘
                │
    ┌───────────┼────────────────────────────────┐
    │           │                                │
┌───▼───┐  ┌───▼───┐  ┌────▼────┐  ┌──────▼─────┐
│ Bash  │  │  DB   │  │   API   │  │  Frontend  │
│Scripts│  │Schema │  │ Models  │  │   Types    │
└───────┘  └───────┘  └─────────┘  └────────────┘
```

---

## Implementation Plan

### Phase 1: Create Schema Definition System (Days 1-2)

#### Step 1.1: Create Central Schema File

**File:** `schema/metrics_schema.yaml`

```yaml
# Server Metrics Schema Definition
# This is the SINGLE SOURCE OF TRUTH for all data structures

version: "1.0.0"
generated_at: "auto"  # Timestamp added during generation

# Metric Groups
metric_groups:
  - id: system_info
    name: System Information
    order: 1

  - id: resources
    name: Resource Usage
    order: 2

  - id: storage
    name: Storage
    order: 3

  - id: network
    name: Network & Security
    order: 4

  - id: users
    name: User Activity
    order: 5

# Server Metrics Table Definition
server_metrics:
  table_name: server_metrics
  primary_key: id

  fields:
    # System Information
    - name: id
      type: serial
      primary_key: true
      nullable: false
      bash_output: false  # Not from bash script

    - name: server_name
      type: varchar(255)
      nullable: false
      bash_output: false
      group: system_info
      description: "Server identifier"
      frontend_display: "Server"

    - name: timestamp
      type: timestamp
      nullable: false
      default: CURRENT_TIMESTAMP
      bash_output: false
      group: system_info

    - name: architecture
      type: varchar(255)
      nullable: true
      bash_output: true
      bash_index: 0  # Position in CSV output
      group: system_info
      description: "System architecture (kernel, release, machine)"
      frontend_display: "Architecture"
      validation:
        type: string
        max_length: 255

    - name: os
      type: varchar(100)
      nullable: true
      bash_output: true
      bash_index: 1
      group: system_info
      description: "Operating system name and version"
      frontend_display: "OS"

    # CPU Information
    - name: physical_cpus
      type: integer
      nullable: true
      bash_output: true
      bash_index: 2
      group: resources
      description: "Number of physical CPU sockets"
      frontend_display: "Physical CPUs"
      validation:
        type: integer
        min: 0
        max: 256

    - name: virtual_cpus
      type: integer
      nullable: true
      bash_output: true
      bash_index: 3
      group: resources
      description: "Number of virtual CPU cores (threads)"
      frontend_display: "Virtual CPUs"
      validation:
        type: integer
        min: 0
        max: 1024

    # Memory
    - name: ram_used
      type: varchar(20)
      nullable: true
      bash_output: true
      bash_index: 4
      bash_format: "part_before_slash"  # "2.5G/16G" -> "2.5G"
      group: resources
      description: "RAM currently in use"
      frontend_display: "RAM Used"
      validation:
        type: memory_size
        unit: GB

    - name: ram_total
      type: varchar(20)
      nullable: true
      bash_output: true
      bash_index: 4
      bash_format: "part_after_slash"  # "2.5G/16G" -> "16G"
      group: resources
      description: "Total RAM available"
      frontend_display: "RAM Total"

    - name: ram_percentage
      type: integer
      nullable: true
      bash_output: true
      bash_index: 5
      group: resources
      description: "RAM usage percentage"
      frontend_display: "RAM %"
      visualization:
        type: progress_bar
        thresholds:
          warning: 70
          critical: 85
      validation:
        type: percentage
        min: 0
        max: 100

    # Disk Storage
    - name: disk_used
      type: varchar(20)
      nullable: true
      bash_output: true
      bash_index: 6
      bash_format: "part_before_slash"
      group: storage
      description: "Disk space used"
      frontend_display: "Disk Used"

    - name: disk_total
      type: varchar(20)
      nullable: true
      bash_output: true
      bash_index: 6
      bash_format: "part_after_slash"
      group: storage
      description: "Total disk space"
      frontend_display: "Disk Total"

    - name: disk_percentage
      type: varchar(10)
      nullable: true
      bash_output: true
      bash_index: 7
      bash_format: "strip_percent"  # "45%" -> 45
      group: storage
      description: "Disk usage percentage"
      frontend_display: "Disk %"
      visualization:
        type: progress_bar
        thresholds:
          warning: 80
          critical: 90
      validation:
        type: percentage

    # CPU Load
    - name: cpu_load_1min
      type: varchar(10)
      nullable: true
      bash_output: true
      bash_index: 8
      bash_format: "csv_split_0"  # "0.5,0.7,0.9" -> "0.5"
      group: resources
      description: "CPU load average (1 minute)"
      frontend_display: "Load (1m)"
      validation:
        type: float
        min: 0

    - name: cpu_load_5min
      type: varchar(10)
      nullable: true
      bash_output: true
      bash_index: 8
      bash_format: "csv_split_1"
      group: resources
      description: "CPU load average (5 minutes)"
      frontend_display: "Load (5m)"

    - name: cpu_load_15min
      type: varchar(10)
      nullable: true
      bash_output: true
      bash_index: 8
      bash_format: "csv_split_2"
      group: resources
      description: "CPU load average (15 minutes)"
      frontend_display: "Load (15m)"

    # System Status
    - name: last_boot
      type: varchar(50)
      nullable: true
      bash_output: true
      bash_index: 9
      group: system_info
      description: "Last system boot time"
      frontend_display: "Last Boot"
      validation:
        type: datetime

    - name: tcp_connections
      type: integer
      nullable: true
      bash_output: true
      bash_index: 10
      group: network
      description: "Number of TCP connections"
      frontend_display: "TCP Connections"
      validation:
        type: integer
        min: 0

    - name: logged_users
      type: integer
      nullable: true
      bash_output: true
      bash_index: 11
      group: users
      description: "Number of logged-in users"
      frontend_display: "Logged Users"
      validation:
        type: integer
        min: 0

    - name: active_vnc
      type: integer
      nullable: true
      bash_output: true
      bash_index: 12
      group: network
      description: "Active VNC sessions"
      frontend_display: "VNC Sessions"
      validation:
        type: integer
        min: 0

    - name: active_ssh
      type: integer
      nullable: true
      bash_output: true
      bash_index: 13
      group: network
      description: "Active SSH sessions"
      frontend_display: "SSH Sessions"
      validation:
        type: integer
        min: 0

# Top Users Table Definition
top_users:
  table_name: top_users
  primary_key: id

  fields:
    - name: id
      type: serial
      primary_key: true
      nullable: false

    - name: server_name
      type: varchar(255)
      nullable: false

    - name: timestamp
      type: timestamp
      nullable: false
      default: CURRENT_TIMESTAMP

    - name: username
      type: varchar(50)
      nullable: false
      bash_output: true
      bash_index: 0
      description: "Username"
      frontend_display: "User"

    - name: cpu_percentage
      type: decimal(5,2)
      nullable: true
      bash_output: true
      bash_index: 1
      description: "CPU usage percentage"
      frontend_display: "CPU %"
      validation:
        type: percentage

    - name: memory_percentage
      type: decimal(5,2)
      nullable: true
      bash_output: true
      bash_index: 2
      description: "Memory usage percentage"
      frontend_display: "Memory %"
      validation:
        type: percentage

    - name: disk_usage_gb
      type: decimal(10,2)
      nullable: true
      bash_output: true
      bash_index: 3
      description: "Disk usage in GB"
      frontend_display: "Disk (GB)"
      validation:
        type: float
        min: 0

    - name: process_count
      type: integer
      nullable: true
      bash_output: true
      bash_index: 4
      description: "Number of processes"
      frontend_display: "Processes"
      validation:
        type: integer
        min: 0

    - name: top_process
      type: varchar(255)
      nullable: true
      bash_output: true
      bash_index: 5
      description: "Top CPU-consuming process"
      frontend_display: "Top Process"

    - name: last_login
      type: varchar(50)
      nullable: true
      bash_output: true
      bash_index: 6
      description: "Last login timestamp"
      frontend_display: "Last Login"

    - name: full_name
      type: varchar(255)
      nullable: true
      bash_output: true
      bash_index: 7
      description: "User's full name"
      frontend_display: "Full Name"

# API Endpoints Configuration
api_endpoints:
  - path: /api/servers/metrics/latest
    method: GET
    description: "Get latest metrics for all servers"
    returns: server_metrics
    fields: all

  - path: /api/servers/<server_name>/metrics/historical/<hours>
    method: GET
    description: "Get historical metrics for specific server"
    returns: server_metrics
    fields: all
    parameters:
      - name: server_name
        type: string
        required: true
      - name: hours
        type: integer
        required: true
        validation:
          min: 1
          max: 720  # 30 days

  - path: /api/users/top
    method: GET
    description: "Get top users across all servers"
    returns: top_users
    fields: all

# Display Configuration for Frontend
frontend_config:
  server_metrics:
    overview_cards:
      - field: ram_percentage
        title: "Memory Usage"
        color_scheme: "blue"
      - field: disk_percentage
        title: "Disk Usage"
        color_scheme: "green"
      - field: cpu_load_1min
        title: "CPU Load"
        color_scheme: "orange"

    graphs:
      - name: "Resource Usage Over Time"
        fields: [ram_percentage, disk_percentage]
        type: line

      - name: "CPU Load Average"
        fields: [cpu_load_1min, cpu_load_5min, cpu_load_15min]
        type: line

  top_users:
    table_columns: [username, cpu_percentage, memory_percentage, disk_usage_gb, process_count, top_process]
    sortable: true
    default_sort: cpu_percentage
    default_order: desc

# New Metric Template (for future additions)
# Copy this template when adding new metrics
new_metric_template:
  - name: new_metric_name
    type: varchar(50)  # or integer, decimal, etc.
    nullable: true
    bash_output: true
    bash_index: 14  # Next available index
    bash_format: "raw"  # or "part_before_slash", "csv_split_0", etc.
    group: resources  # or system_info, storage, network, users
    description: "Description of what this metric measures"
    frontend_display: "Display Name"
    validation:
      type: integer  # or percentage, float, string, datetime, memory_size
      min: 0
      max: 100
    visualization:  # optional
      type: progress_bar  # or line_chart, bar_chart, badge
      thresholds:  # optional
        warning: 70
        critical: 85
```

#### Step 1.2: Create Schema Generator Scripts

**File:** `schema/generators/generate_all.py`

```python
#!/usr/bin/env python3
"""
Master script to generate all code from schema definition.
Run this whenever schema.yaml changes.

Usage:
    python generate_all.py
    python generate_all.py --validate-only
    python generate_all.py --target sql,python
"""

import yaml
import sys
from pathlib import Path
from typing import Dict, Any, List
import argparse
from datetime import datetime

# Import individual generators
from generate_sql import generate_sql_migration
from generate_python import generate_python_models
from generate_typescript import generate_typescript_types
from generate_validators import generate_validators
from generate_parsers import generate_parsers
from generate_docs import generate_documentation

class SchemaGenerator:
    def __init__(self, schema_path: str):
        self.schema_path = Path(schema_path)
        self.schema = self.load_schema()
        self.generated_files = []

    def load_schema(self) -> Dict[str, Any]:
        """Load and validate schema YAML file."""
        try:
            with open(self.schema_path, 'r') as f:
                schema = yaml.safe_load(f)

            # Add generation timestamp
            schema['generated_at'] = datetime.now().isoformat()

            return schema
        except Exception as e:
            print(f"❌ Error loading schema: {e}")
            sys.exit(1)

    def validate_schema(self) -> bool:
        """Validate schema structure and consistency."""
        print("🔍 Validating schema...")

        errors = []

        # Check required top-level keys
        required_keys = ['version', 'server_metrics', 'top_users']
        for key in required_keys:
            if key not in self.schema:
                errors.append(f"Missing required key: {key}")

        # Validate server_metrics fields
        if 'server_metrics' in self.schema:
            fields = self.schema['server_metrics'].get('fields', [])
            bash_indices = []

            for field in fields:
                # Check required field properties
                if 'name' not in field:
                    errors.append(f"Field missing 'name' property: {field}")
                    continue

                if 'type' not in field:
                    errors.append(f"Field '{field['name']}' missing 'type' property")

                # Check for duplicate bash_index
                if field.get('bash_output') and 'bash_index' in field:
                    idx = field['bash_index']
                    if idx in bash_indices:
                        errors.append(f"Duplicate bash_index {idx} for field '{field['name']}'")
                    bash_indices.append(idx)

        # Validate top_users fields
        if 'top_users' in self.schema:
            fields = self.schema['top_users'].get('fields', [])
            for field in fields:
                if 'name' not in field or 'type' not in field:
                    errors.append(f"Invalid field in top_users: {field}")

        if errors:
            print("❌ Schema validation failed:")
            for error in errors:
                print(f"   - {error}")
            return False

        print("✅ Schema validation passed")
        return True

    def generate_all(self, targets: List[str] = None) -> bool:
        """Generate all code from schema."""
        if targets is None:
            targets = ['sql', 'python', 'typescript', 'validators', 'parsers', 'docs']

        success = True

        print(f"\n🚀 Generating code from schema (version {self.schema['version']})...\n")

        if 'sql' in targets:
            print("📊 Generating SQL migration...")
            try:
                sql_file = generate_sql_migration(self.schema)
                self.generated_files.append(sql_file)
                print(f"   ✅ Generated: {sql_file}")
            except Exception as e:
                print(f"   ❌ Failed: {e}")
                success = False

        if 'python' in targets:
            print("🐍 Generating Python models...")
            try:
                py_files = generate_python_models(self.schema)
                self.generated_files.extend(py_files)
                print(f"   ✅ Generated {len(py_files)} files")
            except Exception as e:
                print(f"   ❌ Failed: {e}")
                success = False

        if 'typescript' in targets:
            print("📘 Generating TypeScript types...")
            try:
                ts_files = generate_typescript_types(self.schema)
                self.generated_files.extend(ts_files)
                print(f"   ✅ Generated {len(ts_files)} files")
            except Exception as e:
                print(f"   ❌ Failed: {e}")
                success = False

        if 'validators' in targets:
            print("✔️  Generating validators...")
            try:
                validator_files = generate_validators(self.schema)
                self.generated_files.extend(validator_files)
                print(f"   ✅ Generated {len(validator_files)} files")
            except Exception as e:
                print(f"   ❌ Failed: {e}")
                success = False

        if 'parsers' in targets:
            print("🔧 Generating parsers...")
            try:
                parser_files = generate_parsers(self.schema)
                self.generated_files.extend(parser_files)
                print(f"   ✅ Generated {len(parser_files)} files")
            except Exception as e:
                print(f"   ❌ Failed: {e}")
                success = False

        if 'docs' in targets:
            print("📚 Generating documentation...")
            try:
                doc_files = generate_documentation(self.schema)
                self.generated_files.extend(doc_files)
                print(f"   ✅ Generated {len(doc_files)} files")
            except Exception as e:
                print(f"   ❌ Failed: {e}")
                success = False

        print(f"\n{'✅' if success else '❌'} Generation complete!")
        print(f"📁 Generated {len(self.generated_files)} files:")
        for file in self.generated_files:
            print(f"   - {file}")

        return success

    def show_summary(self):
        """Display schema summary."""
        print("\n📋 Schema Summary")
        print("=" * 60)
        print(f"Version: {self.schema['version']}")

        if 'server_metrics' in self.schema:
            fields = self.schema['server_metrics'].get('fields', [])
            bash_fields = [f for f in fields if f.get('bash_output')]
            print(f"Server Metrics: {len(fields)} fields ({len(bash_fields)} from bash)")

        if 'top_users' in self.schema:
            fields = self.schema['top_users'].get('fields', [])
            bash_fields = [f for f in fields if f.get('bash_output')]
            print(f"Top Users: {len(fields)} fields ({len(bash_fields)} from bash)")

        if 'api_endpoints' in self.schema:
            endpoints = self.schema.get('api_endpoints', [])
            print(f"API Endpoints: {len(endpoints)}")

        print("=" * 60)

def main():
    parser = argparse.ArgumentParser(description='Generate code from schema definition')
    parser.add_argument('--schema', default='schema/metrics_schema.yaml',
                       help='Path to schema YAML file')
    parser.add_argument('--validate-only', action='store_true',
                       help='Only validate schema, do not generate')
    parser.add_argument('--target', default='all',
                       help='Comma-separated list of targets to generate (sql,python,typescript,validators,parsers,docs)')
    parser.add_argument('--summary', action='store_true',
                       help='Show schema summary')

    args = parser.parse_args()

    generator = SchemaGenerator(args.schema)

    if args.summary:
        generator.show_summary()
        return

    # Always validate first
    if not generator.validate_schema():
        sys.exit(1)

    if args.validate_only:
        print("\n✅ Validation complete. Run without --validate-only to generate code.")
        return

    # Parse targets
    targets = None if args.target == 'all' else args.target.split(',')

    # Generate code
    success = generator.generate_all(targets)
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
```

#### Step 1.3: Create SQL Generator

**File:** `schema/generators/generate_sql.py`

```python
#!/usr/bin/env python3
"""
Generate SQL migration scripts from schema definition.
"""

from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime

def sql_type_mapping(yaml_type: str) -> str:
    """Map YAML types to SQL types."""
    mapping = {
        'serial': 'SERIAL',
        'integer': 'INTEGER',
        'varchar': 'VARCHAR',
        'decimal': 'DECIMAL',
        'timestamp': 'TIMESTAMP',
        'text': 'TEXT',
        'boolean': 'BOOLEAN'
    }

    # Handle types with parameters (e.g., varchar(255))
    if '(' in yaml_type:
        base_type = yaml_type.split('(')[0]
        param = yaml_type.split('(')[1].rstrip(')')
        return f"{mapping.get(base_type, yaml_type).upper()}"

    return mapping.get(yaml_type, yaml_type.upper())

def generate_create_table(table_name: str, fields: List[Dict[str, Any]]) -> str:
    """Generate CREATE TABLE statement."""
    lines = [f"CREATE TABLE IF NOT EXISTS {table_name} ("]

    field_defs = []
    for field in fields:
        parts = [f"    {field['name']}"]

        # Type
        sql_type = field['type']
        parts.append(sql_type.upper())

        # Constraints
        if field.get('primary_key'):
            parts.append('PRIMARY KEY')
        if not field.get('nullable', True):
            parts.append('NOT NULL')
        if 'default' in field:
            default = field['default']
            if default == 'CURRENT_TIMESTAMP':
                parts.append('DEFAULT CURRENT_TIMESTAMP')
            else:
                parts.append(f"DEFAULT '{default}'")

        field_defs.append(' '.join(parts))

    lines.append(',\n'.join(field_defs))
    lines.append(");")

    return '\n'.join(lines)

def generate_indexes(table_name: str, fields: List[Dict[str, Any]]) -> str:
    """Generate CREATE INDEX statements for fields that should be indexed."""
    indexes = []

    # Common fields to index
    index_fields = ['server_name', 'timestamp']

    # Index fields with thresholds (for quick filtering)
    for field in fields:
        if 'visualization' in field and 'thresholds' in field['visualization']:
            index_fields.append(field['name'])

    for field_name in index_fields:
        if any(f['name'] == field_name for f in fields):
            index_name = f"idx_{table_name}_{field_name}"
            indexes.append(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name}({field_name});")

    return '\n'.join(indexes)

def generate_sql_migration(schema: Dict[str, Any]) -> str:
    """Generate complete SQL migration script."""

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = Path(f"srcs/Backend/migrations/{timestamp}_schema_migration.sql")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    sql_parts = []

    # Header
    sql_parts.append(f"""-- Generated SQL Migration
-- Schema Version: {schema['version']}
-- Generated At: {schema['generated_at']}
-- DO NOT EDIT MANUALLY - This file is auto-generated from schema/metrics_schema.yaml

BEGIN;

""")

    # Generate server_metrics table
    if 'server_metrics' in schema:
        sql_parts.append("-- Server Metrics Table")
        sql_parts.append(generate_create_table(
            schema['server_metrics']['table_name'],
            schema['server_metrics']['fields']
        ))
        sql_parts.append("\n")
        sql_parts.append(generate_indexes(
            schema['server_metrics']['table_name'],
            schema['server_metrics']['fields']
        ))
        sql_parts.append("\n\n")

    # Generate top_users table
    if 'top_users' in schema:
        sql_parts.append("-- Top Users Table")
        sql_parts.append(generate_create_table(
            schema['top_users']['table_name'],
            schema['top_users']['fields']
        ))
        sql_parts.append("\n")
        sql_parts.append(generate_indexes(
            schema['top_users']['table_name'],
            schema['top_users']['fields']
        ))
        sql_parts.append("\n\n")

    sql_parts.append("COMMIT;")

    # Write to file
    sql_content = ''.join(sql_parts)
    with open(output_file, 'w') as f:
        f.write(sql_content)

    return str(output_file)

if __name__ == '__main__':
    # Test
    import yaml
    with open('schema/metrics_schema.yaml') as f:
        schema = yaml.safe_load(f)

    output = generate_sql_migration(schema)
    print(f"Generated: {output}")
```

#### Step 1.4: Create Python Model Generator

**File:** `schema/generators/generate_python.py`

```python
#!/usr/bin/env python3
"""
Generate Python dataclasses and models from schema definition.
"""

from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime

def python_type_mapping(yaml_type: str) -> str:
    """Map YAML types to Python types."""
    mapping = {
        'serial': 'int',
        'integer': 'int',
        'varchar': 'str',
        'decimal': 'float',
        'timestamp': 'datetime',
        'text': 'str',
        'boolean': 'bool'
    }

    base_type = yaml_type.split('(')[0] if '(' in yaml_type else yaml_type
    return mapping.get(base_type, 'Any')

def generate_dataclass(table_name: str, fields: List[Dict[str, Any]], class_name: str) -> str:
    """Generate Python dataclass."""

    lines = [
        "from dataclasses import dataclass, field",
        "from typing import Optional",
        "from datetime import datetime",
        "",
        "",
        "@dataclass",
        f"class {class_name}:"
    ]

    # Add docstring
    lines.append(f'    """{class_name} data model (auto-generated from schema)."""')
    lines.append("")

    # Add fields
    for f in fields:
        py_type = python_type_mapping(f['type'])
        is_optional = f.get('nullable', True) and not f.get('primary_key')

        if is_optional:
            type_hint = f"Optional[{py_type}] = None"
        else:
            type_hint = py_type

        # Add field with description as comment
        if 'description' in f:
            lines.append(f"    # {f['description']}")

        lines.append(f"    {f['name']}: {type_hint}")

    # Add helper methods
    lines.extend([
        "",
        "    def to_dict(self) -> dict:",
        '        """Convert to dictionary."""',
        "        return {",
        "            k: v.isoformat() if isinstance(v, datetime) else v",
        "            for k, v in self.__dict__.items()",
        "        }",
        "",
        "    @classmethod",
        "    def from_dict(cls, data: dict):",
        '        """Create instance from dictionary."""',
        "        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})",
    ])

    return '\n'.join(lines)

def generate_python_models(schema: Dict[str, Any]) -> List[str]:
    """Generate all Python model files."""

    output_files = []

    # Generate server_metrics model
    if 'server_metrics' in schema:
        output_file = Path("srcs/Backend/generated/models/server_metrics.py")
        output_file.parent.mkdir(parents=True, exist_ok=True)

        content = f"""# Generated Python Model
# Schema Version: {schema['version']}
# Generated At: {schema['generated_at']}
# DO NOT EDIT MANUALLY

{generate_dataclass(
    schema['server_metrics']['table_name'],
    schema['server_metrics']['fields'],
    'ServerMetrics'
)}
"""

        with open(output_file, 'w') as f:
            f.write(content)

        output_files.append(str(output_file))

    # Generate top_users model
    if 'top_users' in schema:
        output_file = Path("srcs/Backend/generated/models/top_users.py")
        output_file.parent.mkdir(parents=True, exist_ok=True)

        content = f"""# Generated Python Model
# Schema Version: {schema['version']}
# Generated At: {schema['generated_at']}
# DO NOT EDIT MANUALLY

{generate_dataclass(
    schema['top_users']['table_name'],
    schema['top_users']['fields'],
    'TopUsers'
)}
"""

        with open(output_file, 'w') as f:
            f.write(content)

        output_files.append(str(output_file))

    # Generate __init__.py
    init_file = Path("srcs/Backend/generated/models/__init__.py")
    with open(init_file, 'w') as f:
        f.write("""# Generated models
from .server_metrics import ServerMetrics
from .top_users import TopUsers

__all__ = ['ServerMetrics', 'TopUsers']
""")

    output_files.append(str(init_file))

    return output_files
```

---

### Phase 2: Create Parser Generator (Days 2-3)

**File:** `schema/generators/generate_parsers.py`

```python
#!/usr/bin/env python3
"""
Generate bash output parsers from schema definition.
This replaces the manual parsing logic in backend.py.
"""

from typing import Dict, Any, List
from pathlib import Path

def generate_bash_parser(schema: Dict[str, Any]) -> List[str]:
    """Generate parser for bash script output."""

    output_file = Path("srcs/DataCollection/generated/bash_parser.py")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Build field parsing logic
    parsing_code = []

    if 'server_metrics' in schema:
        fields = schema['server_metrics']['fields']
        bash_fields = [f for f in fields if f.get('bash_output')]

        parsing_code.append("""
def parse_server_metrics(bash_output: str) -> dict:
    \"\"\"
    Parse mini_monitering.sh output (--line-format).
    Auto-generated from schema definition.
    \"\"\"
    parts = bash_output.strip().split(',')

    result = {}

""")

        for field in bash_fields:
            idx = field['bash_index']
            name = field['name']
            bash_format = field.get('bash_format', 'raw')

            if bash_format == 'raw':
                parsing_code.append(f"    result['{name}'] = parts[{idx}] if len(parts) > {idx} else None")

            elif bash_format == 'part_before_slash':
                parsing_code.append(f"""    if len(parts) > {idx}:
        result['{name}'] = parts[{idx}].split('/')[0] if '/' in parts[{idx}] else parts[{idx}]
""")

            elif bash_format == 'part_after_slash':
                parsing_code.append(f"""    if len(parts) > {idx}:
        result['{name}'] = parts[{idx}].split('/')[1] if '/' in parts[{idx}] else parts[{idx}]
""")

            elif bash_format.startswith('csv_split_'):
                split_idx = bash_format.split('_')[-1]
                parsing_code.append(f"""    if len(parts) > {idx}:
        csv_parts = parts[{idx}].split(',')
        result['{name}'] = csv_parts[{split_idx}] if len(csv_parts) > {split_idx} else None
""")

            elif bash_format == 'strip_percent':
                parsing_code.append(f"""    if len(parts) > {idx}:
        result['{name}'] = parts[{idx}].rstrip('%')
""")

        parsing_code.append("""
    return result
""")

    # Similar for top_users
    if 'top_users' in schema:
        fields = schema['top_users']['fields']
        bash_fields = [f for f in fields if f.get('bash_output')]

        parsing_code.append("""
def parse_top_users_line(bash_line: str) -> dict:
    \"\"\"
    Parse single line from TopUsers.sh output.
    Auto-generated from schema definition.
    \"\"\"
    parts = bash_line.strip().split()

    result = {}

""")

        for field in bash_fields:
            idx = field['bash_index']
            name = field['name']
            parsing_code.append(f"    result['{name}'] = parts[{idx}] if len(parts) > {idx} else None")

        parsing_code.append("""
    return result
""")

    # Write to file
    content = f"""# Generated Bash Output Parser
# Schema Version: {schema['version']}
# Generated At: {schema['generated_at']}
# DO NOT EDIT MANUALLY

from typing import Dict, Optional, List

{''.join(parsing_code)}

def parse_top_users(bash_output: str) -> List[dict]:
    \"\"\"Parse complete TopUsers.sh output.\"\"\"
    lines = [line for line in bash_output.split('\\n') if line.strip() and not line.startswith('-')]
    return [parse_top_users_line(line) for line in lines[2:]]  # Skip header lines
"""

    with open(output_file, 'w') as f:
        f.write(content)

    return [str(output_file)]
```

---

### Phase 3: Create Validator Generator (Days 3-4)

**File:** `schema/generators/generate_validators.py`

```python
#!/usr/bin/env python3
"""
Generate validation functions from schema definition.
This replaces manual validation in validation.py.
"""

from typing import Dict, Any, List
from pathlib import Path

def generate_validators(schema: Dict[str, Any]) -> List[str]:
    """Generate validation functions for all fields."""

    output_file = Path("srcs/Frontend/generated/validators.py")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    validator_code = ["""# Generated Validators
# Schema Version: {version}
# Generated At: {generated_at}
# DO NOT EDIT MANUALLY

from typing import Any, Optional
from datetime import datetime
import re

class ValidationError(Exception):
    pass

""".format(**schema)]

    # Generate validator for each validation type
    seen_validators = set()

    for table_key in ['server_metrics', 'top_users']:
        if table_key in schema:
            for field in schema[table_key]['fields']:
                if 'validation' in field:
                    val_type = field['validation']['type']

                    if val_type in seen_validators:
                        continue
                    seen_validators.add(val_type)

                    if val_type == 'percentage':
                        validator_code.append("""
def validate_percentage(value: Any, field_name: str = 'field') -> float:
    \"\"\"Validate percentage (0-100).\"\"\"
    try:
        val = float(value)
        if val < 0 or val > 100:
            raise ValidationError(f"{field_name} must be between 0 and 100, got {val}")
        return val
    except (ValueError, TypeError):
        raise ValidationError(f"{field_name} must be a number, got {type(value).__name__}")

""")

                    elif val_type == 'integer':
                        min_val = field['validation'].get('min', 'None')
                        max_val = field['validation'].get('max', 'None')
                        validator_code.append(f"""
def validate_integer(value: Any, field_name: str = 'field', min_val: Optional[int] = {min_val}, max_val: Optional[int] = {max_val}) -> int:
    \"\"\"Validate integer with optional min/max.\"\"\"
    try:
        val = int(value)
        if min_val is not None and val < min_val:
            raise ValidationError(f"{{field_name}} must be >= {{min_val}}, got {{val}}")
        if max_val is not None and val > max_val:
            raise ValidationError(f"{{field_name}} must be <= {{max_val}}, got {{val}}")
        return val
    except (ValueError, TypeError):
        raise ValidationError(f"{{field_name}} must be an integer, got {{type(value).__name__}}")

""")

    # Generate field-specific validators
    validator_code.append("\n# Field-specific validators\n")

    for table_key in ['server_metrics', 'top_users']:
        if table_key in schema:
            class_name = ''.join(word.capitalize() for word in table_key.split('_'))
            validator_code.append(f"\nclass {class_name}Validator:\n")
            validator_code.append(f'    """Validator for {table_key} fields."""\n\n')

            for field in schema[table_key]['fields']:
                if 'validation' in field:
                    field_name = field['name']
                    val_type = field['validation']['type']

                    validator_code.append(f"    @staticmethod\n")
                    validator_code.append(f"    def validate_{field_name}(value: Any) -> Any:\n")
                    validator_code.append(f'        """Validate {field.get("description", field_name)}."""\n')

                    if val_type == 'percentage':
                        validator_code.append(f"        return validate_percentage(value, '{field_name}')\n\n")
                    elif val_type == 'integer':
                        min_val = field['validation'].get('min')
                        max_val = field['validation'].get('max')
                        validator_code.append(f"        return validate_integer(value, '{field_name}', {min_val}, {max_val})\n\n")

    # Write to file
    with open(output_file, 'w') as f:
        f.write(''.join(validator_code))

    return [str(output_file)]
```

---

### Phase 4: Create TypeScript Types Generator (Day 4)

**File:** `schema/generators/generate_typescript.py`

```python
#!/usr/bin/env python3
"""
Generate TypeScript type definitions from schema definition.
Useful if Frontend eventually migrates to TypeScript or needs type checking.
"""

from typing import Dict, Any, List
from pathlib import Path

def ts_type_mapping(yaml_type: str) -> str:
    """Map YAML types to TypeScript types."""
    mapping = {
        'serial': 'number',
        'integer': 'number',
        'varchar': 'string',
        'decimal': 'number',
        'timestamp': 'Date | string',
        'text': 'string',
        'boolean': 'boolean'
    }

    base_type = yaml_type.split('(')[0] if '(' in yaml_type else yaml_type
    return mapping.get(base_type, 'any')

def generate_ts_interface(table_name: str, fields: List[Dict[str, Any]], interface_name: str) -> str:
    """Generate TypeScript interface."""

    lines = [
        f"/**",
        f" * {interface_name} interface (auto-generated from schema)",
        f" * Table: {table_name}",
        f" */",
        f"export interface {interface_name} {{"
    ]

    for field in fields:
        ts_type = ts_type_mapping(field['type'])
        is_optional = field.get('nullable', True) and not field.get('primary_key')

        # Add JSDoc comment
        if 'description' in field:
            lines.append(f"  /** {field['description']} */")

        # Add field
        optional_marker = '?' if is_optional else ''
        lines.append(f"  {field['name']}{optional_marker}: {ts_type};")

    lines.append("}")

    return '\n'.join(lines)

def generate_ts_validator_helpers(schema: Dict[str, Any]) -> str:
    """Generate TypeScript validation helper functions."""

    code = ["""
/**
 * Validation helper functions
 */

export class ValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ValidationError';
  }
}

export function validatePercentage(value: any, fieldName: string = 'field'): number {
  const val = Number(value);
  if (isNaN(val)) {
    throw new ValidationError(`${fieldName} must be a number, got ${typeof value}`);
  }
  if (val < 0 || val > 100) {
    throw new ValidationError(`${fieldName} must be between 0 and 100, got ${val}`);
  }
  return val;
}

export function validateInteger(
  value: any,
  fieldName: string = 'field',
  minVal?: number,
  maxVal?: number
): number {
  const val = Number(value);
  if (isNaN(val) || !Number.isInteger(val)) {
    throw new ValidationError(`${fieldName} must be an integer, got ${typeof value}`);
  }
  if (minVal !== undefined && val < minVal) {
    throw new ValidationError(`${fieldName} must be >= ${minVal}, got ${val}`);
  }
  if (maxVal !== undefined && val > maxVal) {
    throw new ValidationError(`${fieldName} must be <= ${maxVal}, got ${val}`);
  }
  return val;
}

export function validateString(
  value: any,
  fieldName: string = 'field',
  maxLength?: number
): string {
  if (typeof value !== 'string') {
    throw new ValidationError(`${fieldName} must be a string, got ${typeof value}`);
  }
  if (maxLength !== undefined && value.length > maxLength) {
    throw new ValidationError(`${fieldName} exceeds max length ${maxLength}`);
  }
  return value;
}
"""]

    return '\n'.join(code)

def generate_ts_api_client(schema: Dict[str, Any]) -> str:
    """Generate TypeScript API client with proper types."""

    code = ["""
/**
 * Typed API client for server metrics dashboard
 * Auto-generated from schema
 */

import { ServerMetrics, TopUsers } from './types';

export class ApiClient {
  private baseUrl: string;
  private timeout: number;

  constructor(baseUrl: string = 'http://localhost:5000', timeout: number = 10000) {
    this.baseUrl = baseUrl;
    this.timeout = timeout;
  }

  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        ...options,
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status} ${response.statusText}`);
      }

      return await response.json();
    } finally {
      clearTimeout(timeoutId);
    }
  }
"""]

    # Generate methods for each API endpoint
    if 'api_endpoints' in schema:
        for endpoint in schema['api_endpoints']:
            path = endpoint['path']
            method = endpoint['method'].lower()
            description = endpoint.get('description', '')
            returns = endpoint.get('returns', '')

            # Determine return type
            if returns == 'server_metrics':
                return_type = 'ServerMetrics[]'
            elif returns == 'top_users':
                return_type = 'TopUsers[]'
            else:
                return_type = 'any'

            # Generate method name from path
            method_name = path.replace('/api/', '').replace('/', '_').replace('<', '').replace('>', '')
            method_name = method_name.replace('server_name', 'serverName').replace('_', '')

            # Extract parameters
            params = endpoint.get('parameters', [])
            param_list = ', '.join([f"{p['name']}: {ts_type_mapping(p['type'])}" for p in params])

            code.append(f"""
  /**
   * {description}
   */
  async {method_name}({param_list}): Promise<{return_type}> {{
""")

            # Build URL with parameters
            url = path
            for param in params:
                url = url.replace(f"<{param['name']}>", f"${{{param['name']}}}")

            code.append(f"""    return this.request<{return_type}>(`{url}`);
  }}
""")

    code.append("}")

    return '\n'.join(code)

def generate_typescript_types(schema: Dict[str, Any]) -> List[str]:
    """Generate all TypeScript files."""

    output_files = []

    # Generate main types file
    types_file = Path("srcs/Frontend/generated/types.ts")
    types_file.parent.mkdir(parents=True, exist_ok=True)

    types_content = [f"""// Generated TypeScript Types
// Schema Version: {schema['version']}
// Generated At: {schema['generated_at']}
// DO NOT EDIT MANUALLY

"""]

    # Generate interfaces
    if 'server_metrics' in schema:
        types_content.append(generate_ts_interface(
            schema['server_metrics']['table_name'],
            schema['server_metrics']['fields'],
            'ServerMetrics'
        ))
        types_content.append("\n\n")

    if 'top_users' in schema:
        types_content.append(generate_ts_interface(
            schema['top_users']['table_name'],
            schema['top_users']['fields'],
            'TopUsers'
        ))
        types_content.append("\n\n")

    # Add API response types
    types_content.append("""
/**
 * Standard API response wrapper
 */
export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
}

/**
 * API error response
 */
export interface ApiError {
  success: false;
  message: string;
  error?: string;
}
""")

    with open(types_file, 'w') as f:
        f.write(''.join(types_content))

    output_files.append(str(types_file))

    # Generate validators file
    validators_file = Path("srcs/Frontend/generated/validators.ts")
    with open(validators_file, 'w') as f:
        f.write(f"""// Generated TypeScript Validators
// Schema Version: {schema['version']}
// Generated At: {schema['generated_at']}
// DO NOT EDIT MANUALLY

{generate_ts_validator_helpers(schema)}
""")

    output_files.append(str(validators_file))

    # Generate API client
    api_client_file = Path("srcs/Frontend/generated/apiClient.ts")
    with open(api_client_file, 'w') as f:
        f.write(f"""// Generated TypeScript API Client
// Schema Version: {schema['version']}
// Generated At: {schema['generated_at']}
// DO NOT EDIT MANUALLY

{generate_ts_api_client(schema)}
""")

    output_files.append(str(api_client_file))

    return output_files
```

---

### Phase 5: Create Documentation Generator (Day 5)

**File:** `schema/generators/generate_docs.py`

```python
#!/usr/bin/env python3
"""
Generate comprehensive documentation from schema definition.
Creates markdown files for database schema, API endpoints, and field reference.
"""

from typing import Dict, Any, List
from pathlib import Path

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
        ""
    ]

    # Server Metrics Table
    if 'server_metrics' in schema:
        table = schema['server_metrics']
        lines.extend([
            f"## Table: `{table['table_name']}`",
            "",
            table.get('description', 'Server monitoring metrics'),
            "",
            "### Columns",
            "",
            "| Column | Type | Nullable | Description | Validation |",
            "|--------|------|----------|-------------|------------|"
        ])

        for field in table['fields']:
            name = field['name']
            ftype = field['type']
            nullable = "Yes" if field.get('nullable', True) else "No"
            desc = field.get('description', '-')
            validation = ""

            if 'validation' in field:
                val_type = field['validation']['type']
                if 'min' in field['validation'] or 'max' in field['validation']:
                    min_v = field['validation'].get('min', '')
                    max_v = field['validation'].get('max', '')
                    validation = f"{val_type} ({min_v}-{max_v})"
                else:
                    validation = val_type

            lines.append(f"| `{name}` | {ftype} | {nullable} | {desc} | {validation} |")

        lines.extend(["", "### Indexes", ""])

        # List indexed fields
        indexed = ['server_name', 'timestamp']
        for field in table['fields']:
            if 'visualization' in field and 'thresholds' in field['visualization']:
                indexed.append(field['name'])

        for idx_field in indexed:
            lines.append(f"- `idx_{table['table_name']}_{idx_field}` on `{idx_field}`")

        lines.append("")

    # Top Users Table
    if 'top_users' in schema:
        table = schema['top_users']
        lines.extend([
            "---",
            "",
            f"## Table: `{table['table_name']}`",
            "",
            "Per-user resource usage metrics",
            "",
            "### Columns",
            "",
            "| Column | Type | Nullable | Description | Validation |",
            "|--------|------|----------|-------------|------------|"
        ])

        for field in table['fields']:
            name = field['name']
            ftype = field['type']
            nullable = "Yes" if field.get('nullable', True) else "No"
            desc = field.get('description', '-')
            validation = ""

            if 'validation' in field:
                val_type = field['validation']['type']
                validation = val_type

            lines.append(f"| `{name}` | {ftype} | {nullable} | {desc} | {validation} |")

        lines.append("")

    return '\n'.join(lines)

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
        ""
    ]

    if 'api_endpoints' in schema:
        for endpoint in schema['api_endpoints']:
            path = endpoint['path']
            method = endpoint['method']
            description = endpoint.get('description', '')
            returns = endpoint.get('returns', '')
            params = endpoint.get('parameters', [])

            lines.extend([
                f"### `{method} {path}`",
                "",
                description,
                ""
            ])

            if params:
                lines.extend([
                    "**Parameters:**",
                    ""
                ])

                for param in params:
                    required = "Required" if param.get('required') else "Optional"
                    lines.append(f"- `{param['name']}` ({param['type']}) - {required}")

                    if 'validation' in param:
                        val = param['validation']
                        if 'min' in val:
                            lines.append(f"  - Min: {val['min']}")
                        if 'max' in val:
                            lines.append(f"  - Max: {val['max']}")

                lines.append("")

            lines.extend([
                "**Returns:**",
                "",
                f"- Table: `{returns}`",
                "",
                "**Example Request:**",
                "",
                "```bash",
                f"curl http://localhost:5000{path.replace('<server_name>', 'Server1').replace('<hours>', '24')}",
                "```",
                "",
                "**Example Response:**",
                "",
                "```json",
                "{",
                '  "success": true,',
                '  "data": [',
                "    { ... }",
                "  ]",
                "}",
                "```",
                "",
                "---",
                ""
            ])

    return '\n'.join(lines)

def generate_field_reference(schema: Dict[str, Any]) -> str:
    """Generate field reference documentation grouped by category."""

    lines = [
        "# Field Reference",
        "",
        f"**Schema Version:** {schema['version']}  ",
        f"**Generated:** {schema['generated_at']}  ",
        "",
        "Complete reference of all fields organized by category.",
        "",
        "---",
        ""
    ]

    # Group fields by category
    if 'metric_groups' in schema and 'server_metrics' in schema:
        groups = {g['id']: g for g in schema['metric_groups']}

        for group_id in sorted(groups.keys(), key=lambda x: groups[x]['order']):
            group = groups[group_id]
            lines.extend([
                f"## {group['name']}",
                ""
            ])

            # Find fields in this group
            group_fields = [f for f in schema['server_metrics']['fields'] if f.get('group') == group_id]

            if not group_fields:
                lines.append("*No fields in this category*")
                lines.append("")
                continue

            for field in group_fields:
                lines.extend([
                    f"### {field.get('frontend_display', field['name'])}",
                    "",
                    f"**Field Name:** `{field['name']}`  ",
                    f"**Type:** {field['type']}  ",
                    f"**Bash Output:** {'Yes' if field.get('bash_output') else 'No'}  "
                ])

                if field.get('bash_output'):
                    lines.append(f"**Bash Index:** {field.get('bash_index')}  ")
                    lines.append(f"**Bash Format:** {field.get('bash_format', 'raw')}  ")

                lines.append("")

                if 'description' in field:
                    lines.append(field['description'])
                    lines.append("")

                if 'validation' in field:
                    lines.append("**Validation:**")
                    lines.append("")
                    val = field['validation']
                    lines.append(f"- Type: `{val['type']}`")
                    if 'min' in val:
                        lines.append(f"- Minimum: {val['min']}")
                    if 'max' in val:
                        lines.append(f"- Maximum: {val['max']}")
                    lines.append("")

                if 'visualization' in field:
                    lines.append("**Visualization:**")
                    lines.append("")
                    viz = field['visualization']
                    lines.append(f"- Type: {viz['type']}")
                    if 'thresholds' in viz:
                        lines.append("- Thresholds:")
                        for level, value in viz['thresholds'].items():
                            lines.append(f"  - {level.capitalize()}: {value}%")
                    lines.append("")

                lines.append("---")
                lines.append("")

    return '\n'.join(lines)

def generate_adding_metrics_guide(schema: Dict[str, Any]) -> str:
    """Generate step-by-step guide for adding new metrics."""

    return f"""# Adding New Metrics Guide

**Schema Version:** {schema['version']}
**Generated:** {schema['generated_at']}

This guide explains how to add a new metric to the monitoring system using the schema-driven approach.

---

## Overview

With the schema-driven architecture, adding a new metric requires **only 2 steps**:

1. Add field definition to `schema/metrics_schema.yaml`
2. Run `python schema/generators/generate_all.py`

All database migrations, API updates, parsers, validators, and documentation are generated automatically!

---

## Step-by-Step Guide

### Step 1: Update Bash Script

First, update the bash script to collect the new metric.

**File:** `srcs/DataCollection/mini_monitering.sh`

Add your new metric collection logic. For example, to add swap memory:

```bash
# Add after RAM section (around line 14)
SWAP_DATA=$(free -m | grep Swap)
SWAP_USED=$(echo "$SWAP_DATA" | awk '{{printf("%.2fG"), $3/1024.0}}')
SWAP_TOTAL=$(echo "$SWAP_DATA" | awk '{{printf("%.2fG"), $2/1024.0}}')
SWAP_PERC=$(echo "$SWAP_DATA" | awk '{{if($2>0) printf("%.0f"), $3 / $2 * 100; else print "0"}}')
```

Update the line format output to include new fields (line 45):

```bash
printf "${{ARCH}},${{OS}},...,${{SWAP_USED}}/${{SWAP_TOTAL}},${{SWAP_PERC}}\\n"
```

**Important:** Note the index position of your new field in the CSV output. This will be your `bash_index`.

### Step 2: Update Schema Definition

**File:** `schema/metrics_schema.yaml`

Add your new field to the `server_metrics.fields` array:

```yaml
    # Swap Memory (NEW)
    - name: swap_used
      type: varchar(20)
      nullable: true
      bash_output: true
      bash_index: 14  # Position in CSV output from bash script
      bash_format: "part_before_slash"  # "2.5G/16G" -> "2.5G"
      group: resources
      description: "Swap memory currently in use"
      frontend_display: "Swap Used"
      validation:
        type: string

    - name: swap_total
      type: varchar(20)
      nullable: true
      bash_output: true
      bash_index: 14
      bash_format: "part_after_slash"  # "2.5G/16G" -> "16G"
      group: resources
      description: "Total swap memory available"
      frontend_display: "Swap Total"

    - name: swap_percentage
      type: integer
      nullable: true
      bash_output: true
      bash_index: 15
      group: resources
      description: "Swap usage percentage"
      frontend_display: "Swap %"
      visualization:
        type: progress_bar
        thresholds:
          warning: 50
          critical: 75
      validation:
        type: percentage
        min: 0
        max: 100
```

### Step 3: Generate All Code

Run the code generator:

```bash
cd schema/generators
python generate_all.py
```

This will automatically generate:

- ✅ SQL migration (`srcs/Backend/migrations/TIMESTAMP_schema_migration.sql`)
- ✅ Python models (`srcs/Backend/generated/models/server_metrics.py`)
- ✅ Bash parser (`srcs/DataCollection/generated/bash_parser.py`)
- ✅ Validators (`srcs/Frontend/generated/validators.py`)
- ✅ TypeScript types (`srcs/Frontend/generated/types.ts`)
- ✅ Documentation (this file and others)

### Step 4: Apply Database Migration

```bash
# Stop services
make down

# Start only database
docker compose up -d postgres

# Apply migration
docker exec -i postgres psql -U postgres server_db < srcs/Backend/migrations/LATEST_MIGRATION.sql

# Restart all services
make up
```

### Step 5: Update Backend to Use Generated Code

**File:** `srcs/DataCollection/backend.py`

Replace manual parsing with generated parser:

```python
# Old way (REMOVE):
# parts = output.split(',')
# swap_used = parts[14].split('/')[0]
# ...

# New way (ADD):
from generated.bash_parser import parse_server_metrics

data = parse_server_metrics(bash_output)
# data now contains all fields automatically!
```

Update the database insert to use generated model:

```python
from generated.models.server_metrics import ServerMetrics

metrics = ServerMetrics.from_dict(data)
# Insert to database
```

### Step 6: Update API to Include New Fields

The API should automatically include new fields if using `SELECT *`. However, if you have explicit field lists:

**File:** `srcs/Backend/api.py`

```python
# Use generated model
from generated.models.server_metrics import ServerMetrics

# Fields are automatically available in queries
# No manual updates needed if using generated code!
```

### Step 7: Update Frontend

**File:** `srcs/Frontend/components.py`

Add display component for new metric:

```python
from generated.validators import ServerMetricsValidator

def create_swap_card(data):
    # Validate data
    swap_perc = ServerMetricsValidator.validate_swap_percentage(data.get('swap_percentage', 0))

    return dbc.Card([
        dbc.CardBody([
            html.H4("Swap Usage"),
            html.H2(f"{{data.get('swap_used')}}/{{data.get('swap_total')}}"),
            dbc.Progress(value=swap_perc, color="info")
        ])
    ])
```

### Step 8: Test End-to-End

1. **Test bash script:**
   ```bash
   ./mini_monitering.sh --line-format
   # Verify new fields appear in output
   ```

2. **Test data collection:**
   ```bash
   make logs-DataCollection
   # Watch for successful data insertion
   ```

3. **Test API:**
   ```bash
   curl http://localhost:5000/api/servers/metrics/latest | jq
   # Verify new fields in response
   ```

4. **Test frontend:**
   - Open http://localhost:3000
   - Verify new metrics display correctly

---

## Field Configuration Options

### `bash_format` Options

- `raw` - Use value as-is from CSV
- `part_before_slash` - Extract part before `/` (e.g., "2.5G/16G" → "2.5G")
- `part_after_slash` - Extract part after `/` (e.g., "2.5G/16G" → "16G")
- `csv_split_0` - Split by comma, take first part (e.g., "1,2,3" → "1")
- `csv_split_1` - Split by comma, take second part
- `strip_percent` - Remove `%` sign (e.g., "45%" → "45")

### `validation.type` Options

- `percentage` - Float 0-100
- `integer` - Whole number (supports min/max)
- `float` - Decimal number (supports min/max)
- `string` - Text (supports max_length)
- `datetime` - Timestamp
- `memory_size` - Memory size string (e.g., "2.5G")

### `visualization.type` Options

- `progress_bar` - Progress bar with thresholds
- `line_chart` - Time-series line graph
- `bar_chart` - Bar chart
- `badge` - Colored badge

---

## Troubleshooting

### Parser Returns None for New Field

**Problem:** Parser returns `None` for your new field.

**Solution:**
- Check `bash_index` matches the position in CSV output
- Verify bash script outputs the field
- Test bash script: `./mini_monitering.sh --line-format | cut -d',' -f15` (adjust field number)

### Database Insert Fails

**Problem:** Error inserting data into database.

**Solution:**
- Ensure migration was applied: `docker exec postgres psql -U postgres server_db -c "\\d server_metrics"`
- Check column exists and type matches
- Verify data format matches column type

### Validation Errors

**Problem:** Frontend shows validation errors.

**Solution:**
- Check `validation` rules in schema match actual data ranges
- Use generated validators: `ServerMetricsValidator.validate_field_name(value)`
- Add error handling: try/except around validation calls

### Field Not Showing in Frontend

**Problem:** New field doesn't appear in dashboard.

**Solution:**
- Ensure you added display component in `components.py`
- Check callback includes new field
- Verify API returns the field: `curl http://localhost:5000/api/servers/metrics/latest | jq`

---

## Example: Complete Workflow

Here's a complete example of adding "Network RX/TX" metrics:

```yaml
# 1. Update schema/metrics_schema.yaml
- name: network_rx_gb
  type: decimal(10,2)
  nullable: true
  bash_output: true
  bash_index: 16
  bash_format: "raw"
  group: network
  description: "Total network bytes received (GB)"
  frontend_display: "Network RX"
  validation:
    type: float
    min: 0

- name: network_tx_gb
  type: decimal(10,2)
  nullable: true
  bash_output: true
  bash_index: 17
  bash_format: "raw"
  group: network
  description: "Total network bytes transmitted (GB)"
  frontend_display: "Network TX"
  validation:
    type: float
    min: 0
```

```bash
# 2. Generate code
python schema/generators/generate_all.py

# 3. Apply migration
docker exec -i postgres psql -U postgres server_db < srcs/Backend/migrations/LATEST.sql

# 4. Restart services
make restart

# 5. Test
curl http://localhost:5000/api/servers/metrics/latest | jq '.data[0].network_rx_gb'
```

Done! Your new metrics are fully integrated across the entire stack.

---

## Benefits Summary

### Before (Manual Approach)
- Edit 10+ files manually
- 2-4 hours per metric
- High risk of bugs
- Inconsistencies between layers
- Manual synchronization required

### After (Schema-Driven Approach)
- Edit 1 file (schema.yaml)
- Run 1 command
- 15-30 minutes per metric
- Zero synchronization bugs
- All layers guaranteed consistent
- Automatic documentation updates

---

**Questions?** See `SCHEMA_DRIVEN_REFACTORING_PLAN.md` for complete architecture details.
"""

def generate_documentation(schema: Dict[str, Any]) -> List[str]:
    """Generate all documentation files."""

    output_files = []

    # Database schema docs
    db_docs_file = Path("docs/generated/DATABASE_SCHEMA.md")
    db_docs_file.parent.mkdir(parents=True, exist_ok=True)
    with open(db_docs_file, 'w') as f:
        f.write(generate_database_schema_docs(schema))
    output_files.append(str(db_docs_file))

    # API docs
    api_docs_file = Path("docs/generated/API_DOCUMENTATION.md")
    with open(api_docs_file, 'w') as f:
        f.write(generate_api_docs(schema))
    output_files.append(str(api_docs_file))

    # Field reference
    field_ref_file = Path("docs/generated/FIELD_REFERENCE.md")
    with open(field_ref_file, 'w') as f:
        f.write(generate_field_reference(schema))
    output_files.append(str(field_ref_file))

    # Adding metrics guide
    guide_file = Path("docs/generated/ADDING_METRICS_GUIDE.md")
    with open(guide_file, 'w') as f:
        f.write(generate_adding_metrics_guide(schema))
    output_files.append(str(guide_file))

    return output_files
```

---

## Complete Implementation Steps

### Setup Phase (1 hour)

```bash
# 1. Create directory structure
mkdir -p schema/generators
mkdir -p srcs/Backend/generated/models
mkdir -p srcs/DataCollection/generated
mkdir -p srcs/Frontend/generated
mkdir -p docs/generated

# 2. Install dependencies
pip install pyyaml  # For schema parsing

# 3. Create all generator files
# (Copy the code from above into respective files)
```

### Testing Phase (2 hours)

```bash
# 1. Validate schema
cd schema/generators
python generate_all.py --validate-only

# 2. Show schema summary
python generate_all.py --summary

# 3. Generate all code
python generate_all.py

# 4. Review generated files
ls -la srcs/Backend/generated/models/
ls -la srcs/DataCollection/generated/
ls -la srcs/Frontend/generated/
ls -la docs/generated/

# 5. Test generated SQL
docker exec -it postgres psql -U postgres server_db < srcs/Backend/migrations/LATEST.sql
```

### Integration Phase (4-6 hours)

See "Adding New Metrics Guide" generated in `docs/generated/ADDING_METRICS_GUIDE.md`

---

## Maintenance Workflow

### Daily Development

```bash
# When adding a new metric:
1. Edit schema/metrics_schema.yaml
2. Run: python schema/generators/generate_all.py
3. Apply migration: docker exec -i postgres psql -U postgres server_db < srcs/Backend/migrations/LATEST.sql
4. Restart: make restart
```

### Before Commits

```bash
# Always regenerate before committing schema changes
python schema/generators/generate_all.py
git add schema/ srcs/Backend/generated/ srcs/DataCollection/generated/ srcs/Frontend/generated/ docs/generated/
git commit -m "Add new metrics: [description]"
```

### Version Updates

When incrementing schema version:

```yaml
# Update schema/metrics_schema.yaml
version: "1.1.0"  # Increment version
```

```bash
# Regenerate everything
python schema/generators/generate_all.py

# All generated files will show new version number
```

---

## Benefits Recap

| Aspect | Before | After |
|--------|--------|-------|
| **Files to edit** | 10+ files | 1 file |
| **Time per metric** | 2-4 hours | 15-30 minutes |
| **Error rate** | High (manual sync) | Very low (automated) |
| **Type safety** | None | Full |
| **Documentation** | Manual, outdated | Auto-generated, current |
| **Testing** | Manual verification | Automated validation |
| **Onboarding** | Complex | Simple (read schema) |

---

## Next Steps

1. **Try it out:** Add a simple metric (e.g., system uptime) following the guide
2. **Migrate gradually:** Keep old code working while testing generated code
3. **Measure success:** Compare time to add metrics before/after
4. **Extend:** Add custom generators for your specific needs (e.g., Grafana dashboards, alerts)

---

**The key benefit: Future changes from 10+ places to 1 file + 1 command!**