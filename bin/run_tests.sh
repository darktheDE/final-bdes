#!/bin/bash
# ==============================================================================
# Food & Restaurant Sentiment Analysis System — Automated Test Runner
#
# Usage:
#   bash bin/run_tests.sh
# ==============================================================================

set -e

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${BASE_DIR}"

echo "==================================================="
echo " Food & Restaurant Sentiment Analysis - Test Runner"
echo " Environment: Ubuntu 24.04 WSL2 LTS"
echo "==================================================="

# ── Environment setup ─────────────────────────────────────────────────────────
export JAVA_HOME="/usr/lib/jvm/java-1.8.0-openjdk-amd64"
export HADOOP_HOME="/usr/local/hadoop"
export HIVE_HOME="/usr/local/hive"
export PATH="${JAVA_HOME}/bin:${PATH}:${HADOOP_HOME}/bin:${HADOOP_HOME}/sbin:${HIVE_HOME}/bin"

# ── Activate Python venv ──────────────────────────────────────────────────────
VENV_DIR="${BASE_DIR}/venv"
if [ ! -f "${VENV_DIR}/bin/activate" ]; then
    echo "[!] Virtual environment not found at ${VENV_DIR}."
    echo "    Please run Setup Script first: ./bin/install_infra.sh or bash bin/setup.sh"
    exit 1
fi

source "${VENV_DIR}/bin/activate"

# ── Run the Python Integration test suite ─────────────────────────────────────
python tests/test_all_components.py

# ── Deactivate venv ───────────────────────────────────────────────────────────
deactivate
