#!/usr/bin/env bash
# Runs every model (or the ones named as arguments) through NuSMV.
# Override the binary with NUSMV=/path/to/NuSMV ./check.sh
set -uo pipefail

NUSMV="${NUSMV:-NuSMV}"
cd "$(dirname "$0")" || exit 1

if ! command -v "$NUSMV" >/dev/null 2>&1 && [ ! -x "$NUSMV" ]; then
    echo "NuSMV not found. Set NUSMV=/path/to/NuSMV" >&2
    exit 1
fi

models=("$@")
[ ${#models[@]} -eq 0 ] && models=(*.smv)

status=0
for model in "${models[@]}"; do
    echo "=============================================================="
    echo "  $model"
    echo "=============================================================="
    "$NUSMV" "$model" || status=1
    echo
done
exit $status
