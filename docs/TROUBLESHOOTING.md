# Ubuntu WSL2 Big Data Stack: Troubleshooting Guide
## Quick Diagnostics & Workarounds (Ubuntu 24.04 LTS)

This guide compiles common errors encountered when running Hadoop, HDFS, YARN, MapReduce, MongoDB, MySQL, and Apache Hive natively on Ubuntu 24.04 LTS within a Windows Subsystem for Linux (WSL2) environment.

---

## 1. Hadoop, HDFS & YARN Issues

### Issue 1.1: `ssh: connect to host localhost port 22: Connection refused`
- **Symptoms**: Starting HDFS (`start-dfs.sh`) fails with SSH connection refused error.
- **Cause**: SSH server is either not installed or ssh daemon is inactive on WSL2.
- **Solution**:
  1. Install openssh-server:
     ```bash
     sudo apt update && sudo apt install openssh-server -y
     ```
  2. Start the ssh service:
     ```bash
     sudo service ssh start
     ```
  3. Generate and authorized keys to allow passwordless access:
     ```bash
     ssh-keygen -t rsa -P '' -f ~/.ssh/id_rsa
     cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
     chmod 0600 ~/.ssh/authorized_keys
     ```
  4. Test with `ssh localhost`.

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
- **Symptoms**: Streamlit throws `Access denied for user 'root'@'localhost'` error when trying to connect.
- **Cause**: MySQL on Ubuntu restricts root login to root OS users using auth_socket plugin.
- **Solution**: Set standard password authentication for the database root or create a dedicated user:
  ```sql
  ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'your_password';
  FLUSH PRIVILEGES;
  ```

---

## 3. Apache Hive Connection Issues

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

---

## 4. Python Environment Issues

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