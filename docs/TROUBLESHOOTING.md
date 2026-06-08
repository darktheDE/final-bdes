# Native Windows Big Data Stack: Troubleshooting Guide
## Quick Diagnostics & Workarounds

This guide compiles common errors encountered when running Hadoop, HDFS, YARN, MapReduce, MongoDB, and PySpark natively on Windows 10/11. Use these step-by-step solutions to debug deployment blocks quickly.

---

## 1. Hadoop & HDFS Common Issues

### Issue 1.1: `java.io.IOException: Could not locate executable null\bin\winutils.exe`
- **Symptoms**: PySpark or HDFS writes fail with a `null\bin\winutils.exe` pointer error.
- **Cause**: The `HADOOP_HOME` environment variable is either not set, set globally with a syntax error, or Spark/Hadoop cannot find `winutils.exe`.
- **Solution**:
  1. Ensure `winutils.exe` exists in your local project `tools/` folder (or `%HADOOP_HOME%\bin\`).
  2. If using `bin/run.bat`, verify it successfully binds `HADOOP_HOME` inside the active cmd session.
  3. Verify by running:
     ```cmd
     echo %HADOOP_HOME%
     dir %HADOOP_HOME%\bin\winutils.exe
     ```

### Issue 1.2: `org.apache.hadoop.security.AccessControlException: Permission denied`
- **Symptoms**: Cannot write files to HDFS or create directories (HTTP/RPC Permission denied).
- **Cause**: Windows local accounts do not map 1:1 with standard POSIX security permissions in HDFS. HDFS registers you under your Windows username, which might not match the Hadoop superuser.
- **Solution**:
  - **Quick Fix (Command Line)**: Force your terminal session to act as the Hadoop superuser before executing scripts:
    ```cmd
    set HADOOP_USER_NAME=hadoop
    :: Or use Administrator
    set HADOOP_USER_NAME=Administrator
    ```
  - **Permanent Fix (XML configuration)**: Disable HDFS permission checking inside `config/hadoop/hdfs-site.xml`:
    ```xml
    <property>
      <name>dfs.permissions.enabled</name>
      <value>false</value>
    </property>
    ```

---

## 2. YARN & MapReduce Stuck / Job Failures

### Issue 2.1: MapReduce Job stuck at 0% or failing on NodeManager launch
- **Symptoms**: YARN starts up, but your MapReduce job freezes indefinitely or fails immediately. Log shows virtual memory limit warnings.
- **Cause**: Windows reports virtual-to-physical memory allocation differently than Linux. Windows NodeManager virtual memory check usually triggers false positives, killing container allocations immediately.
- **Solution**: Add these virtual memory bypass configurations inside `config/hadoop/yarn-site.xml`:
  ```xml
  <property>
    <name>yarn.nodemanager.vmem-check-enabled</name>
    <value>false</value>
  </property>
  <property>
    <name>yarn.nodemanager.pmem-check-enabled</name>
    <value>false</value>
  </property>
  ```

### Issue 2.2: `The system cannot find the path specified` (Java path spaces)
- **Symptoms**: Hadoop command line crashes instantly upon execution.
- **Cause**: Your `JAVA_HOME` path contains spaces (e.g., `C:\Program Files\Java\jdk-11`).
- **Solution**:
  - Reinstall Java to a flat directory with no spaces (e.g., `C:\Java\jdk-11`).
  - Alternatively, use the Windows short path (8.3 format) in `hadoop-env.cmd`:
    ```cmd
    set JAVA_HOME=C:\PROGRA~1\Java\jdk-11
    ```

---

## 3. MongoDB Server Locks & Collisions

### Issue 3.1: MongoDB refuses to start: `mongod` exits immediately
- **Symptoms**: Running `mongod` yields code `100` or exits with log: `Unclean shutdown detected` or `Address already in use`.
- **Cause**: 
  - Another MongoDB background service is already running on port 27017.
  - A previous crash left a `.lock` file in the database folder.
- **Solution**:
  1. Kill any existing MongoDB processes:
     ```cmd
     taskkill /f /im mongod.exe
     ```
  2. If running MongoDB as a background Windows Service, stop it:
     ```cmd
     net stop MongoDB
     ```
  3. Delete the stubborn lock file inside your local database folder:
     ```cmd
     del "%~dp0..\data\db\mongod.lock"
     ```

---

## 4. PySpark & Streamlit Integration Errors

### Issue 4.1: Streamlit freezes or PySpark cannot bind loopback ports
- **Symptoms**: PySpark initialization hangs or throws port binding network exceptions.
- **Cause**: Local firewalls or VPN software (like Cisco AnyConnect, FortiClient) block local loopback ports (`127.0.0.1`).
- **Solution**:
  - Temporarily disable VPN services during active pipeline runs.
  - Set Spark's driver host bind address explicitly to localhost in Python code:
    ```python
    from pyspark.sql import SparkSession
    spark = SparkSession.builder \
        .master("local[*]") \
        .config("spark.driver.host", "127.0.0.1") \
        .getOrCreate()
    ```

---

## 5. Quick Windows CMD Commands (Cheat Sheet)

| Command Objective | Windows CMD Command |
| :--- | :--- |
| Check if port 27017 (MongoDB) is active | `netstat -ano \| findstr :27017` |
| Kill a process blocking port 27017 | `taskkill /pid <PID_NUMBER> /f` |
| View active local HDFS directories | `hdfs dfs -ls /` |
| Force clean HDFS temp storage | `hdfs dfs -rm -r -f /data/raw/*` |
```