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
        "name": "Price Segment",
        "script": "src/mapreduce/mr_price_segment.py",
        "input": HDFS_RAW_RESTAURANTS,
        "output": f"{HDFS_OUTPUT_DIR}/mr_price_segment",
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
            "--python-bin", PYTHON_BIN,
            job['input'],
            "--output-dir", job['output']
        ] + job['extra_args']
        
        success = run_cmd(cmd)
        if not success:
            print(f"[!] MapReduce Job '{job['name']}' failed. Exiting.")
            sys.exit(1)
            
    print("\n[+] All 8 MapReduce jobs completed successfully on Hadoop!")

if __name__ == "__main__":
    main()
