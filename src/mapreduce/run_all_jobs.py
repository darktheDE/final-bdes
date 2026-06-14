import subprocess
import sys
import os

# Configuration
PYTHON_BIN = "/mnt/d/Project/final-bdes/venv/bin/python3"
HDFS_RAW_RESTAURANTS = "hdfs:///data/raw/restaurants/restaurants.jsonl"
HDFS_RAW_MEALS = "hdfs:///data/raw/meals/meals.jsonl"
HDFS_OUTPUT_DIR = "/data/output"

JOBS = [
    {
        "name": "Rating by District",
        "script": "src/mapreduce/mr_rating_by_district.py",
        "input": HDFS_RAW_RESTAURANTS,
        "output": f"{HDFS_OUTPUT_DIR}/mr_rating_by_district",
        "extra_args": []
    },
    {
        "name": "Cuisine Count",
        "script": "src/mapreduce/mr_cuisine_count.py",
        "input": HDFS_RAW_MEALS,
        "output": f"{HDFS_OUTPUT_DIR}/mr_cuisine_count",
        "extra_args": []
    },
    {
        "name": "Rating Bucket",
        "script": "src/mapreduce/mr_rating_bucket.py",
        "input": HDFS_RAW_RESTAURANTS,
        "output": f"{HDFS_OUTPUT_DIR}/mr_rating_bucket",
        "extra_args": []
    },
    {
        "name": "Sentiment Analysis",
        "script": "src/mapreduce/mr_sentiment_analysis.py",
        "input": HDFS_RAW_RESTAURANTS,
        "output": f"{HDFS_OUTPUT_DIR}/mr_sentiment_analysis",
        "extra_args": []
    },
    {
        "name": "Ingredient Match",
        "script": "src/mapreduce/mr_ingredient_match.py",
        "input": HDFS_RAW_RESTAURANTS,
        "output": f"{HDFS_OUTPUT_DIR}/mr_ingredient_match",
        "extra_args": ["--file", "src/crawler/seed/ingredients.json"]
    },
    {
        "name": "Top Reviewed",
        "script": "src/mapreduce/mr_top_reviewed.py",
        "input": HDFS_RAW_RESTAURANTS,
        "output": f"{HDFS_OUTPUT_DIR}/mr_top_reviewed",
        "extra_args": []
    },
    {
        "name": "Review Distribution",
        "script": "src/mapreduce/mr_review_distribution.py",
        "input": HDFS_RAW_RESTAURANTS,
        "output": f"{HDFS_OUTPUT_DIR}/mr_review_distribution",
        "extra_args": []
    },
    {
        "name": "Delivery Analysis",
        "script": "src/mapreduce/mr_delivery_analysis.py",
        "input": HDFS_RAW_RESTAURANTS,
        "output": f"{HDFS_OUTPUT_DIR}/mr_delivery_analysis",
        "extra_args": []
    }
]

def run_cmd(args):
    print(f"[*] Executing: {' '.join(args)}")
    res = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        print(f"[!] Command failed!")
        print(f"Stderr: {res.stderr}")
        return False
    return True

def print_summary(job_name, output_dir):
    print(f"\n--- Summary for {job_name} ---")
    cat_cmd = ["hdfs", "dfs", "-cat", f"{output_dir}/part-*"]
    res = subprocess.run(cat_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        print("  [!] Could not read output from HDFS.")
        return
    
    lines = res.stdout.strip().split('\n')
    if not lines or lines == ['']:
        print("  No output records found.")
        return
        
    print(f"  Total Output Records: {len(lines)}")
    
    # Parse json/tsv lines
    parsed_records = []
    for line in lines:
        parts = line.split('\t', 1)
        if len(parts) == 2:
            try:
                import json
                key = json.loads(parts[0])
                val = json.loads(parts[1])
                parsed_records.append((key, val))
            except:
                parsed_records.append((parts[0], parts[1]))
                
    print("  Sample Results (up to 10):")
    for i, (k, v) in enumerate(parsed_records[:10]):
        print(f"    {i+1}. {k}: {v}")
    print("-" * 40 + "\n")

def main():
    print("=== Triggering all 8 MapReduce jobs on Hadoop ===")
    
    # Ensure setuptools is active
    for job in JOBS:
        print(f"\n--- Running Job: {job['name']} ---")
        
        # 1. Clean up HDFS output directory if it exists to prevent mrjob error
        clean_args = ["hdfs", "dfs", "-rm", "-r", "-f", job['output']]
        subprocess.run(clean_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # 2. Construct mrjob command
        cmd = [
            PYTHON_BIN, job['script'],
            "-r", "hadoop",
            "-c", "conf/mrjob.conf",
            "--python-bin", PYTHON_BIN,
            job['input'],
            "--output-dir", job['output']
        ] + job['extra_args']
        
        success = run_cmd(cmd)
        if not success:
            print(f"[!] MapReduce Job '{job['name']}' failed. Exiting.")
            sys.exit(1)
            
        # 3. Print summary
        print_summary(job['name'], job['output'])
            
    print("\n[+] All 8 MapReduce jobs completed successfully on Hadoop!")

if __name__ == "__main__":
    main()
