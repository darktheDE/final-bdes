#!/bin/bash
# ==============================================================================
# Database Backup Script
# Backs up MySQL (food_sentiment_db) and MongoDB (sentiment_db)
# to data/backups/backup_<TIMESTAMP>/
#
# Usage:
#   bash src/backup/db_backup.sh
#
# Called automatically by ./bin/stop.sh --backup
# ==============================================================================

# NOTE: Do NOT use set -e here — we want partial failures to be logged,
# not crash the whole script. Each step checks its own return code.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

BACKUPS_PARENT_DIR="${BASE_DIR}/data/backups"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_DIR="${BACKUPS_PARENT_DIR}/backup_${TIMESTAMP}"

BACKUP_SUCCESS=true

echo "==================================================="
echo " Database Backup Process"
echo " Target: ${BACKUP_DIR}"
echo "==================================================="

# Create backup directory
mkdir -p "${BACKUP_DIR}"
if [ ! -d "${BACKUP_DIR}" ]; then
    echo "[!] FATAL: Could not create backup directory ${BACKUP_DIR}."
    exit 1
fi

# ── MySQL Backup ──────────────────────────────────────────────────────────────
echo -e "\n[1/2] Backing up MySQL database: food_sentiment_db..."
MYSQL_BACKUP="${BACKUP_DIR}/mysql_backup.sql"

if mysqldump -h 127.0.0.1 -u root food_sentiment_db > "${MYSQL_BACKUP}" 2>/dev/null; then
    MYSQL_SIZE=$(du -sh "${MYSQL_BACKUP}" | cut -f1)
    echo "  [+] MySQL backup saved: ${MYSQL_BACKUP} (${MYSQL_SIZE})"
else
    echo "  [!] MySQL backup FAILED (is MySQL running? sudo service mysql start)"
    rm -f "${MYSQL_BACKUP}"
    BACKUP_SUCCESS=false
fi

# ── MongoDB Backup ────────────────────────────────────────────────────────────
echo -e "\n[2/2] Backing up MongoDB database: sentiment_db..."
MONGO_BACKUP_DIR="${BACKUP_DIR}/mongo_backup"

if mongodump --host localhost --port 27017 --db sentiment_db \
             --out "${MONGO_BACKUP_DIR}" --quiet 2>/dev/null; then
    echo "  [+] MongoDB backup saved: ${MONGO_BACKUP_DIR}/sentiment_db/"
else
    echo "  [!] MongoDB backup FAILED (is MongoDB running? sudo service mongod start)"
    BACKUP_SUCCESS=false
fi

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo "==================================================="
if [ "${BACKUP_SUCCESS}" = true ]; then
    echo "[+] SUCCESS: Full backup completed."
    echo " Backup location: ${BACKUP_DIR}"
    ls -lh "${BACKUP_DIR}"
else
    echo "[!] PARTIAL: Backup completed with errors. Check output above."
    echo " Backup location: ${BACKUP_DIR}"
    ls -lh "${BACKUP_DIR}" 2>/dev/null || true
fi
echo "==================================================="

# Exit with error if backup was not fully successful
[ "${BACKUP_SUCCESS}" = true ]
