#!/bin/bash
# ==============================================================================
# Food & Restaurant Sentiment Analysis System — Service Stopper
#
# Usage:
#   ./bin/stop.sh                  # Stop all services
#   ./bin/stop.sh --backup         # Backup all data before stopping
#   ./bin/stop.sh --cleandata      # Wipe all data after stopping (demo reset)
#   ./bin/stop.sh --backup --cleandata  # Backup first, then wipe
# ==============================================================================

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${BASE_DIR}"

echo "==================================================="
echo " Food & Restaurant Sentiment Analysis System"
echo " Stopping all services..."
echo "==================================================="

# ── Parse flags ───────────────────────────────────────────────────────────────
DO_BACKUP=false
DO_CLEANDATA=false
for arg in "$@"; do
    case "${arg}" in
        --backup)    DO_BACKUP=true ;;
        --cleandata) DO_CLEANDATA=true ;;
        --help|-h)
            echo ""
            echo "Usage: ./bin/stop.sh [--backup] [--cleandata]"
            echo ""
            echo "  --backup     Run database backup before stopping services."
            echo "  --cleandata  Wipe all data from MongoDB, MySQL, and HDFS."
            echo "               Useful for a clean demo run (combine with --crawl on next start)."
            echo ""
            exit 0
            ;;
    esac
done

export HADOOP_HOME="/usr/local/hadoop"

# ── Step 1: Optional backup ───────────────────────────────────────────────────
if [ "${DO_BACKUP}" = true ]; then
    echo -e "\n[--backup] Running database backup before stopping..."
    BACKUP_SCRIPT="${BASE_DIR}/src/backup/db_backup.sh"
    if [ -f "${BACKUP_SCRIPT}" ]; then
        bash "${BACKUP_SCRIPT}"
    else
        echo "  [!] Backup script not found at ${BACKUP_SCRIPT}. Skipping backup."
    fi
fi

# ── Step 2: Stop Streamlit ────────────────────────────────────────────────────
echo -e "\n[1/4] Stopping Streamlit..."
if pgrep -f "streamlit run" > /dev/null 2>&1; then
    pkill -f "streamlit run" && echo "  [+] Streamlit stopped." || echo "  [-] Could not stop Streamlit."
else
    echo "  [*] Streamlit not running."
fi

# ── Step 3: Stop Hadoop ───────────────────────────────────────────────────────
echo -e "\n[2/4] Stopping Hadoop (YARN + DFS)..."
if [ -x "${HADOOP_HOME}/sbin/stop-yarn.sh" ]; then
    "${HADOOP_HOME}/sbin/stop-yarn.sh" 2>/dev/null && echo "  [+] YARN stopped." || echo "  [-] YARN stop failed (may already be stopped)."
else
    echo "  [!] Hadoop not found at ${HADOOP_HOME}"
fi

if [ -x "${HADOOP_HOME}/sbin/stop-dfs.sh" ]; then
    "${HADOOP_HOME}/sbin/stop-dfs.sh" 2>/dev/null && echo "  [+] HDFS stopped." || echo "  [-] HDFS stop failed (may already be stopped)."
fi

# ── Step 4: Stop MongoDB ──────────────────────────────────────────────────────
echo -e "\n[3/4] Stopping MongoDB..."
sudo service mongod stop 2>/dev/null && echo "  [+] MongoDB stopped." || echo "  [*] MongoDB already stopped."

# ── Step 5: Stop MySQL ────────────────────────────────────────────────────────
echo -e "\n[4/4] Stopping MySQL..."
sudo service mysql stop 2>/dev/null && echo "  [+] MySQL stopped." || echo "  [*] MySQL already stopped."

# ── Step 6: Optional data wipe ───────────────────────────────────────────────
if [ "${DO_CLEANDATA}" = true ]; then
    echo -e "\n[--cleandata] Wiping all data stores for demo reset..."
    echo "  [!] WARNING: This will permanently delete all crawled data."

    # Restart services temporarily for clean drop
    sudo service mysql start 2>/dev/null || true
    sudo service mongod start 2>/dev/null || true
    sleep 2

    # Drop and recreate MySQL app database
    echo "  -> Clearing MySQL food_sentiment_db..."
    mysql -h 127.0.0.1 -u root 2>/dev/null << 'SQLEOF' || echo "  [!] MySQL clean failed."
DROP DATABASE IF EXISTS food_sentiment_db;
CREATE DATABASE food_sentiment_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
SQLEOF
    echo "  [+] MySQL data cleared."

    # Drop MongoDB sentiment_db
    echo "  -> Clearing MongoDB sentiment_db..."
    mongosh --quiet --eval 'db.getSiblingDB("sentiment_db").dropDatabase()' 2>/dev/null \
        || mongo --quiet --eval 'db.getSiblingDB("sentiment_db").dropDatabase()' 2>/dev/null \
        || echo "  [!] MongoDB clean failed (mongosh/mongo not found)."
    echo "  [+] MongoDB data cleared."

    # Clear HDFS data directory
    echo "  -> Clearing HDFS /data/raw ..."
    if [ -x "${HADOOP_HOME}/bin/hdfs" ]; then
        "${HADOOP_HOME}/sbin/start-dfs.sh" 2>/dev/null || true
        sleep 3
        "${HADOOP_HOME}/bin/hdfs" dfs -rm -r -f /data/raw 2>/dev/null || true
        echo "  [+] HDFS /data/raw cleared."
        "${HADOOP_HOME}/sbin/stop-dfs.sh" 2>/dev/null || true
    else
        echo "  [!] Hadoop not available — HDFS data not cleared."
    fi

    # Stop services again
    sudo service mysql stop 2>/dev/null || true
    sudo service mongod stop 2>/dev/null || true

    echo ""
    echo "  [+] All data cleared. To run full pipeline fresh:"
    echo "      ./bin/run.sh --crawl --jobs"
fi

# ── Done ──────────────────────────────────────────────────────────────────────
echo -e "\n==================================================="
echo "[+] All services stopped."
echo ""
if [ "${DO_CLEANDATA}" = true ]; then
    echo " Data wiped. Next run: ./bin/run.sh --crawl --jobs"
else
    echo " To restart:  ./bin/run.sh"
    echo " To backup:   ./bin/stop.sh --backup"
fi
echo "==================================================="
