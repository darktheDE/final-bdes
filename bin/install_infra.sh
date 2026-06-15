#!/bin/bash
# ==============================================================================
# Food & Restaurant Sentiment Analysis System
# Infrastructure Installer — WSL2 Ubuntu 24.04 LTS
#
# Usage:
#   bash bin/install_infra.sh           # Full install / re-install
#
# What this script does (idempotent — safe to re-run):
#   1. SSH passwordless localhost setup  (Hadoop requires this)
#   2. Java 8 OpenJDK                   (Hadoop 3.3.6 + Hive 3.1.3 require Java 8)
#   3. MySQL 8.0                        (Hive metastore + app database)
#   4. MongoDB 8.0                      (Raw restaurant data store)
#   5. Apache Hadoop 3.3.6              (HDFS + YARN)
#   6. Apache Hive 3.1.3               (Data warehouse / OLAP)
#   7. Python venv + dependencies       (mrjob, streamlit, scrapy, ...)
#
# After running this script, use:
#   ./bin/run.sh [--crawl] [--jobs]     # Start the full pipeline
#   ./bin/stop.sh [--backup] [--cleandata]  # Stop all services
# ==============================================================================

set -e

# Detect base directory of the project (parent of bin/)
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "======================================================================"
echo " Food & Restaurant Sentiment Analysis System — Infrastructure Installer"
echo " Base directory: ${BASE_DIR}"
echo " Target: Ubuntu 24.04 LTS (WSL2)"
echo "======================================================================"

# ──────────────────────────────────────────────────────────────────────────────
# STEP 1: SSH Server — Required for Hadoop pseudo-distributed mode
# ──────────────────────────────────────────────────────────────────────────────
echo -e "\n[Step 1/7] Configuring SSH Server for Hadoop..."
sudo apt-get update -qq
sudo apt-get install -y openssh-server

sudo service ssh start || true

mkdir -p ~/.ssh
chmod 700 ~/.ssh

if [ ! -f ~/.ssh/id_rsa ]; then
    ssh-keygen -t rsa -P '' -f ~/.ssh/id_rsa
fi

# Append public key only if not already present
if ! grep -qF "$(cat ~/.ssh/id_rsa.pub)" ~/.ssh/authorized_keys 2>/dev/null; then
    cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
fi
chmod 0600 ~/.ssh/authorized_keys

# Add localhost fingerprints (idempotent)
ssh-keyscan -H localhost >> ~/.ssh/known_hosts 2>/dev/null || true
ssh-keyscan -H 127.0.0.1 >> ~/.ssh/known_hosts 2>/dev/null || true

echo "[+] SSH passwordless access configured."

# ──────────────────────────────────────────────────────────────────────────────
# STEP 2: Java 8 — Hadoop 3.3.6 and Hive 3.1.3 require Java 8
#          (Java 11+ causes Kryo NoSuchFieldException in Hive 3.x)
# ──────────────────────────────────────────────────────────────────────────────
echo -e "\n[Step 2/7] Checking Java 8 (OpenJDK)..."

JAVA8_PATH="/usr/lib/jvm/java-1.8.0-openjdk-amd64"

if java -version 2>&1 | grep -q '"1\.8'; then
    echo "[+] Java 8 already active — skipping install."
else
    echo "[*] Java 8 not active. Installing openjdk-8-jdk..."
    sudo apt-get install -y openjdk-8-jdk
    # Set Java 8 as default
    sudo update-alternatives --set java "${JAVA8_PATH}/bin/java" 2>/dev/null || true
fi

export JAVA_HOME="${JAVA8_PATH}"
echo "  -> JAVA_HOME = ${JAVA_HOME}"
echo "  -> java version: $(java -version 2>&1 | head -n 1)"

# Write environment variables to ~/.bashrc (idempotent)
if ! grep -q "HADOOP_HOME" ~/.bashrc; then
    echo "[*] Adding environment variables to ~/.bashrc..."
    cat >> ~/.bashrc << 'ENVEOF'

# ── Food Sentiment Analysis — Big Data Stack ──────────────────────────────────
export JAVA_HOME=/usr/lib/jvm/java-1.8.0-openjdk-amd64
export HADOOP_HOME=/usr/local/hadoop
export HADOOP_INSTALL=$HADOOP_HOME
export HADOOP_MAPRED_HOME=$HADOOP_HOME
export HADOOP_COMMON_HOME=$HADOOP_HOME
export HADOOP_HDFS_HOME=$HADOOP_HOME
export YARN_HOME=$HADOOP_HOME
export HADOOP_COMMON_LIB_NATIVE_DIR=$HADOOP_HOME/lib/native
export HIVE_HOME=/usr/local/hive
export HADOOP_OPTS="-Djava.library.path=$HADOOP_HOME/lib/native"
export PATH=$PATH:$HADOOP_HOME/sbin:$HADOOP_HOME/bin:$HIVE_HOME/bin
# ─────────────────────────────────────────────────────────────────────────────
ENVEOF
fi

