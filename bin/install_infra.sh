#!/bin/bash
# ==============================================================================
# Food & Restaurant Sentiment Analysis System - WSL2 Ubuntu Big Data Stack Installer
# Cycle 0: Base Services Infrastructure Setup (Automated Manual Installation Script)
# ==============================================================================

set -e

echo "======================================================================"
echo "Starting Big Data Stack Installation & Configuration on WSL2/Ubuntu..."
echo "======================================================================"

# 1. SSH Server Configuration
echo -e "\n[*] Step 1: Configuring SSH Server..."
sudo apt-get update
sudo apt-get install -y openssh-server
sudo service ssh start

# Configure passwordless SSH localhost access
mkdir -p ~/.ssh
chmod 700 ~/.ssh
if [ ! -f ~/.ssh/id_rsa ]; then
    ssh-keygen -t rsa -P '' -f ~/.ssh/id_rsa
fi
cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
chmod 0600 ~/.ssh/authorized_keys
ssh-keyscan -H localhost >> ~/.ssh/known_hosts
ssh-keyscan -H 127.0.0.1 >> ~/.ssh/known_hosts

echo "[+] SSH passwordless access configured successfully."

# 2. Java Environments Setup (Java 8 for Hadoop and Hive compatibility)
echo -e "\n[*] Step 2: Installing Java JDK 8..."
sudo apt-get install -y openjdk-8-jdk

# Configure .bashrc paths at the very top to prevent early return blocking
echo "[*] Adding environment variables to ~/.bashrc..."
cat << 'EOF' > /tmp/env_vars_temp
export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
export HADOOP_HOME=/usr/local/hadoop
export HADOOP_INSTALL=$HADOOP_HOME
export HADOOP_MAPRED_HOME=$HADOOP_HOME
export HADOOP_COMMON_HOME=$HADOOP_HOME
export HADOOP_HDFS_HOME=$HADOOP_HOME
export YARN_HOME=$HADOOP_HOME
export HADOOP_COMMON_LIB_NATIVE_DIR=$HADOOP_HOME/lib/native
export HIVE_HOME=/usr/local/hive
export PATH=$PATH:$HADOOP_HOME/sbin:$HADOOP_HOME/bin:$HIVE_HOME/bin
export HADOOP_OPTS="-Djava.library.path=$HADOOP_HOME/lib/native"
EOF

# Combine variables to the top of .bashrc safely
if ! grep -q "HADOOP_HOME" ~/.bashrc; then
    cat /tmp/env_vars_temp ~/.bashrc > ~/.bashrc.new && mv ~/.bashrc.new ~/.bashrc
fi
rm -f /tmp/env_vars_temp

# 3. MySQL Server Configuration
echo -e "\n[*] Step 3: Configuring MySQL Server..."
sudo apt-get install -y mysql-server
sudo service mysql start

# Configure permissions and create metastore/app databases
sudo mysql -u root << 'EOF'
CREATE USER IF NOT EXISTS 'root'@'127.0.0.1' IDENTIFIED BY '';
ALTER USER 'root'@'127.0.0.1' IDENTIFIED BY '';
GRANT ALL PRIVILEGES ON *.* TO 'root'@'127.0.0.1' WITH GRANT OPTION;
ALTER USER 'root'@'localhost' IDENTIFIED BY '';
GRANT ALL PRIVILEGES ON *.* TO 'root'@'localhost' WITH GRANT OPTION;

CREATE DATABASE IF NOT EXISTS food_sentiment_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS hive_metastore CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'hive'@'%' IDENTIFIED BY 'hive';
GRANT ALL PRIVILEGES ON hive_metastore.* TO 'hive'@'%';
CREATE USER IF NOT EXISTS 'hive'@'localhost' IDENTIFIED BY 'hive';
GRANT ALL PRIVILEGES ON hive_metastore.* TO 'hive'@'localhost';

FLUSH PRIVILEGES;
EOF

