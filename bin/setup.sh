#!/bin/bash
set -e

# Base directory setup
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$BASE_DIR"

echo "==================================================="
echo " Setting up Food & Restaurant Sentiment Analysis"
echo " Environment: Ubuntu 24.04 WSL2 LTS"
echo "==================================================="

# 1. Verify basic utilities
echo "[1/4] Verifying and installing basic system utilities..."

# Update package list helper
update_apt() {
    echo "  -> Updating package lists..."
    sudo apt-get update
}

if ! command -v python3 &> /dev/null; then
    echo "  -> python3 is not installed. Installing python3..."
    update_apt
    sudo apt-get install -y python3
fi

# Ensure python3-venv is installed (often missing on minimal Ubuntu installations)
if ! dpkg -l | grep -q "python3-venv"; then
    echo "  -> python3-venv is not installed. Installing python3-venv..."
    update_apt
    sudo apt-get install -y python3-venv
fi

if ! command -v pip3 &> /dev/null; then
    echo "  -> pip3 is not installed. Installing python3-pip..."
    update_apt
    sudo apt-get install -y python3-pip
fi

if ! command -v java &> /dev/null; then
    echo "  -> java (JVM) is not installed. Installing OpenJDK 11..."
    update_apt
    sudo apt-get install -y openjdk-11-jdk
fi


echo "  -> python3: $(python3 -V)"
echo "  -> java: $(java -version 2>&1 | head -n 1)"

# 2. Setup Python virtual environment
echo -e "\n[2/4] Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    echo "  -> Creating venv using python3..."
    python3 -m venv venv
else
    echo "  -> venv directory already exists."
fi

# Activate venv and install dependencies
echo "  -> Activating virtual environment..."
source venv/bin/activate

echo "  -> Installing Python dependencies from requirements.txt..."
pip install --upgrade pip
pip install -r requirements.txt

# 3. Verify Database Services
echo -e "\n[3/4] Checking databases (MySQL & MongoDB)..."

# Check if MySQL is running
if ! pgrep mysql > /dev/null; then
    echo "  -> MySQL is not running. Attempting to start service..."
    sudo service mysql start || echo "    [!] Warning: Failed to start MySQL. Please start it manually: sudo service mysql start"
fi

# Check if MongoDB is running
if ! pgrep mongod > /dev/null; then
    echo "  -> MongoDB is not running. Attempting to start service..."
    sudo service mongod start || echo "    [!] Warning: Failed to start MongoDB. Please start it manually: sudo service mongod start"
fi

# 4. Initialize Database Schemas & Seed Migration
echo -e "\n[4/4] Initializing Database Schema and migrating seed data..."
python src/ingest/init_db.py

echo "==================================================="
echo " Setup Completed successfully!"
echo " "
echo " To activate the virtual environment in your current terminal session, run:"
echo "   source venv/bin/activate"
echo " "
echo " Start the system by running: ./bin/run.sh"
echo "==================================================="
