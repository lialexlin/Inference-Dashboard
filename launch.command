#!/bin/bash
# Double-click this file to launch the dashboard.
# Starts a local web server, opens your browser, and keeps the Terminal
# window open until you close it (or press Ctrl+C).

set -e
cd "$(dirname "$0")"

PORT=8765
while lsof -i :"$PORT" >/dev/null 2>&1; do PORT=$((PORT+1)); done
URL="http://localhost:$PORT"

echo ""
echo "  ┌─────────────────────────────────────────────────┐"
echo "  │  Inference Stack Dashboard                       │"
echo "  │  $URL"
echo "  │                                                  │"
echo "  │  Close this window or press Ctrl+C to stop.      │"
echo "  └─────────────────────────────────────────────────┘"
echo ""

(sleep 1 && open "$URL") &
exec python3 -m http.server "$PORT"
