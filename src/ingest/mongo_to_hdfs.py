import os
import sys
import json
import subprocess
import pymongo
from bson import ObjectId

# MongoDB Configuration
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "sentiment_db"

# Workspace Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEMP_DIR = os.path.join(BASE_DIR, 'data', 'temp')

# HDFS Path
HDFS_RAW_DIR = "/data/raw"

class MongoJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle BSON ObjectIds and complex MongoDB datatypes."""
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return super().default(o)

def export_collection_to_jsonl(db, collection_name, local_filepath):
    """Reads all records from a Mongo collection and writes them to a local JSONL file."""
    print(f"[*] Exporting collection '{collection_name}' from MongoDB...")
    coll = db[collection_name]
    
    count = 0
    with open(local_filepath, 'w', encoding='utf-8') as f:
        for doc in coll.find({}):
            # Convert _id to id for Hive compatibility
            if '_id' in doc:
                doc['id'] = str(doc.pop('_id'))
            json_line = json.dumps(doc, cls=MongoJSONEncoder, ensure_ascii=False)
            f.write(json_line + '\n')
            count += 1
            
    print(f"  -> Exported {count} records to {local_filepath}")
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
    print("=== MongoDB to HDFS Ingestion Pipeline ===")
    
    # Ensure local temp directory exists inside workspace
    os.makedirs(TEMP_DIR, exist_ok=True)
    
    try:
        # Connect to MongoDB
        print(f"[*] Connecting to MongoDB at {MONGO_URI}...")
        client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        db = client[DB_NAME]
    except Exception as e:
        print(f"[!] MongoDB connection failed: {e}")
        print("[!] Ensure MongoDB daemon is active (sudo service mongod start).")
        sys.exit(1)
        
    collections_to_sync = {
        'restaurants': ('restaurants', 'restaurants.jsonl'),
        'meals': ('meals', 'meals.jsonl')
    }
    
    for coll_name, (hdfs_subdir, hdfs_name) in collections_to_sync.items():
        local_path = os.path.join(TEMP_DIR, hdfs_name)
        try:
            # 1. Export locally
            count = export_collection_to_jsonl(db, coll_name, local_path)
            if count == 0:
                print(f"  [!] Warning: Collection '{coll_name}' is empty. Skipping upload.")
                continue
                
            # 2. Upload to HDFS
            upload_to_hdfs(local_path, hdfs_subdir, hdfs_name)

            
            # 3. Clean up local temp file
            if os.path.exists(local_path):
                os.remove(local_path)
                print(f"  -> Cleaned up local temporary file: {local_path}")
                
        except Exception as err:
            print(f"[!] Error syncing collection '{coll_name}': {err}")
            # Clean up temp file in case of error
            if os.path.exists(local_path):
                os.remove(local_path)
            sys.exit(1)
            
    print("[+] MongoDB to HDFS Ingestion completed successfully.")

if __name__ == "__main__":
    main()
