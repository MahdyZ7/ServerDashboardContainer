# Code Review Fix Plan

Last reviewed: 2026-05-04

This plan tracks fixes from the current code and documentation review. It is ordered by risk and expected impact for a student-facing server status dashboard.

## Goals

- Make server status accurate and trustworthy for students.
- Remove security risks around SSH credentials and exposed API behavior.
- Align schema, migrations, generated docs, and runtime code.
- Improve dashboard usability on desktop and mobile.
- Add enough tests to catch regressions in collection, API responses, and UI behavior.

## Phase 0: Safety And Baseline

- [ ] Capture current running behavior with screenshots of all dashboard tabs.
- [ ] Export a sample `/api/servers/metrics/latest` response for test fixtures.
- [ ] Export a sample `/api/system/overview` response for test fixtures.
- [ ] Dump current PostgreSQL table definitions with `\d server_metrics` and `\d top_users`.
- [ ] Confirm whether production uses the Compose cron mode or a separate scheduler.
- [ ] Confirm the required supported remote Linux distributions.

## Phase 1: Critical Security Fixes

- [ ] Replace password-based SSH collection with SSH key authentication.
- [ ] Stop passing SSH passwords as command-line arguments to `BashGetInfo.sh`.
- [ ] Pin known hosts instead of relying on `StrictHostKeyChecking accept-new`.
- [ ] Remove legacy `ssh-rsa` algorithm overrides unless a documented target server still requires them.
- [ ] Restrict Flask CORS to the dashboard origin instead of enabling unrestricted CORS.
- [ ] Require `SECRET_KEY` in production and fail startup if it is missing or still set to the dev default.
- [ ] Stop returning raw exception strings in API JSON responses.
- [ ] Add HTTPS or place the dashboard behind a TLS-terminating reverse proxy before student use.
- [ ] Document the SSH key setup flow in `Docs/Project-Overview/SSH_KEY_MIGRATION.md`.

## Phase 2: Schema And Database Correctness

- [ ] Choose one source of truth for schema creation: generated SQL migrations or `DataCollection/backend.py`.
- [ ] Regenerate valid migrations from `schema/metrics_schema.yaml`.
- [ ] Fix invalid SQL comments in `srcs/Backend/migrations/20251105_001146_schema_migration.sql`.
- [ ] Align column names across schema YAML, generated docs, generated models, `backend.py`, and API queries.
- [ ] Add indexes for latest and historical dashboard queries:
  - [ ] `server_metrics(server_name, timestamp DESC)`
  - [ ] `server_metrics(timestamp DESC)`
  - [ ] `top_users(server_name, cpu DESC)`
- [ ] Add a deterministic latest-row query using `ROW_NUMBER()` to avoid duplicate rows on timestamp ties.
- [ ] Validate and cap historical `hours` values to a safe range, for example 1 to 168.
- [ ] Decide whether `top_users` is current-state only or historical data.
- [ ] If historical top-user data is needed, remove the current `UNIQUE(server_name, username)` current-state overwrite model or split into two tables.
- [ ] Add a migration application step to container startup or deployment documentation.

## Phase 3: Status Accuracy And Data Collection Reliability

- [ ] Make stale/offline detection take priority over warning thresholds everywhere.
- [ ] Centralize server status calculation so API and frontend use the same rules.
- [ ] Make thresholds configurable in one place and document defaults.
- [ ] Replace raw comma-separated monitoring output with JSON or properly quoted CSV.
- [ ] Harden `parse_monitoring_data()` against missing fields, commas in OS strings, and invalid numeric data.
- [ ] Harden `parse_top_users()` against names or GECOS values with spaces.
- [ ] Fix physical CPU detection for systems where `/proc/cpuinfo` has no `physical id`.
- [ ] Handle missing commands on remote servers, especially `lsof`, `ip`, `lsb_release`, `last`, and `du`.
- [ ] Add command timeouts to SSH script execution.
- [ ] Store collection failures per server so the UI can show "collection failed" instead of only stale data.
- [ ] Convert network byte counters to rates for charts, or label them clearly as cumulative counters.

## Phase 4: API And Backend Maintainability

- [ ] Split database access into a small repository module instead of duplicating connection/query handling in route functions.
- [ ] Remove or clearly mark `srcs/Backend/api.py` as legacy if it is not started by Compose.
- [ ] Add request validation for server names and time ranges.
- [ ] Return consistent error envelopes with safe user-facing messages and internal log IDs.
- [ ] Use timezone-aware timestamps consistently.
- [ ] Add health checks that verify database connectivity, not just Flask process availability.
- [ ] Add structured logging with server name, collection cycle ID, and request path.

## Phase 5: Frontend And UX Improvements

- [ ] Make the overview answer "Which server should I use now?" with a recommended server card.
- [ ] Sort server cards by health and available capacity.
- [ ] Show per-server freshness, for example "Collected 12 minutes ago".
- [ ] Add explicit "stale data" and "collection failed" visual states.
- [ ] Use green consistently for online/success and keep KU blue for brand/navigation.
- [ ] Fix the performance rating formula so CPU, RAM, and disk are normalized percentages.
- [ ] Register dashboard event listeners once to avoid duplicate chart loads and duplicate toasts.
- [ ] Fix tab ARIA references by adding matching `id` attributes to tab buttons.
- [ ] Improve mobile user activity view with card layout, sticky first column, or real pagination.
- [ ] Add empty states for analytics and network panels when no servers are available.
- [ ] Bundle Chart.js, Font Awesome, and fonts locally for reliability on restricted campus networks.
- [ ] Add a visible "last collection" timestamp and "next refresh" timestamp in the header or footer.

## Phase 6: Tests And Quality Gates

- [ ] Add Python unit tests for monitoring parsers.
- [ ] Add Flask API tests using a test database or mocked repository layer.
- [ ] Add SQL migration smoke tests.
- [ ] Add JavaScript unit tests for status calculation, formatting, filters, and chart data shaping.
- [ ] Add one browser smoke test that loads the dashboard and switches every tab.
- [ ] Add shell linting for `BashGetInfo.sh`, `mini_monitering.sh`, `TopUsers.sh`, and `start-cron.sh`.
- [ ] Add CI or a documented local quality command that runs all available tests and linters.
- [ ] Update README testing section after tests exist.

## Phase 7: Documentation Cleanup

- [ ] Keep `README.md` as the source for the current runtime architecture.
- [ ] Keep `Docs/INDEX.md` as the navigation source for documentation.
- [ ] Mark historical docs as historical when they describe removed Dash/Nginx/frontend-container architecture.
- [ ] Update generated docs after schema reconciliation.
- [ ] Add an operator runbook for common production tasks:
  - [ ] Rotate SSH keys.
  - [ ] Add a monitored server.
  - [ ] Recover from database connection failure.
  - [ ] Check collection freshness.
  - [ ] Run retention cleanup.
- [ ] Fix spelling in directory names if safe, especially `DesginGuideLine`.

## Suggested Implementation Order

1. Security and credentials.
2. Schema and migration reconciliation.
3. Status correctness and parser hardening.
4. UI event-handler and performance-score bugs.
5. Student-centered overview UX.
6. Tests and CI.
7. Historical documentation cleanup.

## Definition Of Done

- [ ] Students can identify an available server within five seconds on desktop and mobile.
- [ ] Offline and stale data cannot appear as healthy.
- [ ] No server passwords are passed through process arguments.
- [ ] Database schema is created through one documented path.
- [ ] API responses are safe, bounded, and consistently shaped.
- [ ] Dashboard refreshes do not duplicate event handlers.
- [ ] Current README, docs index, generated schema docs, and running code agree.
