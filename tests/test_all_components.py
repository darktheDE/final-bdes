"""
test_all_components.py
-----------------------
Automated Integration Test Suite for the Food & Restaurant Sentiment Analysis System.
Validates environment, infrastructure services, databases, HDFS, Hive, MapReduce, and backups.

Usage:
    python tests/test_all_components.py
"""

import os
import re
import socket
import subprocess
import sys
import tempfile
import traceback

# Constants
MONGO_URI = "mongodb://localhost:27017/"
MYSQL_CONFIG = {
    'user': 'root',
    'password': '',
    'host': '127.0.0.1',
    'port': 3306
}
MYSQL_DB_NAME = "food_sentiment_db"
MONGO_DB_NAME = "sentiment_db"

def check_port(port: int) -> bool:
    """Check if a specific port is active and listening on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1.0)
        try:
            s.connect(('127.0.0.1', port))
            return True
        except (socket.timeout, ConnectionRefusedError):
            return False

def test_ports():
    """Verify that essential service ports are listening."""
    print("\n--- [1] Checking Service Ports ---")
    ports = {
        3306: "MySQL Database",
        27017: "MongoDB Database",
        9000: "Hadoop NameNode",
        10000: "HiveServer2 (Thrift)",
        8501: "Streamlit App Server"
    }
    
    all_ok = True
    for port, name in ports.items():
        active = check_port(port)
        status = "✅ ACTIVE" if active else "❌ INACTIVE"
        print(f"  Port {port:<5} ({name:<25}): {status}")
        if port != 8501 and not active:  # Streamlit might not be running in headless tests
            # Don't fail the whole test just for Streamlit, but fail for critical infra
            if port != 10000: # HiveServer2 could be offline but we can fallback
                all_ok = False
            else:
                print("  [!] Warning: HiveServer2 is not running. Subprocess fallback will be tested.")
                
    return all_ok

def test_mongodb():
    """Verify MongoDB connection and collections."""
    print("\n--- [2] Checking MongoDB Ingestion ---")
    try:
        import pymongo
        client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
        # Ping
        client.admin.command('ping')
        print("  ✅ MongoDB connection: SUCCESS")
        
        db = client[MONGO_DB_NAME]
        collections = db.list_collection_names()
        print(f"  Found collections: {collections}")
        
        for col_name in ['restaurants', 'meals']:
            if col_name in collections:
                count = db[col_name].count_documents({})
                print(f"    - Collection '{col_name}': {count} documents")
                if count == 0:
                    print(f"    ⚠️ Warning: Collection '{col_name}' is empty.")
            else:
                print(f"    ❌ Error: Collection '{col_name}' is missing.")
                return False
        client.close()
        return True
    except Exception as e:
        print(f"  ❌ MongoDB verification failed: {e}")
        return False

def test_mysql():
    """Verify MySQL tables, schema and record count."""
    print("\n--- [3] Checking MySQL Clean Data ---")
    try:
        import mysql.connector
        
        # Connect
        conn = None
        for pw in ['', 'root']:
            try:
                config = MYSQL_CONFIG.copy()
                config['password'] = pw
                config['database'] = MYSQL_DB_NAME
                conn = mysql.connector.connect(**config)
                break
            except mysql.connector.Error:
                continue
                
        if not conn:
            print("  ❌ MySQL connection: FAILED (Cannot login with root or root/root)")
            return False
            
        print("  ✅ MySQL connection: SUCCESS")
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SHOW TABLES;")
        tables = [t[0] for t in cursor.fetchall()]
        print(f"  Found tables: {tables}")
        
        expected_tables = ['restaurants', 'reviews', 'meals']
        for table in expected_tables:
            if table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table};")
                count = cursor.fetchone()[0]
                print(f"    - Table '{table}': {count} records")
                if count == 0:
                    print(f"    ⚠️ Warning: Table '{table}' has 0 records.")
            else:
                print(f"    ❌ Error: Table '{table}' is missing.")
                cursor.close()
                conn.close()
                return False
                
        # Check district_parsed
        cursor.execute("SELECT COUNT(*) FROM restaurants WHERE district_parsed = 'Unknown';")
        unknown_districts = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM restaurants;")
        total_rests = cursor.fetchone()[0]
        
        if total_rests > 0:
            unknown_ratio = unknown_districts / total_rests
            print(f"    - Parse Ratio: {total_rests - unknown_districts}/{total_rests} districts parsed.")
            if unknown_ratio > 0.8:
                print("    ⚠️ Warning: More than 80% of districts parsed as 'Unknown'. Check parsing logic.")
                
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"  ❌ MySQL verification failed: {e}")
        return False

def test_hdfs():
    """Verify HDFS directory structure and data files."""
    print("\n--- [4] Checking Hadoop HDFS Storage ---")
    try:
        # Check hdfs cmd
        res = subprocess.run(["which", "hdfs"], capture_output=True, text=True)
        if res.returncode != 0:
            print("  ❌ Hadoop HDFS: 'hdfs' command not found in PATH.")
            return False
            
        print("  ✅ Hadoop HDFS CLI: FOUND")
        
        # Check files
        files_to_check = [
            "/data/raw/restaurants/restaurants.jsonl",
            "/data/raw/meals/meals.jsonl"
        ]
        
        all_present = True
        for hdfs_path in files_to_check:
            # test -e returns 0 if file exists
            res = subprocess.run(["hdfs", "dfs", "-test", "-e", hdfs_path], capture_output=True)
            if res.returncode == 0:
                print(f"    - File '{hdfs_path}': ✅ EXISTS")
            else:
                print(f"    - File '{hdfs_path}': ❌ MISSING")
                all_present = False
                
        return all_present
    except Exception as e:
        print(f"  ❌ HDFS verification failed: {e}")
        return False

def test_hive():
    """Verify Apache Hive Metastore connection and analytics views."""
    print("\n--- [5] Checking Apache Hive DW ---")
    try:
        # Check mode in hive_connector
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from src.streamlit_app import hive_connector
        
        hive_connector.reset_connection_cache()
        status = hive_connector.get_hive_status()
        print(f"  Hive Connection Mode Resolved: {status.upper()}")
        
        if status == "offline":
            print("  ❌ Hive server/CLI is completely offline.")
            return False
            
        # Try running a quick test query on views
        views = [
            "view_rating_by_district",
            "view_cuisine_frequency",
            "view_review_distribution"
        ]
        
        all_views_ok = True
        for view in views:
            sql = f"SELECT * FROM {view} LIMIT 2"
            df = hive_connector.query_hive(sql)
            if not df.empty:
                print(f"    - View '{view}': ✅ READ SUCCESS ({len(df)} rows returned)")
            else:
                print(f"    - View '{view}': ❌ EMPTY OR READ FAILED")
                all_views_ok = False
                
        return all_views_ok
    except Exception as e:
        print(f"  ❌ Hive verification failed: {e}")
        traceback.print_exc()
        return False

def test_mapreduce_smoke():
    """Smoke test MapReduce locally using a subset of mock records."""
    print("\n--- [6] Running MapReduce Local Smoke Test ---")
    
    # Check if mrjob is installed
    try:
        import mrjob
        print("  ✅ mrjob library: INSTALLED")
    except ImportError:
        print("  ❌ mrjob library: NOT INSTALLED")
        return False
        
    mock_data = (
        '{"id": "rest_1", "name": "Test Rest 1", "rating": 5.0, "review_count": 10, "district": "18B/17 Đ. Nguyễn Thị Minh Khai Quận 1", "city": "Ho Chi Minh City", "reviews": []}\n'
        '{"id": "rest_2", "name": "Test Rest 2", "rating": 4.0, "review_count": 20, "district": "Phường Bến Nghé, Quận 1", "city": "Ho Chi Minh City", "reviews": []}\n'
        '{"id": "rest_3", "name": "Test Rest 3", "rating": 3.0, "review_count": 5, "district": "Quận 3, HCMC", "city": "Ho Chi Minh City", "reviews": []}\n'
    )
    
    try:
        # Create temp input
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write(mock_data)
            temp_path = f.name
            
        script_path = "src/mapreduce/mr_rating_by_district.py"
        print(f"  Running {script_path} locally on mock data...")
        
        # Run local MapReduce job as a subprocess
        cmd = [sys.executable, script_path, temp_path]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Clean up temp
        try:
            os.remove(temp_path)
        except OSError:
            pass
            
        if res.returncode != 0:
            print(f"  ❌ MapReduce job execution failed with exit code {res.returncode}")
            print(f"  Stderr: {res.stderr}")
            return False
            
        # Parse output: keys/values are tab-separated
        results = {}
        import json
        for line in res.stdout.strip().split('\n'):
            if not line.strip():
                continue
            parts = line.split('\t')
            if len(parts) == 2:
                try:
                    key_str = json.loads(parts[0])
                except Exception:
                    key_str = parts[0].strip('"')
                try:
                    val = json.loads(parts[1])
                    results[key_str] = val
                except Exception:
                    pass
                    
        print(f"  MapReduce Results: {results}")
        
        # Verify aggregation: Quận 1 average rating should be (5.0 + 4.0)/2 = 4.5
        if "Quận 1" in results:
            avg_rating = results["Quận 1"]["avg_rating"]
            restaurant_count = results["Quận 1"]["restaurant_count"]
            if abs(avg_rating - 4.5) < 0.1 and restaurant_count == 2:
                print("  ✅ MapReduce aggregation test: PASS")
                return True
            else:
                print(f"  ❌ MapReduce aggregated ratings incorrect: {results['Quận 1']}")
                return False
        else:
            print("  ❌ MapReduce district key 'Quận 1' missing from results.")
            return False
            
    except Exception as e:
        print(f"  ❌ MapReduce smoke test failed: {e}")
        traceback.print_exc()
        return False

def test_backup_restore():
    """Verify backup functionality (smoke test backup script)."""
    print("\n--- [7] Checking DevOps Backup & Recovery ---")
    backup_script = "src/backup/db_backup.sh"
    
    if not os.path.exists(backup_script):
        print(f"  ❌ Backup script not found at: {backup_script}")
        return False
        
    try:
        print("  Running db_backup.sh script...")
        # Run backup
        res = subprocess.run(["bash", backup_script], capture_output=True, text=True, timeout=60)
        
        if res.returncode == 0:
            print("  ✅ Backup script execution: SUCCESS")
            # Verify backup directory contains timestamp files
            backup_dir = "data/backups"
            if os.path.exists(backup_dir):
                backups = os.listdir(backup_dir)
                print(f"  Found backup entries: {backups}")
                if len(backups) > 0:
                    print("  ✅ Backup file verification: PASS")
                    return True
            print("  ❌ Backup directory is empty or missing.")
            return False
        else:
            print(f"  ❌ Backup script failed with return code {res.returncode}")
            print(f"  Stderr: {res.stderr}")
            return False
    except Exception as e:
        print(f"  ❌ Backup verification failed: {e}")
        return False

def main():
    print("==============================================================")
    print("  Food & Restaurant Sentiment Analysis System Integration Tests")
    print("==============================================================")
    
    tests = [
        ("Service Ports", test_ports),
        ("MongoDB Collection", test_mongodb),
        ("MySQL Clean Data", test_mysql),
        ("Hadoop HDFS Storage", test_hdfs),
        ("Apache Hive DW Connection", test_hive),
        ("MapReduce Job Smoke Test", test_mapreduce_smoke),
        ("DevOps Backup Execution", test_backup_restore)
    ]
    
    results = []
    for name, test_func in tests:
        success = False
        try:
            success = test_func()
        except Exception as e:
            print(f"  ❌ Unexpected error during {name}: {e}")
            
        results.append((name, success))
        
    print("\n==============================================================")
    print("  INTEGRATION TEST SUMMARY TABLE")
    print("==============================================================")
    all_passed = True
    for name, success in results:
        status = "PASS ✅" if success else "FAIL ❌"
        print(f"  {name:<30}: {status}")
        if not success:
            all_passed = False
            
    print("==============================================================")
    if all_passed:
        print("  🎉 SUCCESS: All component tests passed successfully!")
        sys.exit(0)
    else:
        print("  ❌ FAILURE: Some components did not pass tests.")
        sys.exit(1)

if __name__ == "__main__":
    main()