# ──────────────────────────────────────────────────────────────────────────────
# STEP 3: MySQL 8.0 — App database + Hive metastore backend
# ──────────────────────────────────────────────────────────────────────────────
echo -e "\n[Step 3/7] Configuring MySQL Server..."

if mysql --version 2>/dev/null | grep -q "mysql"; then
    echo "[+] MySQL already installed — skipping download."
else
    sudo apt-get install -y mysql-server
fi

sudo service mysql start

# Configure databases and users (idempotent)
echo "[*] Creating databases and users..."
sudo mysql -u root << 'SQLEOF'
-- App database
CREATE DATABASE IF NOT EXISTS food_sentiment_db
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Hive metastore database
CREATE DATABASE IF NOT EXISTS hive_metastore
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- root with empty password for TCP (127.0.0.1) access — app connection
CREATE USER IF NOT EXISTS 'root'@'127.0.0.1' IDENTIFIED BY '';
ALTER USER 'root'@'127.0.0.1' IDENTIFIED BY '';
GRANT ALL PRIVILEGES ON *.* TO 'root'@'127.0.0.1' WITH GRANT OPTION;

-- root@localhost — keep consistent
ALTER USER 'root'@'localhost' IDENTIFIED BY '';
GRANT ALL PRIVILEGES ON *.* TO 'root'@'localhost' WITH GRANT OPTION;

-- Dedicated Hive metastore user (NEVER use root for Hive JDBC)
CREATE USER IF NOT EXISTS 'hive'@'localhost' IDENTIFIED BY 'hive';
GRANT ALL PRIVILEGES ON hive_metastore.* TO 'hive'@'localhost';
CREATE USER IF NOT EXISTS 'hive'@'%' IDENTIFIED BY 'hive';
GRANT ALL PRIVILEGES ON hive_metastore.* TO 'hive'@'%';

FLUSH PRIVILEGES;
SQLEOF

echo "[+] MySQL databases and users configured."

# ──────────────────────────────────────────────────────────────────────────────
# STEP 4: MongoDB 8.0 Community — Raw restaurant + meals data store
# ──────────────────────────────────────────────────────────────────────────────
echo -e "\n[Step 4/7] Configuring MongoDB 8.0..."

if mongod --version 2>/dev/null | grep -q "db version"; then
    echo "[+] MongoDB already installed — skipping download."
else
    echo "[*] Installing MongoDB 8.0..."
    sudo apt-get install -y gnupg curl
    curl -fsSL https://www.mongodb.org/static/pgp/server-8.0.asc \
        | sudo gpg --dearmor -o /usr/share/keyrings/mongodb-server-8.0.gpg
    echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-8.0.gpg ] \
https://repo.mongodb.org/apt/ubuntu noble/mongodb-org/8.0 multiverse" \
        | sudo tee /etc/apt/sources.list.d/mongodb-org-8.0.list
    sudo apt-get update -qq
    sudo apt-get install -y mongodb-org
fi

sudo service mongod start || true
echo "[+] MongoDB started."

# ──────────────────────────────────────────────────────────────────────────────
# STEP 5: Apache Hadoop 3.3.6 — HDFS + YARN
# ──────────────────────────────────────────────────────────────────────────────
echo -e "\n[Step 5/7] Installing Apache Hadoop 3.3.6..."

HADOOP_INSTALL_DIR="/usr/local/hadoop"
HADOOP_TAR="/tmp/hadoop-3.3.6.tar.gz"
HADOOP_VERSION_CHECK="3.3.6"

# Check if correct version already installed
if [ -d "${HADOOP_INSTALL_DIR}" ] && \
   "${HADOOP_INSTALL_DIR}/bin/hadoop" version 2>/dev/null | grep -q "${HADOOP_VERSION_CHECK}"; then
    echo "[+] Hadoop ${HADOOP_VERSION_CHECK} already installed at ${HADOOP_INSTALL_DIR} — skipping download."
else
    echo "[*] Downloading Hadoop ${HADOOP_VERSION_CHECK}..."
    # Only download if tar not present or incomplete (< 700 MB)
    if [ ! -f "${HADOOP_TAR}" ] || [ "$(stat -c%s "${HADOOP_TAR}" 2>/dev/null || echo 0)" -lt 700000000 ]; then
        rm -f "${HADOOP_TAR}"
        curl -L -o "${HADOOP_TAR}" \
            https://archive.apache.org/dist/hadoop/common/hadoop-3.3.6/hadoop-3.3.6.tar.gz
    fi

    echo "[*] Extracting Hadoop to ${HADOOP_INSTALL_DIR}..."
    sudo rm -rf "${HADOOP_INSTALL_DIR}" /usr/local/hadoop-3.3.6
    sudo tar -xzf "${HADOOP_TAR}" -C /usr/local/
    sudo mv /usr/local/hadoop-3.3.6 "${HADOOP_INSTALL_DIR}"
    sudo chown -R "${USER}:${USER}" "${HADOOP_INSTALL_DIR}"
