#!/bin/bash
# ==============================================================================
# Food & Restaurant Sentiment Analysis System
# Local Database Ingestion & Initialization Script
# ==============================================================================

set -e

# Detect base directory of the project (parent of bin/)
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "======================================================================"
# Activate virtual environment
if [ -f "${BASE_DIR}/venv/bin/activate" ]; then
    echo "[*] Activating Python virtual environment..."
    source "${BASE_DIR}/venv/bin/activate"
else
    echo "[!] Warning: virtual environment not found at ${BASE_DIR}/venv."
    echo "    Attempting to run using system python..."
fi

# Initialize database schemas with seed data
echo -e "\n[*] Importing offline TripAdvisor data to MongoDB..."
python "${BASE_DIR}/src/ingest/import_tripadvisor.py"

echo -e "\n[*] Loading offline meals data to MongoDB..."
python "${BASE_DIR}/src/crawler/fetch_mealdb.py"

echo -e "\n[*] Running init_db.py to initialize MySQL schema and migrate data..."
python "${BASE_DIR}/src/ingest/init_db.py"

echo -e "\n======================================================================"
echo "[+] Local data ingestion and database initialization complete!"
echo "======================================================================"
