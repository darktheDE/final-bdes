#!/bin/bash
set -e

# Base directory setup
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$BASE_DIR"

echo "==================================================="
echo " Starting Food & Restaurant Sentiment Analysis System"
echo " Environment: Ubuntu 24.04 WSL2 LTS"
echo "==================================================="

# 1. Export environment variables
export JAVA_HOME="/usr/lib/jvm/java-11-openjdk-amd64"
export HADOOP_HOME="/usr/local/hadoop"
export PATH="$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin"

# 2. Port and service availability verification
echo "[1/4] Checking ports and services..."

check_port() {
    local port=$1
    local name=$2
    if ss -tln | grep -q ":$port "; then
        echo "  -> Port $port ($name) is active."
        return 0
    else
        echo "  -> Port $port ($name) is NOT active."
        return 1
    fi
}

# 3. Boot DB and Hadoop Services
echo -e "\n[2/4] Starting relational, NoSQL, and Big Data services..."

# MySQL
echo "  -> Starting MySQL..."
sudo service mysql start || echo "    [!] Could not start MySQL daemon."

# MongoDB
echo "  -> Starting MongoDB..."
sudo service mongod start || echo "    [!] Could not start MongoDB daemon."

# Hadoop DFS
if ! check_port 9000 "HDFS NameNode" &> /dev/null; then
    echo "  -> Starting Hadoop DFS..."
    "${HADOOP_HOME}/sbin/start-dfs.sh"
else
    echo "  -> Hadoop DFS is already running."
fi

# Hadoop YARN
if ! check_port 8088 "YARN ResourceManager" &> /dev/null; then
    echo "  -> Starting Hadoop YARN..."
    "${HADOOP_HOME}/sbin/start-yarn.sh"
else
    echo "  -> Hadoop YARN is already running."
fi

# Verify final port status
echo "--- Service Port Summary ---"
check_port 3306 "MySQL" || true
check_port 27017 "MongoDB" || true
check_port 9000 "HDFS NameNode" || true
check_port 10000 "HiveServer2" || true
echo "----------------------------"

# 4. Activate environment & run data pipelines
echo -e "\n[3/4] Activating virtual environment & running ingestion pipelines..."
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "[!] Error: Virtual environment (venv) not found. Please run ./bin/setup.sh first."
    exit 1
fi

# Run TheMealDB crawling
echo "  -> Executing TheMealDB ingestion script..."
python src/crawler/fetch_mealdb.py

# Run TripAdvisor crawl
echo "  -> Executing TripAdvisor scraper (limit reviews count, offline tolerant)..."
# Scrapy project requires moving to its folder
cd src/crawler/tripadvisor_job
scrapy crawl tripadvisor || echo "    [!] Scrapy crawler encountered an error or was skipped."
cd "$BASE_DIR"

# Run HDFS sync pipelines
echo -e "\n[4/4] Executing HDFS synchronization pipelines..."
if [ -f "src/ingest/mongo_to_hdfs.py" ]; then
    echo "  -> Syncing MongoDB raw to HDFS..."
    python src/ingest/mongo_to_hdfs.py
fi

if [ -f "src/ingest/mysql_to_hdfs.py" ]; then
    echo "  -> Syncing MySQL relational tables to HDFS..."
    python src/ingest/mysql_to_hdfs.py
fi

# 5. Launch Streamlit Web Application
echo -e "\n==================================================="
echo " Launching Streamlit Web App..."
echo " Open http://localhost:8501 on your Windows browser."
echo " "
echo " Note: To activate this virtual environment in your terminal shell, run:"
echo "   source venv/bin/activate"
echo "==================================================="


if [ -f "src/streamlit_app/app.py" ]; then
    streamlit run src/streamlit_app/app.py
else
    # Create empty dashboard app placeholder if not exists yet
    echo "  -> No app.py found yet. Launching placeholder app..."
    mkdir -p src/streamlit_app
    cat << 'EOF' > src/streamlit_app/app.py
import streamlit as st
st.title("Food & Restaurant Sentiment Analysis Dashboard")
st.info("Dashboard is currently under construction. Cycle 5 tasks will complete the UI layout.")
EOF
    streamlit run src/streamlit_app/app.py
fi
