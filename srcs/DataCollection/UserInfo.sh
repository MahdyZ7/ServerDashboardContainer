#!/bin/bash

get_running_processes() {
  if [ $# -eq 0 ]; then
	echo "Usage: $0 <username>"
	return 1
  fi
  ps -u "$1" -o pid,pcpu,pmem,comm --no-headers | awk '{printf("%s %.2f %.2f %s\n", $1, $2, $3, $4)}'
}

get_running_processes $1


