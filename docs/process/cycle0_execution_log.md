# Cycle 0: Base Services Infrastructure Setup - Detailed Execution Log & Configuration Backup

This document contains a comprehensive record of the commands executed, configuration file contents, and validation outputs for the Base Services Infrastructure Setup (Cycle 0) on Ubuntu 24.04 WSL2.

> [!TIP]
> All the commands, configurations, and fixes documented here have been automated into a single one-click installer script: [install_infra.sh](../../bin/install_infra.sh).
> You can run `bash bin/install_infra.sh` on any clean Ubuntu 24.04 WSL2 distribution to set up the entire infrastructure automatically.

---


## 1. Task 0.1: SSH Server Configuration for Hadoop localhost Access

### Commands Executed:
1. Update apt cache and install OpenSSH server:
   ```bash
   sudo apt-get update && sudo apt-get install -y openssh-server
   ```
2. Start the SSH service:
   ```bash
   sudo service ssh start
   ```
3. Generate and register SSH keypairs for passwordless localhost access for `kien_hung` user:
   ```bash
   mkdir -p ~/.ssh
   chmod 700 ~/.ssh
   ssh-keygen -t rsa -P '' -f ~/.ssh/id_rsa
   cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
   chmod 0600 ~/.ssh/authorized_keys
   ```
4. Verification:
   ```bash
   ssh -o StrictHostKeyChecking=no localhost echo "SSH OK"
   ```

### Output / Verification Log:
- Output: `SSH OK`
- Passwordless access to localhost is fully functional.

---

## 2. Task 0.2: Java Development Kit (JDK 11) Setup

### Commands Executed:
1. Java was pre-installed. Verified the version:
   ```bash
   java -version
   ```
2. Exported `JAVA_HOME` in `~/.bashrc` by appending to the file:
   ```bash
   export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
   ```

### Output / Verification Log:
```
openjdk version "11.0.31" 2026-04-21
OpenJDK Runtime Environment (build 11.0.31+11-post-1ubuntu1-26.04.2-Ubuntu)
OpenJDK 64-Bit Server VM (build 11.0.31+11-post-1ubuntu1-26.04.2-Ubuntu, mixed mode, sharing)
```

---

## 3. Task 0.3: MySQL Server 8.4 Configuration

### Commands Executed:
1. Start the MySQL service:
   ```bash
   sudo service mysql start
   ```
2. Configure authentication for TCP/IP and Unix Socket root accounts to use empty passwords:
   ```sql
   CREATE USER IF NOT EXISTS 'root'@'127.0.0.1' IDENTIFIED BY '';
   ALTER USER 'root'@'127.0.0.1' IDENTIFIED BY '';
   GRANT ALL PRIVILEGES ON *.* TO 'root'@'127.0.0.1' WITH GRANT OPTION;
   ALTER USER 'root'@'localhost' IDENTIFIED BY '';
   GRANT ALL PRIVILEGES ON *.* TO 'root'@'localhost' WITH GRANT OPTION;
   FLUSH PRIVILEGES;
   ```
3. Create databases:
   ```sql
   CREATE DATABASE IF NOT EXISTS food_sentiment_db;
   CREATE DATABASE IF NOT EXISTS hive_metastore;
   ```

### Output / Verification Log:
- Verification using `mysql -u root -e "SHOW DATABASES;"`:
```
Database
food_sentiment_db
hive_metastore
information_schema
mysql
performance_schema
sys
```

---

## 4. Task 0.4: MongoDB Community Server Configuration

### Commands Executed:
1. Start the MongoDB daemon service:
   ```bash
   sudo service mongod start
   ```
2. Verification:
   ```bash
   mongosh --eval "db.adminCommand({ping: 1})"
   ```

### Output / Verification Log:
```json
{ "ok": 1 }
```

---

## 5. Task 0.5: Apache Hadoop 3.3.6 Configuration & Booting

### Commands Executed:
1. Download Hadoop 3.3.6 tarball package:
   ```bash
   curl -L -o /mnt/d/Project/final-bdes/hadoop-3.3.6.tar.gz https://archive.apache.org/dist/hadoop/common/hadoop-3.3.6/hadoop-3.3.6.tar.gz
   ```
2. Extract to `/usr/local/` and rename folder:
   ```bash
   sudo tar -xzf /mnt/d/Project/final-bdes/hadoop-3.3.6.tar.gz -C /usr/local/
   sudo mv /usr/local/hadoop-3.3.6 /usr/local/hadoop
   sudo chown -R kien_hung:kien_hung /usr/local/hadoop
   ```
3. Configure environment variables in `~/.bashrc`:
   ```bash
   export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
   export HADOOP_HOME=/usr/local/hadoop
   export HADOOP_INSTALL=$HADOOP_HOME
   export HADOOP_MAPRED_HOME=$HADOOP_HOME
   export HADOOP_COMMON_HOME=$HADOOP_HOME
   export HADOOP_HDFS_HOME=$HADOOP_HOME
   export YARN_HOME=$HADOOP_HOME
   export HADOOP_COMMON_LIB_NATIVE_DIR=$HADOOP_HOME/lib/native
   export PATH=$PATH:$HADOOP_HOME/sbin:$HADOOP_HOME/bin
   export HADOOP_OPTS="-Djava.library.path=$HADOOP_HOME/lib/native"
   ```
