"""
test_hive_connection.py
-----------------------
Quick smoke-test: verify HiveServer2 is reachable on localhost:10000.

Usage (from project root, venv activated):
    python src/mapreduce/test_hive_connection.py
"""

import logging
import traceback

logging.basicConfig(level=logging.DEBUG)


def test_connection():
    """Attempt to connect to HiveServer2 and run a trivial query."""
    try:
        from pyhive import hive  # type: ignore
        print("Connecting to HiveServer2 (localhost:10000)...")
        conn = hive.connect(host="localhost", port=10000, database="food_sentiment_db")
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        print("✅ Connection successful!")
        cursor.close()
        conn.close()
    except Exception:
        print("\n❌ Connection FAILED. Full traceback:")
        traceback.print_exc()


if __name__ == "__main__":
    test_connection()
