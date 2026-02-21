#!/bin/bash

# Navigate to the script's directory
cd "$(dirname "$0")"

# Check if .venv exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Install requirements if needed
echo "Verifying dependencies..."
.venv/bin/pip install -r requirements.txt -q

# Check for --web flag
if [ "$1" = "--web" ]; then
    PORT="${2:-8080}"
    echo "--------------------------------------------------------"
    echo "  Starting dwfx2pdf Web Interface"
    echo "  Open http://localhost:$PORT in your browser"
    echo "--------------------------------------------------------"
    .venv/bin/python dwfx_to_pdf.py web --port "$PORT"
else
    echo "--------------------------------------------------------"
    echo "  Starting dwfx2pdf in Watch Mode."
    echo "  Drop your .dwfx files into the 'dwfx' folder."
    echo "  Tip: Run './run.sh --web' for the web interface."
    echo "--------------------------------------------------------"
    .venv/bin/python dwfx_to_pdf.py watch --dwfx-dir ./dwfx --pdf-dir ./pdf
fi
