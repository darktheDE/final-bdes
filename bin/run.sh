#!/bin/bash
# ==============================================================================
# Food & Restaurant Sentiment Analysis System — Pipeline Runner
#
# Usage:
#   ./bin/run.sh                  # Start all services + launch Streamlit
#   ./bin/run.sh --crawl          # Crawl fresh data → ingest → launch Streamlit
#   ./bin/run.sh --jobs           # Run all 8 MapReduce jobs then launch Streamlit
#   ./bin/run.sh --crawl --jobs   # Full pipeline: crawl + ingest + MR + Streamlit
#
# Prerequisites: Run ./bin/install_infra.sh once on a clean machine first.
# ==============================================================================

set -e

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${BASE_DIR}"

echo "==================================================="
echo " Food & Restaurant Sentiment Analysis System"
echo " Environment: Ubuntu 24.04 WSL2 LTS"
echo "==================================================="

# ── Parse flags ───────────────────────────────────────────────────────────────
CRAWL=false
RUN_JOBS=false
for arg in "$@"; do
    case "${arg}" in
        --crawl) CRAWL=true ;;
        --jobs)  RUN_JOBS=true ;;
        --help|-h)
            echo ""
            echo "Usage: ./bin/run.sh [--crawl] [--jobs]"
            echo ""
            echo "  --crawl   Fetch fresh data from TripAdvisor & TheMealDB,"
            echo "            then normalize into MongoDB and MySQL."
            echo "  --jobs    Run all 8 MapReduce analytical jobs on Hadoop YARN"
            echo "            (requires data already loaded in HDFS)."
            echo ""
            exit 0
            ;;
    esac
done

# ── Environment setup ─────────────────────────────────────────────────────────
# Force Java 8 via JAVA_HOME — overrides any system default (e.g., Java 11)
# Use the canonical symlink path from: update-java-alternatives -l
export JAVA_HOME="/usr/lib/jvm/java-1.8.0-openjdk-amd64"
export HADOOP_HOME="/usr/local/hadoop"
export HIVE_HOME="/usr/local/hive"
export HADOOP_CLIENT_OPTS="-Xmx1024m $HADOOP_CLIENT_OPTS"
# Prepend JAVA_HOME/bin so it takes priority over system java in PATH
export PATH="${JAVA_HOME}/bin:${PATH}:${HADOOP_HOME}/bin:${HADOOP_HOME}/sbin:${HIVE_HOME}/bin"
# Add HCatalog jar to HADOOP_CLASSPATH so JsonSerDe is available in YARN MR tasks
export HADOOP_CLASSPATH="${HIVE_HOME}/lib/hive-hcatalog-core-3.1.3.jar:${HIVE_HOME}/lib/hive-exec-3.1.3.jar:${HADOOP_CLASSPATH}"


# ── Version check — fail fast if infra not matching ───────────────────────────
echo "[0/4] Verifying required tech stack versions..."
INFRA_OK=true

# Java 8 check — use JAVA_HOME/bin/java explicitly to bypass system default
if [ ! -x "${JAVA_HOME}/bin/java" ]; then
    echo "  [!] Java 8 not found at ${JAVA_HOME}"
    echo "      Please run: ./bin/install_infra.sh"
    INFRA_OK=false
else
    JAVA_VER=$("${JAVA_HOME}/bin/java" -version 2>&1 | head -n 1)
    echo "  [+] Java (JAVA_HOME): ${JAVA_VER}"
fi

# Hadoop check
if [ -x "${HADOOP_HOME}/bin/hadoop" ]; then
    HADOOP_VER=$("${HADOOP_HOME}/bin/hadoop" version 2>/dev/null | head -n 1)
    if echo "${HADOOP_VER}" | grep -q "3.3.6"; then
        echo "  [+] Hadoop: ${HADOOP_VER}"
    else
        echo "  [!] Expected Hadoop 3.3.6, found: ${HADOOP_VER}"
        INFRA_OK=false
    fi
