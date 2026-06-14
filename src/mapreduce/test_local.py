import json
import os
import subprocess
import sys

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MEALS_JSON = os.path.join(BASE_DIR, 'src', 'crawler', 'seed', 'meals.json')
RESTAURANTS_JSON = os.path.join(BASE_DIR, 'src', 'crawler', 'tripadvisor_job', 'full_output.json')

TEMP_MEALS_JSONL = os.path.join(BASE_DIR, 'data', 'temp_meals_test.jsonl')
TEMP_REST_JSONL = os.path.join(BASE_DIR, 'data', 'temp_restaurants_test.jsonl')

def convert_json_to_jsonl(input_json_path, output_jsonl_path, limit=20):
    """Converts a standard JSON array file to a JSON Lines file with a limit of records."""
    if not os.path.exists(input_json_path):
        print(f"[!] Warning: Input file {input_json_path} does not exist.")
        return False
        
    with open(input_json_path, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except Exception as e:
            print(f"[!] Failed to parse {input_json_path}: {e}")
            return False
            
    # Clean up _id/id names if needed
    os.makedirs(os.path.dirname(output_jsonl_path), exist_ok=True)
    with open(output_jsonl_path, 'w', encoding='utf-8') as f:
        for item in data[:limit]:
            if '_id' in item:
                item['id'] = str(item.pop('_id'))
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
            
    print(f"[+] Converted {min(len(data), limit)} records to {output_jsonl_path}")
    return True

def run_local_job(script_path, input_path, extra_args=[]):
    """Runs a MapReduce job locally and returns output."""
    cmd = [sys.executable, script_path, input_path] + extra_args
    print(f"[*] Running: {' '.join(cmd)}")
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        print(f"[!] Job failed!")
        print(f"Stderr: {res.stderr}")
        return None
    return res.stdout

def main():
    print("=== Cycle 4: MapReduce Local Test Suite ===")
    
    # 1. Prepare temp JSONL test files
    print("\n[*] Preparing mock data...")
    if not convert_json_to_jsonl(MEALS_JSON, TEMP_MEALS_JSONL, limit=20):
        print("[!] Cannot generate mock meals. Exiting.")
        sys.exit(1)
        
    if not convert_json_to_jsonl(RESTAURANTS_JSON, TEMP_REST_JSONL, limit=20):
        print("[!] Cannot generate mock restaurants. Exiting.")
        sys.exit(1)
        
    # 2. Run and test all 8 jobs locally
    test_jobs = [
        {
            "name": "mr_rating_by_district.py",
            "script": "src/mapreduce/mr_rating_by_district.py",
            "input": TEMP_REST_JSONL,
            "args": []
        },
        {
            "name": "mr_cuisine_count.py",
            "script": "src/mapreduce/mr_cuisine_count.py",
            "input": TEMP_MEALS_JSONL,
            "args": []
        },
        {
            "name": "mr_price_segment.py",
            "script": "src/mapreduce/mr_price_segment.py",
            "input": TEMP_REST_JSONL,
            "args": []
        },
        {
            "name": "mr_sentiment_analysis.py",
            "script": "src/mapreduce/mr_sentiment_analysis.py",
            "input": TEMP_REST_JSONL,
            "args": []
        },
        {
            "name": "mr_ingredient_match.py",
            "script": "src/mapreduce/mr_ingredient_match.py",
            "input": TEMP_REST_JSONL,
            "args": ["--file", "src/crawler/seed/ingredients.json"]
        },
        {
            "name": "mr_top_reviewed.py",
            "script": "src/mapreduce/mr_top_reviewed.py",
            "input": TEMP_REST_JSONL,
            "args": []
        },
        {
            "name": "mr_review_distribution.py",
            "script": "src/mapreduce/mr_review_distribution.py",
            "input": TEMP_REST_JSONL,
            "args": []
        },
        {
            "name": "mr_delivery_analysis.py",
            "script": "src/mapreduce/mr_delivery_analysis.py",
            "input": TEMP_REST_JSONL,
            "args": []
        }
    ]
    
    all_passed = True
    for job in test_jobs:
        print(f"\n--- Testing: {job['name']} ---")
        output = run_local_job(job['script'], job['input'], job['args'])
        if output is not None:
            print("[+] Output:")
            # Print first 5 lines of output
            lines = output.strip().split('\n')
            for line in lines[:5]:
                print(f"    {line}")
            if len(lines) > 5:
                print(f"    ... and {len(lines) - 5} more lines.")
        else:
            all_passed = False
            
    # Cleanup temp files
    for path in [TEMP_MEALS_JSONL, TEMP_REST_JSONL]:
        if os.path.exists(path):
            os.remove(path)
            
    if all_passed:
        print("\n[+] SUCCESS: All 8 MapReduce jobs passed local inline tests successfully!")
    else:
        print("\n[!] FAILURE: Some MapReduce jobs failed local inline tests.")
        sys.exit(1)

if __name__ == "__main__":
    main()
