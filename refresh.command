#!/bin/bash
# Double-click this file to refresh the data (prices + RSS + EDGAR).
# Takes ~30 seconds. Window will close itself when done.

set -e
cd "$(dirname "$0")"

echo ""
echo "  Refreshing data — this takes ~30 seconds..."
echo ""

python3 -m jobs.refresh

echo ""
echo "  Done. You can close this window."
echo ""
sleep 3
