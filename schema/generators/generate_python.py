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
        "serial": "int",
        "integer": "int",
        "varchar": "str",
        "decimal": "float",
        "timestamp": "datetime",
        "text": "str",
        "boolean": "bool",
    }

    base_type = yaml_type.split("(")[0] if "(" in yaml_type else yaml_type
    return mapping.get(base_type, "Any")


def generate_dataclass(
    table_name: str, fields: List[Dict[str, Any]], class_name: str
) -> str:
    """Generate Python dataclass."""

    lines = [
        "from dataclasses import dataclass, field",
        "from typing import Optional, Any",
        "from datetime import datetime",
        "",
        "",
        "@dataclass",
        f"class {class_name}:",
    ]

    # Add docstring
    lines.append(f'    """{class_name} data model (auto-generated from schema)."""')
    lines.append("")

    # Add fields
    for f in fields:
        py_type = python_type_mapping(f["type"])
        is_optional = f.get("nullable", True) and not f.get("primary_key")

        if is_optional:
            type_hint = f"Optional[{py_type}] = None"
        else:
            type_hint = py_type

        # Add field with description as comment
        if "description" in f:
            lines.append(f"    # {f['description']}")

        lines.append(f"    {f['name']}: {type_hint}")

    # Add helper methods
    lines.extend(
        [
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
        ]
    )

    return "\n".join(lines)


def generate_python_models(schema: Dict[str, Any]) -> List[str]:
    """Generate all Python model files."""

    output_files = []

    # Base path relative to this script
    base_path = (
        Path(__file__).parent.parent.parent
        / "srcs"
        / "Backend"
        / "generated"
        / "models"
    )
    base_path.mkdir(parents=True, exist_ok=True)

    # Generate server_metrics model
    if "server_metrics" in schema:
        output_file = base_path / "server_metrics.py"

        content = f"""# Generated Python Model
# Schema Version: {schema["version"]}
# Generated At: {schema["generated_at"]}
# DO NOT EDIT MANUALLY

{
            generate_dataclass(
                schema["server_metrics"]["table_name"],
                schema["server_metrics"]["fields"],
                "ServerMetrics",
            )
        }
"""

        with open(output_file, "w") as f:
            f.write(content)

        output_files.append(str(output_file))

    # Generate top_users model
    if "top_users" in schema:
        output_file = base_path / "top_users.py"

        content = f"""# Generated Python Model
# Schema Version: {schema["version"]}
# Generated At: {schema["generated_at"]}
# DO NOT EDIT MANUALLY

{
            generate_dataclass(
                schema["top_users"]["table_name"],
                schema["top_users"]["fields"],
                "TopUsers",
            )
        }
"""

        with open(output_file, "w") as f:
            f.write(content)

        output_files.append(str(output_file))

    # Generate __init__.py
    init_file = base_path / "__init__.py"
    with open(init_file, "w") as f:
        f.write("""# Generated models
from .server_metrics import ServerMetrics
from .top_users import TopUsers

__all__ = ['ServerMetrics', 'TopUsers']
""")

    output_files.append(str(init_file))

    return output_files


if __name__ == "__main__":
    # Test
    import yaml

    with open("../metrics_schema.yaml") as f:
        schema = yaml.safe_load(f)

    schema["generated_at"] = datetime.now().isoformat()
    outputs = generate_python_models(schema)
    print(f"Generated {len(outputs)} files:")
    for output in outputs:
        print(f"  - {output}")
