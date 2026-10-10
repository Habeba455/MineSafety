#!/usr/bin/env bash
set -euo pipefail

cd /workspace
mkdir -p /workspace/output/analysis

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

python3 "${SCRIPT_DIR}/solve.py"

test -s /workspace/output/recommendation.md
test -s /workspace/output/analysis/summary.csv
test -s /workspace/output/analysis/sensitivity.csv
test -s /workspace/output/analysis/data_quality.json

echo "Oracle solution completed successfully."
