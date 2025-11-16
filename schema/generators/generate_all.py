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
            with open(self.schema_path, "r") as f:
                schema = yaml.safe_load(f)

            # Add generation timestamp
            schema["generated_at"] = datetime.now().isoformat()

            return schema
        except Exception as e:
            print(f"❌ Error loading schema: {e}")
            sys.exit(1)

    def validate_schema(self) -> bool:
        """Validate schema structure and consistency."""
        print("🔍 Validating schema...")

        errors = []

        # Check required top-level keys
        required_keys = ["version", "server_metrics", "top_users"]
        for key in required_keys:
            if key not in self.schema:
                errors.append(f"Missing required key: {key}")

        # Validate server_metrics fields
        if "server_metrics" in self.schema:
            fields = self.schema["server_metrics"].get("fields", [])
            bash_indices = []

            for field in fields:
                # Check required field properties
                if "name" not in field:
                    errors.append(f"Field missing 'name' property: {field}")
                    continue

                if "type" not in field:
                    errors.append(f"Field '{field['name']}' missing 'type' property")

                # Check for duplicate bash_index (allow if different bash_format)
                if field.get("bash_output") and "bash_index" in field:
                    idx = field["bash_index"]
                    fmt = field.get("bash_format", "raw")
                    key = (idx, fmt)
                    if key in bash_indices:
                        errors.append(
                            f"Duplicate bash_index {idx} with format '{fmt}' for field '{field['name']}'"
                        )
                    bash_indices.append(key)

        # Validate top_users fields
        if "top_users" in self.schema:
            fields = self.schema["top_users"].get("fields", [])
            for field in fields:
                if "name" not in field or "type" not in field:
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
            targets = ["sql", "python", "typescript", "validators", "parsers", "docs"]

        success = True

        print(
            f"\n🚀 Generating code from schema (version {self.schema['version']})...\n"
        )

        if "sql" in targets:
            print("📊 Generating SQL migration...")
            try:
                sql_file = generate_sql_migration(self.schema)
                self.generated_files.append(sql_file)
                print(f"   ✅ Generated: {sql_file}")
            except Exception as e:
                print(f"   ❌ Failed: {e}")
                import traceback

                traceback.print_exc()
                success = False

        if "python" in targets:
            print("🐍 Generating Python models...")
            try:
                py_files = generate_python_models(self.schema)
                self.generated_files.extend(py_files)
                print(f"   ✅ Generated {len(py_files)} files")
            except Exception as e:
                print(f"   ❌ Failed: {e}")
                import traceback

                traceback.print_exc()
                success = False

        if "typescript" in targets:
            print("📘 Generating TypeScript types...")
            try:
                ts_files = generate_typescript_types(self.schema)
                self.generated_files.extend(ts_files)
                print(f"   ✅ Generated {len(ts_files)} files")
            except Exception as e:
                print(f"   ❌ Failed: {e}")
                import traceback

                traceback.print_exc()
                success = False

        if "validators" in targets:
            print("✔️  Generating validators...")
            try:
                validator_files = generate_validators(self.schema)
                self.generated_files.extend(validator_files)
                print(f"   ✅ Generated {len(validator_files)} files")
            except Exception as e:
                print(f"   ❌ Failed: {e}")
                import traceback

                traceback.print_exc()
                success = False

        if "parsers" in targets:
            print("🔧 Generating parsers...")
            try:
                parser_files = generate_parsers(self.schema)
                self.generated_files.extend(parser_files)
                print(f"   ✅ Generated {len(parser_files)} files")
            except Exception as e:
                print(f"   ❌ Failed: {e}")
                import traceback

                traceback.print_exc()
                success = False

        if "docs" in targets:
            print("📚 Generating documentation...")
            try:
                doc_files = generate_documentation(self.schema)
                self.generated_files.extend(doc_files)
                print(f"   ✅ Generated {len(doc_files)} files")
            except Exception as e:
                print(f"   ❌ Failed: {e}")
                import traceback

                traceback.print_exc()
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

        if "server_metrics" in self.schema:
            fields = self.schema["server_metrics"].get("fields", [])
            bash_fields = [f for f in fields if f.get("bash_output")]
            print(
                f"Server Metrics: {len(fields)} fields ({len(bash_fields)} from bash)"
            )

        if "top_users" in self.schema:
            fields = self.schema["top_users"].get("fields", [])
            bash_fields = [f for f in fields if f.get("bash_output")]
            print(f"Top Users: {len(fields)} fields ({len(bash_fields)} from bash)")

        if "api_endpoints" in self.schema:
            endpoints = self.schema.get("api_endpoints", [])
            print(f"API Endpoints: {len(endpoints)}")

        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Generate code from schema definition")
    parser.add_argument(
        "--schema", default="../metrics_schema.yaml", help="Path to schema YAML file"
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate schema, do not generate",
    )
    parser.add_argument(
        "--target",
        default="all",
        help="Comma-separated list of targets to generate (sql,python,typescript,validators,parsers,docs)",
    )
    parser.add_argument("--summary", action="store_true", help="Show schema summary")

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
    targets = None if args.target == "all" else args.target.split(",")

    # Generate code
    success = generator.generate_all(targets)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