echo "[+] MySQL databases and users configured successfully."

# 4. MongoDB Server Configuration
echo -e "\n[*] Step 4: Installing and Starting MongoDB..."
sudo apt-get install -y gnupg curl
curl -fsSL https://www.mongodb.org/static/pgp/server-8.0.asc | sudo gpg --dearmor -o /usr/share/keyrings/mongodb-server-8.0.gpg
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-8.0.gpg ] https://repo.mongodb.org/apt/ubuntu noble/mongodb-org/8.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-8.0.list
sudo apt-get update
sudo apt-get install -y mongodb-org
sudo service mongod start

echo "[+] MongoDB started successfully."

# 5. Apache Hadoop Installation & Configuration
echo -e "\n[*] Step 5: Downloading and Configuring Apache Hadoop 3.3.6..."
HADOOP_TAR="/tmp/hadoop-3.3.6.tar.gz"
if [ ! -f "$HADOOP_TAR" ] || [ $(stat -c%s "$HADOOP_TAR") -lt 700000000 ]; then
    echo "[*] Downloading Hadoop 3.3.6..."
    rm -f "$HADOOP_TAR"
    curl -L -o "$HADOOP_TAR" https://archive.apache.org/dist/hadoop/common/hadoop-3.3.6/hadoop-3.3.6.tar.gz
fi

echo "[*] Extracting Hadoop to /usr/local/hadoop..."
sudo rm -rf /usr/local/hadoop /usr/local/hadoop-3.3.6
sudo tar -xzf "$HADOOP_TAR" -C /usr/local/
sudo mv /usr/local/hadoop-3.3.6 /usr/local/hadoop
sudo chown -R $USER:$USER /usr/local/hadoop

# Write Hadoop configuration files
echo "[*] Generating core-site.xml..."
cat <<EOT > /usr/local/hadoop/etc/hadoop/core-site.xml
<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
    <property>
        <name>fs.defaultFS</name>
        <value>hdfs://localhost:9000</value>
    </property>
</configuration>
EOT

echo "[*] Generating hdfs-site.xml..."
cat <<EOT > /usr/local/hadoop/etc/hadoop/hdfs-site.xml
<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
    <property>
        <name>dfs.replication</name>
        <value>1</value>
    </property>
</configuration>
EOT

echo "[*] Generating yarn-site.xml..."
cat <<EOT > /usr/local/hadoop/etc/hadoop/yarn-site.xml
<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
    <property>
        <name>yarn.nodemanager.aux-services</name>
        <value>mapreduce_shuffle</value>
    </property>
    <property>
        <name>yarn.nodemanager.aux-services.mapreduce_shuffle.class</name>
        <value>org.apache.hadoop.mapred.ShuffleHandler</value>
    </property>
    <property>
        <name>yarn.nodemanager.vmem-check-enabled</name>
        <value>false</value>
    </property>
</configuration>
EOT

