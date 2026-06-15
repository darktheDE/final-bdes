# Ubuntu WSL2 Big Data Stack: Troubleshooting Guide
## Quick Diagnostics & Workarounds (Ubuntu 24.04 LTS)

This guide compiles common errors encountered when running Hadoop, HDFS, YARN, MapReduce, MongoDB, MySQL, and Apache Hive natively on Ubuntu 24.04 LTS within a Windows Subsystem for Linux (WSL2) environment.

---

## 1. Hadoop, HDFS & YARN Issues

### Issue 1.1: `ssh: connect to host localhost port 22: Connection refused`
- **Symptoms**: Starting HDFS (`start-dfs.sh`) fails with SSH connection refused error.
- **Cause**: SSH server is either not installed or inactive on WSL2.
- **Solution**:
  1. Install openssh-server:
     ```bash
     sudo apt update && sudo apt install openssh-server -y
     ```
  2. Start the ssh service (needs to be done every time WSL restarts unless automated):
     ```bash
     sudo service ssh start
     ```
  3. Generate authorized keys to allow passwordless access:
     ```bash
     ssh-keygen -t rsa -P '' -f ~/.ssh/id_rsa
     cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
     chmod 0600 ~/.ssh/authorized_keys
     ```
  4. Test with:
     ```bash
     ssh localhost
     ```

### Issue 1.2: MapReduce Job stuck at 0% or failing on YARN
- **Symptoms**: YARN launches but MapReduce jobs freeze indefinitely.
- **Cause**: NodeManager virtual memory limits killing containers (false positive in WSL2/Windows VM environments).
- **Solution**: Disable the check in `yarn-site.xml`:
  ```xml
  <property>
    <name>yarn.nodemanager.vmem-check-enabled</name>
    <value>false</value>
  </property>
  ```

### Issue 1.3: `Input path does not exist: hdfs://localhost:9000/.../restaurants.jsonl`
- **Symptoms**: MapReduce job fails immediately claiming the file is missing.
- **Cause**: HDFS path structure has been updated during refactor.
- **Solution**: Verify the directory structure in HDFS using:
  ```bash
  hdfs dfs -ls -R /data/raw/
  ```
  Ensure you are using the correct full path: `hdfs://localhost:9000/data/raw/restaurants/restaurants.jsonl`

---

## 2. MySQL & MongoDB Daemon Issues

### Issue 2.1: `System has not been booted with systemd as init system` (MongoDB/MySQL)
- **Symptoms**: Running `systemctl` commands yields PID 1 errors.
- **Cause**: WSL2 doesn't initialize systemd by default.
- **Solution**:
  - **Quick Workaround**: Use SysV init commands:
    ```bash
    sudo service mysql start
    sudo service mongod start
    ```
  - **Enable systemd permanently**: Create/edit `/etc/wsl.conf`:
    ```ini
    [boot]
    systemd=true
    ```
    Then restart WSL2 in Windows PowerShell: `wsl --shutdown`.

### Issue 2.2: MySQL Access Denied for root user
- **Symptoms**: Setup script or Streamlit throws `Access denied for user 'root'@'localhost'` (Error 1698) or similar connection errors.
- **Cause**: MySQL on Ubuntu restricts root login to root OS users using the `auth_socket` plugin, and handles connection host profiles `localhost` (Unix socket) and `127.0.0.1` (TCP/IP) separately. Additionally, newer MySQL versions (8.4+) disable the old `mysql_native_password` plugin by default.
- **Solution**: 
  1. Open the MySQL console with superuser privileges:
     ```bash
     sudo mysql -u root
     ```
  2. Execute the following SQL queries to create/alter root users to authenticate with empty passwords using the default authentication (or `caching_sha2_password`):
     ```sql
     -- Setup for TCP/IP connection (127.0.0.1)
     CREATE USER IF NOT EXISTS 'root'@'127.0.0.1' IDENTIFIED BY '';
     ALTER USER 'root'@'127.0.0.1' IDENTIFIED BY '';
     GRANT ALL PRIVILEGES ON *.* TO 'root'@'127.0.0.1' WITH GRANT OPTION;

     -- Setup for Unix socket connection (localhost)
     ALTER USER 'root'@'localhost' IDENTIFIED BY '';
     GRANT ALL PRIVILEGES ON *.* TO 'root'@'localhost' WITH GRANT OPTION;

     FLUSH PRIVILEGES;
     EXIT;
     ```
  3. Restart the MySQL service:
     ```bash
     sudo service mysql restart
     ```

