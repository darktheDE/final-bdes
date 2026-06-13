import os
import sys
import time
import urllib.request
import subprocess
import shutil

hive_url = "https://archive.apache.org/dist/hive/hive-3.1.3/apache-hive-3.1.3-bin.tar.gz"
hive_dest = "/tmp/apache-hive-3.1.3-bin.tar.gz"
expected_hive_size = 301292150  # Let's verify size later or check if non-zero

mysql_jar_url = "https://repo1.maven.org/maven2/com/mysql/mysql-connector-j/8.3.0/mysql-connector-j-8.3.0.jar"
mysql_jar_dest = "/tmp/mysql-connector-j-8.3.0.jar"

def download_file(url, dest):
    print(f"Downloading {url} to {dest}...")
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as response, open(dest, 'wb') as f:
            chunk_size = 1024 * 1024
            downloaded = 0
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                print(f"\rDownloaded {downloaded} bytes...", end="", flush=True)
            print()
        return True
    except Exception as e:
        print(f"\nError downloading {url}: {e}")
        return False

# 1. Download Hive
if not os.path.exists(hive_dest) or os.path.getsize(hive_dest) < 100000000:
    if not download_file(hive_url, hive_dest):
        print("Failed to download Hive.")
        sys.exit(1)

# 2. Download MySQL Connector
if not os.path.exists(mysql_jar_dest):
    if not download_file(mysql_jar_url, mysql_jar_dest):
        print("Failed to download MySQL connector.")
        sys.exit(1)

# 3. Extract Hive
print("Extracting Hive...")
if os.path.exists("/usr/local/hive"):
    shutil.rmtree("/usr/local/hive")
if os.path.exists("/usr/local/apache-hive-3.1.3-bin"):
    shutil.rmtree("/usr/local/apache-hive-3.1.3-bin")

subprocess.run(["tar", "-xzf", hive_dest, "-C", "/usr/local/"], check=True)
shutil.move("/usr/local/apache-hive-3.1.3-bin", "/usr/local/hive")
import getpass
current_user = getpass.getuser()
subprocess.run(["chown", "-R", f"{current_user}:{current_user}", "/usr/local/hive"], check=True)

# 4. Configure env in .bashrc
print("Configuring ~/.bashrc for Hive...")
bashrc_path = os.path.expanduser("~/.bashrc")
env_vars = [
    'export HIVE_HOME=/usr/local/hive\n',
    'export PATH=$PATH:$HIVE_HOME/bin\n'
]
with open(bashrc_path, "r") as f:
    bashrc_content = f.read()

# Put them at the top as well
with open(bashrc_path, "w") as f:
    f.writelines(env_vars + [bashrc_content])

# 5. Copy MySQL Connector Jar to Hive lib
print("Copying MySQL connector to Hive lib...")
shutil.copy(mysql_jar_dest, "/usr/local/hive/lib/mysql-connector-j-8.3.0.jar")

# 6. Fix Guava version mismatch
print("Fixing Guava mismatch...")
if os.path.exists("/usr/local/hive/lib/guava-19.0.jar"):
    os.remove("/usr/local/hive/lib/guava-19.0.jar")

# Find guava in hadoop
hadoop_guava_src = "/usr/local/hadoop/share/hadoop/common/lib/guava-27.0-jre.jar"
if os.path.exists(hadoop_guava_src):
    shutil.copy(hadoop_guava_src, "/usr/local/hive/lib/guava-27.0-jre.jar")
    print("Copied Hadoop's guava-27.0-jre.jar to Hive.")
else:
    # Look for any guava jar in hadoop common
    lib_dir = "/usr/local/hadoop/share/hadoop/common/lib"
    found = False
    for filename in os.listdir(lib_dir):
        if filename.startswith("guava-") and filename.endswith(".jar"):
            shutil.copy(os.path.join(lib_dir, filename), "/usr/local/hive/lib/" + filename)
            print(f"Copied {filename} to Hive.")
            found = True
            break
    if not found:
        print("Warning: Guava jar not found in Hadoop common lib!")

# 7. Write hive-site.xml
print("Writing hive-site.xml...")
hive_site_content = '''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
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
        <value>root</value>
    </property>
    <property>
        <name>javax.jdo.option.ConnectionPassword</name>
        <value></value>
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
'''
with open("/usr/local/hive/conf/hive-site.xml", "w") as f:
    f.write(hive_site_content)

print("Hive installation and configuration completed successfully!")