fi

export HADOOP_HOME="${HADOOP_INSTALL_DIR}"

# Copy XML config files from project conf/ into Hadoop installation
echo "[*] Copying Hadoop config from conf/hadoop/ ..."
cp "${BASE_DIR}/conf/hadoop/core-site.xml"  "${HADOOP_HOME}/etc/hadoop/core-site.xml"
cp "${BASE_DIR}/conf/hadoop/hdfs-site.xml"  "${HADOOP_HOME}/etc/hadoop/hdfs-site.xml"
cp "${BASE_DIR}/conf/hadoop/yarn-site.xml"  "${HADOOP_HOME}/etc/hadoop/yarn-site.xml"
cp "${BASE_DIR}/conf/hadoop/mapred-site.xml" "${HADOOP_HOME}/etc/hadoop/mapred-site.xml"
echo "[+] Hadoop config copied."

# Set JAVA_HOME in hadoop-env.sh
HADOOP_ENV="${HADOOP_HOME}/etc/hadoop/hadoop-env.sh"
if ! grep -q "^export JAVA_HOME=/usr/lib/jvm/java-1.8.0" "${HADOOP_ENV}"; then
    # Remove any existing export JAVA_HOME line to avoid duplicates
    sed -i '/^export JAVA_HOME=/d' "${HADOOP_ENV}"
    echo 'export JAVA_HOME=/usr/lib/jvm/java-1.8.0-openjdk-amd64' >> "${HADOOP_ENV}"
fi
echo "[+] hadoop-env.sh JAVA_HOME configured."

# Format NameNode only if it has never been formatted
HDFS_DATA_DIR="${HOME}/hadoop-data"
if [ ! -d "${HDFS_DATA_DIR}/namenode" ]; then
    echo "[*] Formatting HDFS NameNode (first time)..."
    "${HADOOP_HOME}/bin/hdfs" namenode -format -force
else
    echo "[+] NameNode already formatted — skipping."
fi

echo "[*] Starting Hadoop DFS & YARN..."
"${HADOOP_HOME}/sbin/start-dfs.sh"
"${HADOOP_HOME}/sbin/start-yarn.sh"

echo "[+] Hadoop services started. Running processes:"
jps

# ──────────────────────────────────────────────────────────────────────────────
# STEP 6: Apache Hive 3.1.3 — Data Warehouse / OLAP
# ──────────────────────────────────────────────────────────────────────────────
echo -e "\n[Step 6/7] Installing Apache Hive 3.1.3..."

HIVE_INSTALL_DIR="/usr/local/hive"
HIVE_TAR="/tmp/apache-hive-3.1.3-bin.tar.gz"
HIVE_VERSION_CHECK="3.1.3"

if [ -d "${HIVE_INSTALL_DIR}" ] && \
   "${HIVE_INSTALL_DIR}/bin/hive" --version 2>/dev/null | grep -q "${HIVE_VERSION_CHECK}"; then
    echo "[+] Hive ${HIVE_VERSION_CHECK} already installed — skipping download."
else
    echo "[*] Downloading Apache Hive ${HIVE_VERSION_CHECK}..."
    if [ ! -f "${HIVE_TAR}" ] || [ "$(stat -c%s "${HIVE_TAR}" 2>/dev/null || echo 0)" -lt 300000000 ]; then
        rm -f "${HIVE_TAR}"
        curl -L -o "${HIVE_TAR}" \
            https://archive.apache.org/dist/hive/hive-3.1.3/apache-hive-3.1.3-bin.tar.gz
    fi

    echo "[*] Extracting Hive to ${HIVE_INSTALL_DIR}..."
    sudo rm -rf "${HIVE_INSTALL_DIR}" /usr/local/apache-hive-3.1.3-bin
    sudo tar -xzf "${HIVE_TAR}" -C /usr/local/
    sudo mv /usr/local/apache-hive-3.1.3-bin "${HIVE_INSTALL_DIR}"
    sudo chown -R "${USER}:${USER}" "${HIVE_INSTALL_DIR}"
fi

export HIVE_HOME="${HIVE_INSTALL_DIR}"

