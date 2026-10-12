#!/usr/bin/env bash
# Run a local script on a remote host: BashGetInfo.sh <host> <username> <script> [script args...]
#
# Credentials come from the environment, never the command line:
#   SSH_KEY_FILE  private key (preferred, see Docs/Project-Overview/SSH_KEY_MIGRATION.md)
#   SSHPASS       password, passed to sshpass -e
# Exit status 255 means the SSH connection itself failed; sshpass uses 5 for a wrong password.

if [ $# -lt 3 ]; then
	echo "Usage: $0 <hostname> <username> <script> [args...]" >&2
	exit 1
fi

host="$1" user="$2" script="$3"
shift 3

ssh_opts=(
	-o "StrictHostKeyChecking=accept-new"
	-o "ConnectTimeout=10"
	-o "ServerAliveInterval=15"
	-o "ServerAliveCountMax=3"
	-o "HostKeyAlgorithms=+ssh-rsa"
	-o "PubkeyAcceptedKeyTypes=+ssh-rsa"
)

# The remote side re-splits the command string, so quote every argument
remote_cmd="bash -s --"
for arg in "$@"; do
	remote_cmd+=" $(printf '%q' "$arg")"
done

if [ -n "${SSH_KEY_FILE:-}" ]; then
	exec ssh -i "$SSH_KEY_FILE" -o BatchMode=yes "${ssh_opts[@]}" "$user@$host" "$remote_cmd" < "$script"
elif [ -n "${SSHPASS:-}" ]; then
	exec sshpass -e ssh "${ssh_opts[@]}" "$user@$host" "$remote_cmd" < "$script"
else
	echo "No credentials: set SSH_KEY_FILE or SSHPASS" >&2
	exit 1
fi