echo "[*] Generating mapred-site.xml..."
cat <<EOT > /usr/local/hadoop/etc/hadoop/mapred-site.xml
<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
    <property>
        <name>mapreduce.framework.name</name>
        <value>yarn</value>
    </property>
    <property>
        <name>mapreduce.application.classpath</name>
        <value>\$HADOOP_HOME/share/hadoop/mapreduce/*:\$HADOOP_HOME/share/hadoop/mapreduce/lib/*</value>
    </property>
</configuration>
EOT

# Set up hadoop-env.sh JAVA_HOME
echo "[*] Configuring hadoop-env.sh..."
sed -i 's|# export JAVA_HOME=|export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64|g' /usr/local/hadoop/etc/hadoop/hadoop-env.sh
if ! grep -q "export JAVA_HOME=" /usr/local/hadoop/etc/hadoop/hadoop-env.sh; then
    echo 'export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64' >> /usr/local/hadoop/etc/hadoop/hadoop-env.sh
fi

# Format HDFS NameNode
echo "[*] Formatting HDFS NameNode..."
/usr/local/hadoop/bin/hdfs namenode -format -force

# Start HDFS & YARN
echo "[*] Booting Hadoop services..."
/usr/local/hadoop/sbin/start-dfs.sh
/usr/local/hadoop/sbin/start-yarn.sh

echo "[+] Apache Hadoop is running. Current processes:"
jps

# 6. Apache Hive Installation & Metastore Setup
echo -e "\n[*] Step 6: Downloading and Configuring Apache Hive 3.1.3..."
HIVE_TAR="/tmp/apache-hive-3.1.3-bin.tar.gz"
if [ ! -f "$HIVE_TAR" ] || [ $(stat -c%s "$HIVE_TAR") -lt 300000000 ]; then
    echo "[*] Downloading Apache Hive 3.1.3..."
    rm -f "$HIVE_TAR"
    curl -L -o "$HIVE_TAR" https://archive.apache.org/dist/hive/hive-3.1.3/apache-hive-3.1.3-bin.tar.gz
fi

echo "[*] Extracting Hive to /usr/local/hive..."
sudo rm -rf /usr/local/hive /usr/local/apache-hive-3.1.3-bin
sudo tar -xzf "$HIVE_TAR" -C /usr/local/
sudo mv /usr/local/apache-hive-3.1.3-bin /usr/local/hive
sudo chown -R $USER:$USER /usr/local/hive

# Download MySQL JDBC Connector
echo "[*] Downloading MySQL JDBC connector..."
MYSQL_JAR="/tmp/mysql-connector-j-8.3.0.jar"
if [ ! -f "$MYSQL_JAR" ]; then
    curl -L -o "$MYSQL_JAR" https://repo1.maven.org/maven2/com/mysql/mysql-connector-j/8.3.0/mysql-connector-j-8.3.0.jar
fi
cp "$MYSQL_JAR" /usr/local/hive/lib/

# Resolve Hive vs Hadoop Guava conflict
echo "[*] Fixing Guava library version mismatch..."
rm -f /usr/local/hive/lib/guava-19.0.jar
cp /usr/local/hadoop/share/hadoop/common/lib/guava-27.0-jre.jar /usr/local/hive/lib/

# Generate hive-site.xml
echo "[*] Generating hive-site.xml..."
cat <<EOT > /usr/local/hive/conf/hive-site.xml
<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
    <property>
        <name>javax.jdo.option.ConnectionURL</name>
        <value>jdbc:mysql://localhost:3306/hive_metastore?createDatabaseIfNotExist=true&amp;useSSL=false&amp;allowPublicKeyRetrieval=true</value>
    </property>
    <property>
        <name>javax.jdo.option.ConnectionDriverName</name>
        <value>com.mysql.cj.jdbc.Driver</value>
    </property>
    <property>
        <name>javax.jdo.option.ConnectionUserName</name>
        <value>hive</value>
    </property>
    <property>
        <name>javax.jdo.option.ConnectionPassword</name>
        <value>hive</value>
    </property>
    <property>
        <name>hive.metastore.warehouse.dir</name>
        <value>/user/hive/warehouse</value>
    </property>
    <property>
        <name>hive.cli.print.header</name>
        <value>true</value>
    </property>
    <property>
        <name>hive.cli.print.current.db</name>
        <value>true</value>
    </property>
</configuration>
EOT

# Initialize Hive Metastore Schema
echo "[*] Initializing Hive Metastore Schema..."
export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
/usr/local/hive/bin/schematool -dbType mysql -initSchema

echo -e "\n[*] Step 7: Verifying Hive installation..."
/usr/local/hive/bin/hive -e "SHOW DATABASES;"

echo -e "\n======================================================================"
echo "Big Data Infrastructure Stack configured successfully!"
echo "Enjoy analyzing restaurant sentiments!"
echo "======================================================================"
