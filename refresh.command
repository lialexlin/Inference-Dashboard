#!/bin/bash
# Double-click this file to refresh all the dashboard's data.
# Takes about five minutes.

set -e
cd "$(dirname "$0")"

echo ""
echo "  Refreshing data — this takes about five minutes..."
echo ""

doppler run -- uv run python -m jobs.refresh

echo ""
echo "  Done. You can close this window."
echo ""
sleep 3
