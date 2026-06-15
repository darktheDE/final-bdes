import logging
import traceback
from pyhive import hive

logging.basicConfig(level=logging.DEBUG)

def test_connection():
    try:
        print("Đang thử kết nối HiveServer2 (localhost:10000)...")
        conn = hive.connect(host="localhost", port=10000, database="food_sentiment_db")
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        print("✅ Kết nối thành công!")
        cursor.close()
        conn.close()
    except Exception as e:
        print("\n❌ KẾT NỐI THẤT BẠI. Chi tiết lỗi:")
        traceback.print_exc()

if __name__ == "__main__":
    test_connection()
