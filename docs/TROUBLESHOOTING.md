# Ubuntu WSL2 Big Data Stack: Troubleshooting Guide
## Quick Diagnostics & Workarounds (Ubuntu 24.04 LTS)

This guide compiles common errors encountered when running Hadoop, HDFS, YARN, MapReduce, MongoDB, and PySpark natively on Ubuntu 24.04 LTS within a Windows Subsystem for Linux (WSL2) environment.

---

## 1. Hadoop & HDFS Common Issues

### Issue 1.1: `ssh: connect to host localhost port 22: Connection refused`
- **Symptoms**: When starting HDFS (`start-dfs.sh`), the script halts or complains about connection refusal on port 22.
- **Cause**: The SSH server daemon (`sshd`) is not running on WSL2, or keyless login is not configured.
- **Solution**:
  1. Install SSH Server:
     ```bash
     sudo apt update
     sudo apt install openssh-server -y
     ```
  2. Start SSH Daemon:
     ```bash
     sudo service ssh start
     ```
  3. Configure keyless authentication:
     ```bash
     ssh-keygen -t rsa -P '' -f ~/.ssh/id_rsa
     cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
     chmod 0600 ~/.ssh/authorized_keys
     ```
  4. Verify by running `ssh localhost` (should log in without prompting for a password).

### Issue 1.2: `java.lang.IllegalArgumentException: Server has invalid Kerberos principal name` or NameNode starts and dies
- **Symptoms**: Hadoop processes terminate shortly after launch. Log shows name resolution or directory permission issues.
- **Cause**: WSL2's dynamic IP assignment or lack of proper `/etc/hosts` mappings, or permission mismatches when accessing files mounted from `/mnt/c/`.
- **Solution**:
  - Keep HDFS directories native to the Linux filesystem (e.g., `/home/username/data/hdfs` or `/usr/local/hadoop/data/`) instead of mounting them to Windows drives.
  - Disable permissions checks inside `/usr/local/hadoop/etc/hadoop/hdfs-site.xml` for local development:
    ```xml
    <property>
      <name>dfs.permissions.enabled</name>
      <value>false</value>
    </property>
    ```

---

## 2. MongoDB Daemon Issues

### Issue 2.1: `System has not been booted with systemd as init system (PID 1). Can't operate.`
- **Symptoms**: Running `sudo systemctl start mongod` fails with systemd init failure.
- **Cause**: WSL2 does not enable `systemd` by default in older installations.
- **Solution**:
  - **Option 1 (Quick Fix)**: Launch MongoDB using the SysV init script instead of systemd:
    ```bash
    sudo service mongod start
    ```
  - **Option 2 (Permanent systemd enablement)**: Open `/etc/wsl.conf` (create it if missing) and configure:
    ```ini
    [boot]
    systemd=true
    ```
    Then, open PowerShell on Windows and restart WSL:
    ```powershell
    wsl --shutdown
    ```

### Issue 2.2: MongoDB fails to start, showing `mongod.lock` or unclean shutdown
- **Symptoms**: MongoDB log indicates failure to lock files or directory `/data/db` is unwritable.
- **Cause**: MongoDB daemon does not have read/write access to `/var/lib/mongodb` or clean lock files weren't removed.
- **Solution**:
  1. Fix permissions:
     ```bash
     sudo chown -R mongodb:mongodb /var/lib/mongodb
     sudo chown -R mongodb:mongodb /var/log/mongodb
     ```
  2. Clear lock files:
     ```bash
     sudo rm -f /var/lib/mongodb/mongod.lock
     ```
  3. Launch service:
     ```bash
     sudo service mongod start
     ```

---

## 3. Python & Dependency Issues

### Issue 3.1: `ModuleNotFoundError: No module named 'distutils'`
- **Symptoms**: PySpark or other ML packages crash during execution or initialization under Python 3.12.
- **Cause**: Python 3.12 (the default Python on Ubuntu 24.04) removed the `distutils` library.
- **Solution**:
  - Downgrade the virtual environment runtime to Python 3.10 or 3.11.
  - Use the Deadsnakes PPA to install Python 3.10 on Ubuntu 24.04:
    ```bash
    sudo add-apt-repository ppa:deadsnakes/ppa -y
    sudo apt update
    sudo apt install python3.10 python3.10-venv python3.10-dev -y
    ```
  - Re-create the virtual environment:
    ```bash
    python3.10 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

---

## 4. UI Access & Port Forwarding

### Issue 4.1: Streamlit `localhost:8501` is not reachable from the Windows browser
- **Symptoms**: Streamlit boots inside WSL2 terminal but cannot be viewed inside Chrome/Edge on Windows.
- **Cause**: WSL2 network interface binding is restricted, or firewall is blocking the local routing.
- **Solution**:
  - WSL2 automatically maps `localhost` from Windows to WSL2. If this fails, find the WSL2 IP:
    ```bash
    ip addr show eth0 | grep inet
    ```
    Then navigate to `http://<WSL_IP>:8501` on your Windows browser.
  - Ensure Streamlit is run with broad binding option:
    ```bash
    streamlit run src/streamlit_app/app.py --server.address 0.0.0.0
    ```