else
    echo "  [!] Hadoop not found at ${HADOOP_HOME}"
    INFRA_OK=false
fi

if [ "${INFRA_OK}" = false ]; then
    echo ""
    echo "[!] Infrastructure check failed. Please run ./bin/install_infra.sh first."
    exit 1
fi
echo "  [+] Version check passed."

# ── Start Services ────────────────────────────────────────────────────────────
echo -e "\n[1/4] Starting database and big data services..."

# Update core-site.xml with active user proxy settings to avoid HiveServer2 authorization errors
ACTUAL_USER="${USER:-$(whoami)}"
sed "s/USER_PLACEHOLDER/${ACTUAL_USER}/g" "${BASE_DIR}/conf/hadoop/core-site.xml" > "${HADOOP_HOME}/etc/hadoop/core-site.xml"

check_port() {
    local port=$1
    local name=$2
    if ss -tln 2>/dev/null | grep -q -E ":${port}\b"; then
        return 0  # port active
    fi
    return 1  # port not active
}

# MySQL
if ! check_port 3306 "MySQL"; then
    echo "  -> Starting MySQL..."
    sudo service mysql start 2>/dev/null || echo "    [!] MySQL failed to start — try: sudo service mysql start"
else
    echo "  -> MySQL already running."
fi

# MongoDB
if ! check_port 27017 "MongoDB"; then
    echo "  -> Starting MongoDB..."
    sudo service mongod start 2>/dev/null || echo "    [!] MongoDB failed to start — try: sudo service mongod start"
else
    echo "  -> MongoDB already running."
fi

# HDFS
if ! check_port 9000 "HDFS NameNode"; then
    echo "  -> Starting Hadoop DFS..."
    "${HADOOP_HOME}/sbin/start-dfs.sh"
else
    echo "  -> Hadoop DFS already running."
fi

# YARN
if ! check_port 8088 "YARN ResourceManager"; then
    echo "  -> Starting Hadoop YARN..."
    "${HADOOP_HOME}/sbin/start-yarn.sh"
else
    echo "  -> Hadoop YARN already running."
fi

# Hive Metastore
if ! check_port 9083 "Hive Metastore"; then
    echo "  -> Starting Hive Metastore..."
    nohup hive --service metastore > /tmp/hive-metastore.log 2>&1 &
    sleep 3
fi

# HiveServer2
if ! check_port 10000 "HiveServer2"; then
    echo "  -> Starting HiveServer2..."
    nohup hive --service hiveserver2 > /tmp/hiveserver2.log 2>&1 &
    
    echo "     Waiting for HiveServer2 to start (could take 15-30s)..."
    for i in {1..30}; do
        if check_port 10000 "HiveServer2"; then
            echo "     [+] HiveServer2 is ready on port 10000."
            break
        fi
        sleep 1
    done
    if ! check_port 10000 "HiveServer2"; then
        echo "     [!] HiveServer2 did not start within 30 seconds. It may still be booting."
    fi
else
    echo "  -> HiveServer2 already running."
fi

echo ""
echo "  --- Service Port Summary ---"
check_port 3306  "MySQL"            && echo "  [+] Port 3306  — MySQL"     || echo "  [-] Port 3306  — MySQL (not active)"
check_port 27017 "MongoDB"          && echo "  [+] Port 27017 — MongoDB"   || echo "  [-] Port 27017 — MongoDB (not active)"
check_port 9000  "HDFS NameNode"    && echo "  [+] Port 9000  — HDFS"      || echo "  [-] Port 9000  — HDFS (not active)"
check_port 9083  "Hive Metastore"   && echo "  [+] Port 9083  — Hive Metastore" || echo "  [-] Port 9083  — Hive Metastore (not active)"
check_port 10000 "HiveServer2"      && echo "  [+] Port 10000 — HiveServer2" || echo "  [-] Port 10000 — HiveServer2 (not active)"
echo "  ----------------------------"