4. Configure XML config files inside `/usr/local/hadoop/etc/hadoop/` (contents backed up below).
5. Format NameNode:
   ```bash
   /usr/local/hadoop/bin/hdfs namenode -format -force
   ```
6. Start services:
   ```bash
   /usr/local/hadoop/sbin/start-dfs.sh
   /usr/local/hadoop/sbin/start-yarn.sh
   ```

### Configuration File Backups:

#### core-site.xml (`/usr/local/hadoop/etc/hadoop/core-site.xml`)
```xml
<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
    <property>
        <name>fs.defaultFS</name>
        <value>hdfs://localhost:9000</value>
    </property>
</configuration>
```

#### hdfs-site.xml (`/usr/local/hadoop/etc/hadoop/hdfs-site.xml`)
```xml
<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
    <property>
        <name>dfs.replication</name>
        <value>1</value>
    </property>
</configuration>
```

#### yarn-site.xml (`/usr/local/hadoop/etc/hadoop/yarn-site.xml`)
```xml
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
```

#### mapred-site.xml (`/usr/local/hadoop/etc/hadoop/mapred-site.xml`)
```xml
<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
    <property>
        <name>mapreduce.framework.name</name>
        <value>yarn</value>
    </property>
    <property>
        <name>mapreduce.application.classpath</name>
        <value>$HADOOP_HOME/share/hadoop/mapreduce/*:$HADOOP_HOME/share/hadoop/mapreduce/lib/*</value>
    </property>
</configuration>
```

#### hadoop-env.sh (`/usr/local/hadoop/etc/hadoop/hadoop-env.sh` modifications)
```bash
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
export HADOOP_HOME=/usr/local/hadoop
export HADOOP_INSTALL=$HADOOP_HOME
export HADOOP_MAPRED_HOME=$HADOOP_HOME
export HADOOP_COMMON_HOME=$HADOOP_HOME
export HADOOP_HDFS_HOME=$HADOOP_HOME
export YARN_HOME=$HADOOP_HOME
export HADOOP_COMMON_LIB_NATIVE_DIR=$HADOOP_HOME/lib/native
export PATH=$PATH:$HADOOP_HOME/sbin:$HADOOP_HOME/bin
export HADOOP_OPTS="-Djava.library.path=$HADOOP_HOME/lib/native"
```

### Output / Verification Log (`jps` output):
```
NodeManager
SecondaryNameNode
DataNode
ResourceManager
NameNode
```

---

## 6. Task 0.6: Apache Hive 3.1.3 Configuration & Metastore Setup

### Commands Executed:
1. Install OpenJDK 8 to run Hive 3.1.3 (due to JPMS classloader incompatibilities in Hive 3.1.3 on Java 11+):
   ```bash
   sudo apt-get install -y openjdk-8-jdk
   ```
2. Download and extract Apache Hive 3.1.3 package:
   ```bash
   curl -L -o /tmp/apache-hive-3.1.3-bin.tar.gz https://archive.apache.org/dist/hive/hive-3.1.3/apache-hive-3.1.3-bin.tar.gz
   sudo tar -xzf /tmp/apache-hive-3.1.3-bin.tar.gz -C /usr/local/
   sudo mv /usr/local/apache-hive-3.1.3-bin /usr/local/hive
   sudo chown -R kien_hung:kien_hung /usr/local/hive
   ```
3. Create a dedicated `hive` user in MySQL for metastore:
   ```sql
   CREATE USER IF NOT EXISTS 'hive'@'%' IDENTIFIED BY 'hive';
   GRANT ALL PRIVILEGES ON hive_metastore.* TO 'hive'@'%';
   CREATE USER IF NOT EXISTS 'hive'@'localhost' IDENTIFIED BY 'hive';
   GRANT ALL PRIVILEGES ON hive_metastore.* TO 'hive'@'localhost';
   FLUSH PRIVILEGES;
   ```
4. Download MySQL JDBC connector jar and copy to Hive lib folder:
   ```bash
   curl -L -o /tmp/mysql-connector-j-8.3.0.jar https://repo1.maven.org/maven2/com/mysql/mysql-connector-j/8.3.0/mysql-connector-j-8.3.0.jar
   cp /tmp/mysql-connector-j-8.3.0.jar /usr/local/hive/lib/
   ```
5. Fix Guava version conflict (replace Hive's old Guava 19 with Hadoop's Guava 27):
   ```bash
   rm /usr/local/hive/lib/guava-19.0.jar
   cp /usr/local/hadoop/share/hadoop/common/lib/guava-27.0-jre.jar /usr/local/hive/lib/
   ```
6. Make Hadoop `JAVA_HOME` configuration conditional in `/usr/local/hadoop/etc/hadoop/hadoop-env.sh`:
   ```bash
   export JAVA_HOME=${JAVA_HOME:-/usr/lib/jvm/java-11-openjdk-amd64}
   ```
7. Configure `/usr/local/hive/conf/hive-site.xml` (contents backed up below).
8. Initialize the metastore schema using Java 8:
   ```bash
   export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
   /usr/local/hive/bin/schematool -dbType mysql -initSchema
   ```
9. Test connection:
   ```bash
   /usr/local/hive/bin/hive -e "SHOW DATABASES;"
   ```

### Configuration File Backup:

#### hive-site.xml (`/usr/local/hive/conf/hive-site.xml`)
```xml
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
```

### Output / Verification Log:
```
OK
default
Time taken: 1.131 seconds, Fetched: 1 row(s)
```

