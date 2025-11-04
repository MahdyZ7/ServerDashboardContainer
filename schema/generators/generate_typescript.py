#!/usr/bin/env python3
"""
Generate TypeScript type definitions from schema definition.
Useful if Frontend eventually migrates to TypeScript or needs type checking.
"""

from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime

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

def generate_typescript_types(schema: Dict[str, Any]) -> List[str]:
    """Generate all TypeScript files."""

    # Base path relative to this script
    base_path = Path(__file__).parent.parent.parent / 'srcs' / 'Frontend' / 'generated'
    base_path.mkdir(parents=True, exist_ok=True)

    output_files = []

    # Generate main types file
    types_file = base_path / "types.ts"

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
    types_content.append("""/**
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

    return output_files

if __name__ == '__main__':
    # Test
    import yaml
    with open('../metrics_schema.yaml') as f:
        schema = yaml.safe_load(f)

    schema['generated_at'] = datetime.now().isoformat()
    outputs = generate_typescript_types(schema)
    print(f"Generated {len(outputs)} files:")
    for output in outputs:
        print(f"  - {output}")
