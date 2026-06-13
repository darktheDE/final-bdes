#!/bin/bash
set -e

echo "[*] Extracting Hadoop..."
sudo tar -xzf /tmp/hadoop-3.3.6.tar.gz -C /usr/local/
if [ -d /usr/local/hadoop ]; then
    sudo rm -rf /usr/local/hadoop
fi
sudo mv /usr/local/hadoop-3.3.6 /usr/local/hadoop
sudo chown -R $USER:$USER /usr/local/hadoop

# Configure env in .bashrc (for current user)
echo "[*] Configuring .bashrc..."
if ! grep -q "HADOOP_HOME" ~/.bashrc; then
    echo 'export HADOOP_HOME=/usr/local/hadoop' >> ~/.bashrc
    echo 'export PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin' >> ~/.bashrc
fi

# Configure hadoop-env.sh
echo "[*] Configuring hadoop-env.sh..."
sed -i 's|# export JAVA_HOME=|export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64|g' /usr/local/hadoop/etc/hadoop/hadoop-env.sh
if ! grep -q "export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64" /usr/local/hadoop/etc/hadoop/hadoop-env.sh; then
    echo "export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64" >> /usr/local/hadoop/etc/hadoop/hadoop-env.sh
fi

# Configure core-site.xml
echo "[*] Configuring core-site.xml..."
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

# Configure hdfs-site.xml
echo "[*] Configuring hdfs-site.xml..."
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

# Configure yarn-site.xml
echo "[*] Configuring yarn-site.xml..."
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

# Configure mapred-site.xml
echo "[*] Configuring mapred-site.xml..."
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

echo "=== Hadoop Extraction and Configuration Completed ==="