# ── Activate Python venv ──────────────────────────────────────────────────────
VENV_DIR="${BASE_DIR}/venv"
if [ ! -f "${VENV_DIR}/bin/activate" ]; then
    echo ""
    echo "[!] Virtual environment not found at ${VENV_DIR}."
    echo "    Please run: ./bin/install_infra.sh"
    exit 1
fi

# Generate/update conf/mrjob.conf dynamically to avoid hardcoded paths
echo "[*] Generating conf/mrjob.conf dynamically..."
mkdir -p "${BASE_DIR}/conf"
cat > "${BASE_DIR}/conf/mrjob.conf" << EOF
runners:
  hadoop:
    python_bin: ${BASE_DIR}/venv/bin/python3
  local:
    python_bin: ${BASE_DIR}/venv/bin/python3
EOF

source "${VENV_DIR}/bin/activate"

# ── Data Collection (only if --crawl) ─────────────────────────────────────────
echo -e "\n[2/4] Data collection..."
if [ "${CRAWL}" = true ]; then
    echo "  [--crawl] Importing local offline data..."

    # TheMealDB Seed Data
    echo "  -> Loading local TheMealDB recipes..."
    python src/crawler/fetch_mealdb.py --offline \
        || echo "    [!] fetch_mealdb.py failed."

    # TripAdvisor Offline JSON
    echo "  -> Loading local TripAdvisor JSON..."
    python src/ingest/import_tripadvisor.py \
        || echo "    [!] import_tripadvisor.py failed."

    # Normalize and load into MySQL
    echo "  -> Normalizing and migrating data to MySQL (init_db.py)..."
    python src/ingest/init_db.py \
        || echo "    [!] init_db.py failed — check MySQL connection."

    # Sync to HDFS
    echo "  -> Syncing MongoDB → HDFS..."
    python src/ingest/mongo_to_hdfs.py \
        || echo "    [!] mongo_to_hdfs.py failed — check HDFS status."

    echo "  -> Syncing MySQL → HDFS..."
    python src/ingest/mysql_to_hdfs.py \
        || echo "    [!] mysql_to_hdfs.py failed — check HDFS status."

    # Update Hive schemas and views
    echo "  -> Registering Hive schemas (hive_schema.sql)..."
    hive -f src/ingest/hive_schema.sql \
        || echo "    [!] hive_schema.sql failed to register."

    echo "  -> Generating Hive analytical views (hive_analytics.sql)..."
    hive -f src/ingest/hive_analytics.sql \
        || echo "    [!] hive_analytics.sql failed to generate."
else
    echo "  [*] Skipping data import (use --crawl to re-import and sync local data)."
fi

# ── MapReduce Jobs (only if --jobs) ───────────────────────────────────────────
echo -e "\n[3/4] MapReduce analytical jobs..."
if [ "${RUN_JOBS}" = true ]; then
    echo "  [--jobs] Running all 8 MapReduce jobs on Hadoop YARN..."
    python src/mapreduce/run_all_jobs.py \
        || echo "    [!] Some MapReduce jobs failed — check YARN logs."
else
    echo "  [*] Skipping MapReduce jobs (use --jobs to run analytics)."
fi

# ── Launch Streamlit ──────────────────────────────────────────────────────────
echo -e "\n[4/4] Launching Streamlit web dashboard..."
echo "==================================================="
echo " Dashboard URL: http://localhost:8501"
echo " (Open in your Windows browser)"
echo ""
echo " Tips:"
echo "   ./bin/run.sh --crawl        # Refresh data on next start"
echo "   ./bin/run.sh --jobs         # Re-run MapReduce analytics"
echo "   ./bin/stop.sh               # Stop all services"
echo "   ./bin/stop.sh --backup      # Backup before stopping"
echo "==================================================="

streamlit run src/streamlit_app/app.py
