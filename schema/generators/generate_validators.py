#!/usr/bin/env python3
"""
Generate validation functions from schema definition.
This replaces manual validation in validation.py.
"""

from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime


def generate_validators(schema: Dict[str, Any]) -> List[str]:
    """Generate validation functions for all fields."""

    # Base path relative to this script
    base_path = Path(__file__).parent.parent.parent / "srcs" / "Frontend" / "generated"
    base_path.mkdir(parents=True, exist_ok=True)

    output_file = base_path / "validators.py"

    validator_code = [
        f"""# Generated Validators
# Schema Version: {schema["version"]}
# Generated At: {schema["generated_at"]}
# DO NOT EDIT MANUALLY

from typing import Any, Optional
from datetime import datetime
import re

class ValidationError(Exception):
    \"\"\"Validation error exception.\"\"\"
    pass

"""
    ]

    # Generate base validator functions
    seen_validators = set()

    for table_key in ["server_metrics", "top_users"]:
        if table_key in schema:
            for field in schema[table_key]["fields"]:
                if "validation" in field:
                    val_type = field["validation"]["type"]

                    if val_type in seen_validators:
                        continue
                    seen_validators.add(val_type)

                    if val_type == "percentage":
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

                    elif val_type == "integer":
                        validator_code.append("""
def validate_integer(value: Any, field_name: str = 'field', min_val: Optional[int] = None, max_val: Optional[int] = None) -> int:
    \"\"\"Validate integer with optional min/max.\"\"\"
    try:
        val = int(value)
        if min_val is not None and val < min_val:
            raise ValidationError(f"{field_name} must be >= {min_val}, got {val}")
        if max_val is not None and val > max_val:
            raise ValidationError(f"{field_name} must be <= {max_val}, got {val}")
        return val
    except (ValueError, TypeError):
        raise ValidationError(f"{field_name} must be an integer, got {type(value).__name__}")

""")

                    elif val_type == "float":
                        validator_code.append("""
def validate_float(value: Any, field_name: str = 'field', min_val: Optional[float] = None, max_val: Optional[float] = None) -> float:
    \"\"\"Validate float with optional min/max.\"\"\"
    try:
        val = float(value)
        if min_val is not None and val < min_val:
            raise ValidationError(f"{field_name} must be >= {min_val}, got {val}")
        if max_val is not None and val > max_val:
            raise ValidationError(f"{field_name} must be <= {max_val}, got {val}")
        return val
    except (ValueError, TypeError):
        raise ValidationError(f"{field_name} must be a number, got {type(value).__name__}")

""")

                    elif val_type == "string":
                        validator_code.append("""
def validate_string(value: Any, field_name: str = 'field', max_length: Optional[int] = None) -> str:
    \"\"\"Validate string with optional max length.\"\"\"
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string, got {type(value).__name__}")
    if max_length is not None and len(value) > max_length:
        raise ValidationError(f"{field_name} exceeds max length {max_length}")
    return value

""")

    # Generate field-specific validators
    validator_code.append("\n# Field-specific validators\n")

    for table_key in ["server_metrics", "top_users"]:
        if table_key in schema:
            class_name = "".join(word.capitalize() for word in table_key.split("_"))
            validator_code.append(f"\nclass {class_name}Validator:\n")
            validator_code.append(f'    """Validator for {table_key} fields."""\n\n')

            for field in schema[table_key]["fields"]:
                if "validation" in field:
                    field_name = field["name"]
                    val_type = field["validation"]["type"]

                    validator_code.append("    @staticmethod\n")
                    validator_code.append(
                        f"    def validate_{field_name}(value: Any) -> Any:\n"
                    )
                    validator_code.append(
                        f'        """Validate {field.get("description", field_name)}."""\n'
                    )

                    if val_type == "percentage":
                        validator_code.append(
                            f"        return validate_percentage(value, '{field_name}')\n\n"
                        )
                    elif val_type == "integer":
                        min_val = field["validation"].get("min")
                        max_val = field["validation"].get("max")
                        validator_code.append(
                            f"        return validate_integer(value, '{field_name}', {min_val}, {max_val})\n\n"
                        )
                    elif val_type == "float":
                        min_val = field["validation"].get("min")
                        max_val = field["validation"].get("max")
                        validator_code.append(
                            f"        return validate_float(value, '{field_name}', {min_val}, {max_val})\n\n"
                        )
                    elif val_type == "string":
                        max_length = field["validation"].get("max_length")
                        validator_code.append(
                            f"        return validate_string(value, '{field_name}', {max_length})\n\n"
                        )

    # Write to file
    with open(output_file, "w") as f:
        f.write("".join(validator_code))

    return [str(output_file)]


if __name__ == "__main__":
    # Test
    import yaml

    with open("../metrics_schema.yaml") as f:
        schema = yaml.safe_load(f)

    schema["generated_at"] = datetime.now().isoformat()
    outputs = generate_validators(schema)
    print(f"Generated {len(outputs)} files:")
    for output in outputs:
        print(f"  - {output}")
