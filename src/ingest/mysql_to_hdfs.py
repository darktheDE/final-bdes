import os
import sys
import json
import subprocess
import mysql.connector
from decimal import Decimal

# MySQL Configuration
MYSQL_CONFIG = {
    'user': 'root',
    'password': '',
    'host': '127.0.0.1',
    'port': 3306,
    'database': 'food_sentiment_db'
}

# Workspace Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEMP_DIR = os.path.join(BASE_DIR, 'data', 'temp')

# HDFS Path
HDFS_RAW_DIR = "/data/raw"

class MySQLJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle MySQL Decimal, date, and time values."""
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super().default(o)

def export_table_to_jsonl(conn, table_name, local_filepath):
    """Reads all rows from a MySQL table and writes them to a local JSONL file."""
    print(f"[*] Exporting table '{table_name}' from MySQL...")
    cursor = conn.cursor(dictionary=True)
    
    query = f"SELECT * FROM `{table_name}`"
    cursor.execute(query)
    
    count = 0
    with open(local_filepath, 'w', encoding='utf-8') as f:
        row = cursor.fetchone()
        while row is not None:
            json_line = json.dumps(row, cls=MySQLJSONEncoder, ensure_ascii=False)
            f.write(json_line + '\n')
            count += 1
            row = cursor.fetchone()
            
    cursor.close()
    print(f"  -> Exported {count} rows to {local_filepath}")
    return count

def upload_to_hdfs(local_filepath, hdfs_subdir, hdfs_filename):
    """Executes HDFS commands to create raw dir and put file on Hadoop HDFS."""
    target_dir = f"{HDFS_RAW_DIR}/{hdfs_subdir}"
    hdfs_target_path = f"{target_dir}/{hdfs_filename}"
    print(f"[*] Uploading {local_filepath} to HDFS at {hdfs_target_path}...")
    
    # 1. Create HDFS directory if not exists
    mkdir_cmd = ["hdfs", "dfs", "-mkdir", "-p", target_dir]
    put_cmd = ["hdfs", "dfs", "-put", "-f", local_filepath, hdfs_target_path]
    
    try:
        # Run mkdir
        subprocess.run(mkdir_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # Run put
        subprocess.run(put_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"  -> Successfully uploaded {hdfs_filename} to HDFS.")
        
        # Verify file exists on HDFS
        ls_cmd = ["hdfs", "dfs", "-ls", hdfs_target_path]
        res = subprocess.run(ls_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print(f"  -> HDFS Stat: {res.stdout.strip()}")
        
    except subprocess.CalledProcessError as e:
        print(f"[!] HDFS Command Failed!")
        print(f"    Command: {' '.join(e.cmd)}")
        print(f"    Stderr: {e.stderr.decode('utf-8')}")
        raise RuntimeError("Failed to interact with HDFS. Ensure Hadoop services are running.") from e

def main():
    print("=== MySQL to HDFS Ingestion Pipeline ===")
    
    # Ensure local temp directory exists inside workspace
    os.makedirs(TEMP_DIR, exist_ok=True)
    
    try:
        # Connect to MySQL
        print(f"[*] Connecting to MySQL Database '{MYSQL_CONFIG['database']}'...")
        conn = mysql.connector.connect(**MYSQL_CONFIG)
    except mysql.connector.Error as err:
        print(f"[!] MySQL connection failed: {err}")
        print("[!] Ensure MySQL service is active (sudo service mysql start).")
        sys.exit(1)
        
    tables_to_sync = {
        'restaurants': ('mysql_restaurants', 'mysql_restaurants.jsonl'),
        'reviews': ('mysql_reviews', 'mysql_reviews.jsonl'),
        'meals': ('mysql_meals', 'mysql_meals.jsonl')
    }
    
    for table_name, (hdfs_subdir, hdfs_name) in tables_to_sync.items():
        local_path = os.path.join(TEMP_DIR, hdfs_name)
        try:
            # 1. Export locally
            count = export_table_to_jsonl(conn, table_name, local_path)
            if count == 0:
                print(f"  [!] Warning: Table '{table_name}' is empty. Skipping upload.")
                continue
                
            # 2. Upload to HDFS
            upload_to_hdfs(local_path, hdfs_subdir, hdfs_name)

            
            # 3. Clean up local temp file
            if os.path.exists(local_path):
                os.remove(local_path)
                print(f"  -> Cleaned up local temporary file: {local_path}")
                
        except Exception as err:
            print(f"[!] Error syncing table '{table_name}': {err}")
            # Clean up temp file in case of error
            if os.path.exists(local_path):
                os.remove(local_path)
            sys.exit(1)
            
    conn.close()
    print("[+] MySQL to HDFS Ingestion completed successfully.")

if __name__ == "__main__":
    main()