### Issue 2.3: MySQL `district_parsed` values are all "Unknown"
- **Symptoms**: After running `init_db.py`, the `district_parsed` column only contains "Unknown".
- **Cause**: MySQL 8.0 deprecated `VALUES()` in `ON DUPLICATE KEY UPDATE`. The Python script's SQL UPSERT command might fail to update new columns if old rows existed.
- **Solution**: Clear the tables and re-run ingestion:
  ```sql
  TRUNCATE TABLE reviews;
  TRUNCATE TABLE restaurants;
  ```
  Then run `python src/ingest/init_db.py` again.

---

## 3. Apache Hive Connection & Runtime Issues

### Issue 3.1: Hive client throws Connection Refused on Thrift Port 10000
- **Symptoms**: Streamlit PyHive connector fails to communicate with Hive.
- **Cause**: HiveServer2 is not running, or Thrift server has not fully loaded.
- **Solution**:
  1. Start Hive metastore and HiveServer2 services in background:
     ```bash
     hive --service metastore &
     hive --service hiveserver2 &
     ```
  2. Wait 30 seconds for the Thrift service to bind to port 10000. Check active ports:
     ```bash
     netstat -an | grep 10000
     ```

### Issue 3.2: `NoSuchFieldException: parentOffset` (Java Kryo Conflict)
- **Symptoms**: Running MapReduce queries via Hive fails with `Kryo` serialization errors.
- **Cause**: Hive 3.1.3 is strictly incompatible with Java 11+. Using Java 11 causes reflection errors in Kryo.
- **Solution**: Force Hadoop/Hive to use Java 8. Ensure `JAVA_HOME` points exactly to the Java 8 JRE:
  ```bash
  export JAVA_HOME="/usr/lib/jvm/java-8-openjdk-amd64/jre"
  ```
  Check that `${JAVA_HOME}/bin/java -version` returns `1.8.x`.

### Issue 3.3: `java.lang.NoSuchMethodError: com.google.common.base.Preconditions.checkArgument`
- **Symptoms**: Hive metastore or commands crash immediately on startup.
- **Cause**: Library mismatch. Hive 3.1.3 ships with `guava-19.0.jar`, but Hadoop 3.3.6 requires `guava-27.0-jre.jar`.
- **Solution**: Delete Hive's old Guava and copy Hadoop's newer version:
  ```bash
  rm /usr/local/hive/lib/guava-19.0.jar
  cp /usr/local/hadoop/share/hadoop/common/lib/guava-27.0-jre.jar /usr/local/hive/lib/
  ```

---

## 4. Environment & Python Issues

### Issue 4.1: `ModuleNotFoundError: No module named 'distutils'`
- **Symptoms**: PySpark or `mrjob` throws exceptions under Python 3.12 (Ubuntu 24.04 default).
- **Cause**: Python 3.12 dropped `distutils` from the standard library.
- **Solution**: Create a virtual environment using Python 3.10/3.11:
  ```bash
  sudo add-apt-repository ppa:deadsnakes/ppa -y
  sudo apt update
  sudo apt install python3.10 python3.10-venv python3.10-dev -y
  python3.10 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  ```

### Issue 4.2: `/bin/sh: bash: not found` when running wsl from PowerShell
- **Symptoms**: Running `wsl bash script.sh` from Windows gives a `not found` error.
- **Cause**: Your WSL default distro might be set to `docker-desktop` (which uses Alpine/busybox) instead of `Ubuntu`.
- **Solution**: Always specify the distro name:
  ```powershell
  wsl -d Ubuntu -- bash script.sh
  ```
  Or change your default distro in Windows PowerShell:
  ```powershell
  wsl -s Ubuntu
  ```