#!/bin/bash
set -e

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Base directory setup (root of the project)
BASE_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Define backup directories
BACKUPS_PARENT_DIR="${BASE_DIR}/data/backups"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_DIR="${BACKUPS_PARENT_DIR}/backup_${TIMESTAMP}"

echo "==================================================="
echo " Starting Database Backup Process"
echo " Target Folder: ${BACKUP_DIR}"
echo "==================================================="

# Ensure directories exist
mkdir -p "${BACKUP_DIR}"

# 1. Backup MySQL (food_sentiment_db)
echo "[*] Backing up MySQL database: food_sentiment_db..."
# Use host 127.0.0.1 and user root (no password by default)
mysqldump -h 127.0.0.1 -u root food_sentiment_db > "${BACKUP_DIR}/mysql_backup.sql"
echo "  -> MySQL backup saved: ${BACKUP_DIR}/mysql_backup.sql"

# 2. Backup MongoDB (sentiment_db)
echo "[*] Backing up MongoDB database: sentiment_db..."
mongodump --host localhost --port 27017 --db sentiment_db --out "${BACKUP_DIR}/mongo_backup"
echo "  -> MongoDB backup saved in: ${BACKUP_DIR}/mongo_backup"

echo "==================================================="
echo "[+] SUCCESS: Database backup completed."
echo "==================================================="
ls -lh "${BACKUP_DIR}"
