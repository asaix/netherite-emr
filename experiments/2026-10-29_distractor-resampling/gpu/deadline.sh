#!/usr/bin/env bash
set -uo pipefail
MACHINE_ID=$1
DEADLINE_EPOCH=$2
python3 -m pip install -q jarvislabs > /dev/null 2>&1
command -v jl > /dev/null || { echo "jl not installed on the VM; deadline guard not active"; exit 1; }
echo "deadline guard active: pausing $MACHINE_ID at $(date -d @"$DEADLINE_EPOCH")"
while [ "$(date +%s)" -lt "$DEADLINE_EPOCH" ]; do sleep 60; done
echo "deadline reached $(date); pausing $MACHINE_ID"
jl pause "$MACHINE_ID" --yes
