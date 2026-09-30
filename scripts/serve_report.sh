#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REPORT_DIR="$PROJECT_ROOT/report"

if [[ ! -f "$REPORT_DIR/resnet50_report.html" ]]; then
    echo "ERROR: report does not exist."
    echo "Run:"
    echo "  ./scripts/run_benchmark.sh"
    exit 1
fi

cd "$REPORT_DIR"

echo
echo "Serving benchmark report:"
echo
echo "  http://127.0.0.1:8000/resnet50_report.html"
echo
echo "Press Ctrl+C to stop the server."
echo

exec python3 -m http.server 8000 --bind 0.0.0.0
