#!/usr/bin/env python3
"""
Generate bash output parsers from schema definition.
This replaces the manual parsing logic in backend.py.
"""

from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime


def generate_parsers(schema: Dict[str, Any]) -> List[str]:
    """Generate parser for bash script output."""

    # Base path relative to this script
    base_path = (
        Path(__file__).parent.parent.parent / "srcs" / "DataCollection" / "generated"
    )
    base_path.mkdir(parents=True, exist_ok=True)

    output_file = base_path / "bash_parser.py"

    # Build field parsing logic
    parsing_code = []

    if "server_metrics" in schema:
        fields = schema["server_metrics"]["fields"]
        bash_fields = [f for f in fields if f.get("bash_output")]

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
            idx = field["bash_index"]
            name = field["name"]
            bash_format = field.get("bash_format", "raw")

            if bash_format == "raw":
                parsing_code.append(
                    f"    result['{name}'] = parts[{idx}].strip() if len(parts) > {idx} else None\n"
                )

            elif bash_format == "part_before_slash":
                parsing_code.append(f"""    if len(parts) > {idx}:
        result['{name}'] = parts[{idx}].split('/')[0].strip() if '/' in parts[{idx}] else parts[{idx}].strip()
""")

            elif bash_format == "part_after_slash":
                parsing_code.append(f"""    if len(parts) > {idx}:
        result['{name}'] = parts[{idx}].split('/')[1].strip() if '/' in parts[{idx}] else parts[{idx}].strip()
""")

            elif bash_format.startswith("csv_split_"):
                split_idx = bash_format.split("_")[-1]
                parsing_code.append(f"""    if len(parts) > {idx}:
        csv_parts = parts[{idx}].split(',')
        result['{name}'] = csv_parts[{split_idx}].strip() if len(csv_parts) > {split_idx} else None
""")

            elif bash_format == "strip_percent":
                parsing_code.append(f"""    if len(parts) > {idx}:
        result['{name}'] = parts[{idx}].rstrip('%').strip()
""")

        parsing_code.append("""
    return result
""")

    # Similar for top_users
    if "top_users" in schema:
        fields = schema["top_users"]["fields"]
        bash_fields = [f for f in fields if f.get("bash_output")]

        parsing_code.append("""
def parse_top_users_line(bash_line: str) -> dict:
    \"\"\"
    Parse single line from TopUsers.sh output.
    Auto-generated from schema definition.
    \"\"\"
    parts = bash_line.strip().split()

    if not parts:
        return {}

    result = {}

""")

        for field in bash_fields:
            idx = field["bash_index"]
            name = field["name"]
            parsing_code.append(
                f"    result['{name}'] = parts[{idx}].strip() if len(parts) > {idx} else None\n"
            )

        parsing_code.append("""
    return result
""")

        parsing_code.append("""
def parse_top_users(bash_output: str) -> list:
    \"\"\"Parse complete TopUsers.sh output.\"\"\"
    lines = [line for line in bash_output.split('\\n') if line.strip()]

    # Skip header lines (first 2 lines with "USERNAME" and "----")
    data_lines = []
    for i, line in enumerate(lines):
        if i < 2:  # Skip first two lines (headers)
            continue
        if '----' in line:  # Skip separator lines
            continue
        data_lines.append(line)

    return [parse_top_users_line(line) for line in data_lines if line.strip()]
""")

    # Write to file
    content = f"""# Generated Bash Output Parser
# Schema Version: {schema["version"]}
# Generated At: {schema["generated_at"]}
# DO NOT EDIT MANUALLY

from typing import Dict, Optional, List

{"".join(parsing_code)}
"""

    with open(output_file, "w") as f:
        f.write(content)

    return [str(output_file)]


if __name__ == "__main__":
    # Test
    import yaml

    with open("../metrics_schema.yaml") as f:
        schema = yaml.safe_load(f)

    schema["generated_at"] = datetime.now().isoformat()
    outputs = generate_parsers(schema)
    print(f"Generated {len(outputs)} files:")
    for output in outputs:
        print(f"  - {output}")
