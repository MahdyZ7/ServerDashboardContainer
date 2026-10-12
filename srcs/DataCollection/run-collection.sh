#!/usr/bin/env bash
# Cron entry point: run-collection.sh <job-name> [VAR=value...]
# Loads the container environment from PID 1 (cron starts jobs with an empty
# environment) without word-splitting values, then runs one backend.py
# execution. A job is skipped while the previous run of the same job is active.

job="$1"
shift

while IFS= read -r -d '' entry; do
	export "$entry"
done < /proc/1/environ

cd /app || exit 1
flock -n -E 75 "/tmp/datacollection-${job}.lock" env "$@" EXECUTION_MODE=scheduled uv run backend.py
status=$?
if [ $status -eq 75 ]; then
	echo "[$(date '+%d-%B-%Y %H:%M:%S')] WARNING [run-collection] - previous '${job}' run still active, skipping"
fi
exit $status
