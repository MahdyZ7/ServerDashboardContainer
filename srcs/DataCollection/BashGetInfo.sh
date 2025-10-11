#!/usr/bin/env bash

if [ $# -lt 4 ]; then
	echo "Usage: $0 <hostname> <username> <password> <script>"
	exit 1
fi

sshpass -p "$3" ssh -o "StrictHostKeyChecking accept-new" -oHostKeyAlgorithms=+ssh-rsa -oPubkeyAcceptedKeyTypes=+ssh-rsa "$2"@"$1" "bash -s" < "$4" -- "${@:5}"
# sshpass -p "$3" ssh "$2@$1" "echo Password | sudo -S dnf update"