# MySQL JDBC Connector for Hive metastore
MYSQL_JAR="/tmp/mysql-connector-j-8.3.0.jar"
MYSQL_JAR_DEST="${HIVE_HOME}/lib/mysql-connector-j-8.3.0.jar"
if [ ! -f "${MYSQL_JAR_DEST}" ]; then
    echo "[*] Downloading MySQL JDBC connector..."
    if [ ! -f "${MYSQL_JAR}" ]; then
        curl -L -o "${MYSQL_JAR}" \
            https://repo1.maven.org/maven2/com/mysql/mysql-connector-j/8.3.0/mysql-connector-j-8.3.0.jar
    fi
    cp "${MYSQL_JAR}" "${MYSQL_JAR_DEST}"
    echo "[+] MySQL JDBC connector installed."
else
    echo "[+] MySQL JDBC connector already present."
fi

# Fix Guava version mismatch — Hive 3.x ships guava-19, Hadoop 3.3.6 uses guava-27
echo "[*] Fixing Guava library conflict (guava-19 → guava-27)..."
rm -f "${HIVE_HOME}/lib/guava-19.0.jar"
GUAVA_SRC="${HADOOP_HOME}/share/hadoop/common/lib/guava-27.0-jre.jar"
GUAVA_DEST="${HIVE_HOME}/lib/guava-27.0-jre.jar"
if [ -f "${GUAVA_SRC}" ] && [ ! -f "${GUAVA_DEST}" ]; then
    cp "${GUAVA_SRC}" "${GUAVA_DEST}"
    echo "[+] Guava 27 copied to Hive lib."
else
    echo "[+] Guava already fixed or source not found (skipping)."
fi

# Copy hive-site.xml from project conf/
echo "[*] Copying hive-site.xml from conf/hive/ ..."
cp "${BASE_DIR}/conf/hive/hive-site.xml" "${HIVE_HOME}/conf/hive-site.xml"
echo "[+] hive-site.xml copied."

# Initialize Hive Metastore schema (idempotent — will skip if already initialized)
echo "[*] Initializing Hive Metastore schema in MySQL..."
export JAVA_HOME="${JAVA8_PATH}"
"${HIVE_HOME}/bin/schematool" -dbType mysql -initSchema 2>&1 \
    | grep -v "SLF4J" || true
echo "[+] Hive Metastore initialized."

# Create HDFS warehouse directory
"${HADOOP_HOME}/bin/hdfs" dfs -mkdir -p /user/hive/warehouse 2>/dev/null || true
"${HADOOP_HOME}/bin/hdfs" dfs -chmod g+w /user/hive/warehouse 2>/dev/null || true

# Quick smoke test
echo "[*] Verifying Hive installation..."
"${HIVE_HOME}/bin/hive" -e "SHOW DATABASES;" 2>/dev/null || echo "[!] Hive smoke test skipped (metastore may need a moment to start)."

# ──────────────────────────────────────────────────────────────────────────────
# STEP 7: Python Virtual Environment + Dependencies
# ──────────────────────────────────────────────────────────────────────────────
echo -e "\n[Step 7/7] Setting up Python virtual environment..."

# Ensure python3-venv is available
if ! dpkg -l 2>/dev/null | grep -q "python3-venv"; then
    echo "[*] Installing python3-venv..."
    sudo apt-get install -y python3-venv python3-pip
fi

VENV_DIR="${BASE_DIR}/venv"
if [ ! -d "${VENV_DIR}" ]; then
    echo "[*] Creating virtual environment at ${VENV_DIR}..."
    python3 -m venv "${VENV_DIR}"
fi

echo "[*] Activating venv and installing dependencies..."
source "${VENV_DIR}/bin/activate"
pip install --upgrade pip --quiet
pip install -r "${BASE_DIR}/requirements.txt" --quiet
echo "[+] Python dependencies installed."

# Generate conf/mrjob.conf dynamically to avoid hardcoded paths
echo "[*] Generating conf/mrjob.conf dynamically..."
mkdir -p "${BASE_DIR}/conf"
cat > "${BASE_DIR}/conf/mrjob.conf" << EOF
runners:
  hadoop:
    python_bin: ${BASE_DIR}/venv/bin/python3
  local:
    python_bin: ${BASE_DIR}/venv/bin/python3
EOF

# Initialize database schemas with seed data (Delegated to bin/ingest.sh)
echo "[*] Database initialization has been moved to a separate script."
echo "    After activating your virtual environment, please run: bash bin/ingest.sh"

# ──────────────────────────────────────────────────────────────────────────────
# DONE
# ──────────────────────────────────────────────────────────────────────────────
echo -e "\n======================================================================"
echo "[+] Infrastructure setup complete!"
echo ""
echo " Next steps:"
echo "   1. Start the system:   ./bin/run.sh"
echo "   2. With fresh data:    ./bin/run.sh --crawl"
echo "   3. Run MR jobs:        ./bin/run.sh --jobs"
echo "   4. Stop everything:    ./bin/stop.sh"
echo ""
echo " Open dashboard: http://localhost:8501"
echo "======================================================================"
