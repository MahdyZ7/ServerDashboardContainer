# Quick Reference Guide

**Schema Version:** 1.0.0
**Generated:** 2025-11-05T00:11:46.315719

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
