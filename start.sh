#!/bin/bash
# Start Futu OpenD and the HSI collector (both in background via screen)
# Usage: bash start.sh

set -e
cd "$(dirname "$0")"

# Load environment variables
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
else
  echo "ERROR: .env file not found. Copy .env.example and fill in values."
  exit 1
fi

echo "=== Starting Futu OpenD ==="
screen -dmS futud /opt/futud/FutuOpenD /opt/futud/FutuOpenD.xml
echo "Futu OpenD started in screen session 'futud'"
sleep 5   # Give OpenD time to connect

echo "=== Starting HSI Collector ==="
source venv/bin/activate
screen -dmS hsi-collector python main.py
echo "Collector started in screen session 'hsi-collector'"

echo ""
echo "Running sessions:"
screen -ls

echo ""
echo "Useful commands:"
echo "  screen -r futud          # Attach to Futu OpenD"
echo "  screen -r hsi-collector  # Attach to collector (Ctrl+A, D to detach)"
echo "  python query.py          # View today's signals"
