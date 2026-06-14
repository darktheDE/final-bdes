#!/bin/bash
set -e

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Base directory setup (root of the project)
BASE_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

BACKUPS_PARENT_DIR="${BASE_DIR}/data/backups"

# Check if target backup directory is provided
if [ -z "$1" ]; then
    echo "==================================================="
    echo " Error: No backup folder name or path provided."
    echo " Usage: bash src/backup/db_restore.sh <backup_folder_name_or_path>"
    echo "==================================================="
    echo "Available backups in ${BACKUPS_PARENT_DIR}:"
    if [ -d "${BACKUPS_PARENT_DIR}" ]; then
        ls -d "${BACKUPS_PARENT_DIR}"/*/ 2>/dev/null | xargs -n 1 basename || echo "  No backups found."
    else
        echo "  No backups directory exists."
    fi
    exit 1
fi

# Resolve path
if [ -d "$1" ]; then
    BACKUP_DIR="$1"
else
    BACKUP_DIR="${BACKUPS_PARENT_DIR}/$1"
fi

# Validate backup folder exists
if [ ! -d "${BACKUP_DIR}" ]; then
    echo "[!] Error: Backup directory ${BACKUP_DIR} not found."
    exit 1
fi

echo "==================================================="
echo " Starting Database Restore Process"
echo " Source Folder: ${BACKUP_DIR}"
echo "==================================================="

# 1. Restore MySQL
MYSQL_BACKUP_FILE="${BACKUP_DIR}/mysql_backup.sql"
if [ -f "${MYSQL_BACKUP_FILE}" ]; then
    echo "[*] Restoring MySQL database: food_sentiment_db..."
    # Ensure database exists
    mysql -h 127.0.0.1 -u root -e "CREATE DATABASE IF NOT EXISTS food_sentiment_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
    # Restore from dump file
    mysql -h 127.0.0.1 -u root food_sentiment_db < "${MYSQL_BACKUP_FILE}"
    echo "  -> MySQL restore completed."
else
    echo "[!] Warning: No MySQL backup file found at ${MYSQL_BACKUP_FILE}."
fi

# 2. Restore MongoDB
MONGO_BACKUP_SUBDIR="${BACKUP_DIR}/mongo_backup"
if [ -d "${MONGO_BACKUP_SUBDIR}" ]; then
    echo "[*] Restoring MongoDB database: sentiment_db..."
    # Restore using --drop to clean existing database before restoring
    mongorestore --host localhost --port 27017 --db sentiment_db --drop "${MONGO_BACKUP_SUBDIR}/sentiment_db"
    echo "  -> MongoDB restore completed."
else
    echo "[!] Warning: No MongoDB backup directory found at ${MONGO_BACKUP_SUBDIR}."
fi

echo "==================================================="
echo "[+] SUCCESS: Database restore completed."
echo "==================================================="
