# VAI TRÒ 2: HADOOP INFRASTRUCTURE & DATA SYNC - Trần Thị B

**Mục tiêu chính:** Đồng bộ dữ liệu từ MySQL/MongoDB lên HDFS, quản lý Apache Hive  
**Điểm đạo được:** 1.00 điểm (HDFS, YARN, Hive)

---

## 1. GIỚI THIỆU TỔNG QUÁT

### Vai trò trong Pipeline Dữ liệu

Hadoop Infrastructure Engineer là **cầu nối giữa OLTP (Transactional) và OLAP (Analytical)**. Bạn chịu trách nhiệm:

1. **Đồng bộ dữ liệu từ staging DBMS → HDFS** (MySQL/MongoDB → JSONL files)
2. **Quản lý HDFS** (tạo directories, upload files, verify)
3. **Cấu hình Apache Hive** (external tables, SQL views cho analytics)
4. **Đảm bảo data integrity** (checksum, replication)

Dữ liệu bạn xử lý là **raw source** cho các MapReduce jobs chạy trên Hadoop.

### Tại sao chọn công nghệ này?

| Công nghệ              | Lý do chọn                                                                                                               |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| **Apache Hadoop HDFS** | Distributed file system cho big data. Replicate data across nodes (default 3 copies). Optimize cho batch processing lớn. |
| **Apache YARN**        | Resource manager để schedule MapReduce jobs. Allocate memory/CPU động. Fair sharing giữa multiple jobs.                  |
| **Apache Hive**        | SQL interface trên top HDFS data. User không cần học MapReduce, chỉ cần SQL quen thuộc.                                  |
| **JSON Lines format**  | Mỗi dòng = 1 JSON document. Hive parse được dễ dàng. Compact hơn CSV, đầy đủ thông tin.                                  |
| **MySQL → JSONL**      | Flat relational tables chuyển sang semi-structured JSONL để Hive query.                                                  |
| **MongoDB → JSONL**    | MongoDB native export to JSON. Hive read được nested arrays.                                                             |

---

## 2. CẤU TRÚC CÁC FILE LIÊN QUAN

### 2.1 MySQL to HDFS Ingestion

**Vị trí:** `src/ingest/mysql_to_hdfs.py`

**Cách hoạt động:**

```
MySQL Database (food_sentiment_db)
├─ restaurants table
├─ reviews table
└─ meals table
    ↓
mysql_to_hdfs.py ETL
├─ Step 1: Connect MySQL via mysql.connector
├─ Step 2: SELECT * FROM each table → fetch all rows
├─ Step 3: Convert each row to JSON (custom JSONEncoder for Decimal)
├─ Step 4: Write to local JSONL file (line by line)
│   └─ data/temp/mysql_restaurants.jsonl (format: {"id": ..., "name": ..., ...}\n)
└─ Step 5: HDFS upload
    ├─ hdfs dfs -mkdir -p /data/raw/mysql_restaurants/
    ├─ hdfs dfs -put -f mysql_restaurants.jsonl /data/raw/mysql_restaurants/
    └─ hdfs dfs -ls /data/raw/mysql_restaurants/ (verify)
```

**File bắt đầu:**

```python
MYSQL_CONFIG = {
    'user': 'root',
    'password': '',
    'host': '127.0.0.1',
    'port': 3306,
    'database': 'food_sentiment_db'
}

HDFS_RAW_DIR = "/data/raw"

class MySQLJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super().default(o)
```

**Input:** MySQL tables

**Output:** HDFS paths

- `hdfs:///data/raw/mysql_restaurants/mysql_restaurants.jsonl`
- `hdfs:///data/raw/mysql_reviews/mysql_reviews.jsonl`
- `hdfs:///data/raw/mysql_meals/mysql_meals.jsonl`

### 2.2 MongoDB to HDFS Ingestion

**Vị trí:** `src/ingest/mongo_to_hdfs.py`

**Cách hoạt động:**

```
MongoDB Database (sentiment_db)
├─ restaurants collection
└─ meals collection
    ↓
mongo_to_hdfs.py ETL
├─ Step 1: Connect MongoDB via pymongo
├─ Step 2: Find all documents in collection
├─ Step 3: Convert ObjectId → string
├─ Step 4: Convert _id → id (Hive compatibility)
├─ Step 5: Write to local JSONL file
│   └─ data/temp/restaurants.jsonl
└─ Step 6: HDFS upload
    ├─ hdfs dfs -mkdir -p /data/raw/restaurants/
    ├─ hdfs dfs -put -f restaurants.jsonl /data/raw/restaurants/
    └─ hdfs dfs -ls /data/raw/restaurants/ (verify)
```

**File bắt đầu:**

```python
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "sentiment_db"
HDFS_RAW_DIR = "/data/raw"

class MongoJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)  # ObjectId to string
        return super().default(o)
```

**Input:** MongoDB collections

**Output:** HDFS paths

- `hdfs:///data/raw/restaurants/restaurants.jsonl`
- `hdfs:///data/raw/meals/meals.jsonl`

### 2.3 Hive Schema Definition

**Vị trị:** `src/ingest/hive_schema.sql`

**Cách hoạt động:**

```
HDFS Raw Data Files
    ↓
hive_schema.sql
├─ CREATE DATABASE food_sentiment_db
├─ CREATE EXTERNAL TABLE mongodb_restaurants (
│   ├─ id STRING
│   ├─ name STRING
│   ├─ rating FLOAT
│   ├─ review_count INT
│   ├─ reviews ARRAY<STRUCT<user:STRING, rating:FLOAT, comment:STRING>>
│   └─ LOCATION '/data/raw/restaurants'
├─ CREATE EXTERNAL TABLE mongodb_meals (...)
└─ CREATE EXTERNAL TABLE mysql_restaurants (...)
    ↓
Hive Metastore
└─ Register schemas, enable SQL queries on HDFS data
```

**File bắt đầu:**

```sql
CREATE DATABASE IF NOT EXISTS food_sentiment_db;
USE food_sentiment_db;

DROP TABLE IF EXISTS mongodb_restaurants;
CREATE EXTERNAL TABLE IF NOT EXISTS mongodb_restaurants (
    id             STRING,
    name           STRING,
    rating         FLOAT,
    review_count   INT,
    address        STRING,
    district       STRING,
    city           STRING,
    reviews        ARRAY<STRUCT<`user`:STRING, rating:FLOAT, comment:STRING>>
)
ROW FORMAT SERDE 'org.apache.hive.hcatalog.data.JsonSerDe'
STORED AS TEXTFILE
LOCATION '/data/raw/restaurants';
```

**Input:** JSONL files on HDFS

**Output:** Hive external tables for SQL queries

### 2.4 Hive Analytics Views

**Vị trí:** `src/ingest/hive_analytics.sql`

**Cách hoạt động:**

```
Hive External Tables (mongodb_restaurants, mongodb_meals, mysql_restaurants)
    ↓
hive_analytics.sql
├─ view_rating_by_district: GROUP BY district, AVG(rating)
├─ view_cuisine_frequency: GROUP BY category, COUNT(*)
├─ view_rating_histogram: CASE WHEN rating BETWEEN buckets
├─ view_top_districts: Top 20 districts by count
├─ view_review_distribution: GROUP BY stars, COUNT(reviews)
└─ view_delivery_sentiment: Delivery vs Dine-in comparison
    ↓
Hive Views
└─ 6 views, mỗi view tương ứng 1 chart trên Streamlit
```

**File bắt đầu:**

```sql
-- View 1: Average Rating by District
DROP VIEW IF EXISTS view_rating_by_district;
CREATE VIEW view_rating_by_district AS
SELECT
    district_parsed AS district,
    ROUND(AVG(rating), 2) AS avg_rating,
    COUNT(*) AS total_count
FROM mysql_restaurants
WHERE district_parsed IS NOT NULL
GROUP BY district_parsed
ORDER BY avg_rating DESC;

-- View 2: Cuisine Frequency
DROP VIEW IF EXISTS view_cuisine_frequency;
CREATE VIEW view_cuisine_frequency AS
SELECT
    category,
    COUNT(*) AS cnt
FROM mongodb_meals
WHERE category IS NOT NULL
GROUP BY category
ORDER BY cnt DESC;
```

---

## 3. CÁC VẤN ĐỀ GẶP PHẢI & GIẢI PHÁP

### Vấn đề 1: MySQL-Java Incompatibility (Decimal Type)

**Triệu chứng:**

- Script crash với lỗi: `TypeError: Object of type Decimal is not JSON serializable`
- MySQL DECIMAL type không được JSON encoder nhận diện

**Nguyên nhân:**
MySQL driver trả về `Decimal` type cho NUMERIC/DECIMAL columns. Python's built-in `json.JSONEncoder` chỉ handle int/float/str, không handle Decimal.

**Giải pháp chi tiết:**
Trong [mysql_to_hdfs.py](src/ingest/mysql_to_hdfs.py) dòng 15-20:

```python
class MySQLJSONEncoder(json.JSONEncoder):
    """Custom encoder to handle MySQL Decimal, date, and time values."""
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)  # Decimal(4.50) → 4.50 (float)
        return super().default(o)

# Usage
json_line = json.dumps(row, cls=MySQLJSONEncoder, ensure_ascii=False)
```

**Kết quả:** Script hoàn thành export mà không error. Mỗi row viết thành 1 JSON line.

---

### Vấn đề 2: MongoDB ObjectId Serialization

**Triệu chứng:**

- MongoDB export fail với: `TypeError: Object of type ObjectId is not JSON serializable`
- `_id` field là ObjectId, không thể convert trực tiếp sang JSON

**Nguyên nhân:**
MongoDB dùng BSON ObjectId để unique identification. ObjectId là binary object, không phải string, nên JSON encoder không xử lý được.

**Giải pháp chi tiết:**
Trong [mongo_to_hdfs.py](src/ingest/mongo_to_hdfs.py) dòng 16-22:

```python
class MongoJSONEncoder(json.JSONEncoder):
    """Custom encoder to handle BSON ObjectIds."""
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)  # ObjectId(...) → "507f1f77bcf86cd799439011" (string)
        return super().default(o)

def export_collection_to_jsonl(db, collection_name, local_filepath):
    for doc in coll.find({}):
        if '_id' in doc:
            doc['id'] = str(doc.pop('_id'))  # Rename _id → id (Hive compatible)
        json_line = json.dumps(doc, cls=MongoJSONEncoder, ensure_ascii=False)
```

**Kết quả:** MongoDB documents export thành JSONL mà không error. `_id` renamed to `id` để Hive parse dễ.

---

### Vấn đề 3: HDFS Directory Already Exists Error

**Triệu chứng:**

- Script crash: `hdfs dfs -put: ERROR: Destination already exists`
- Re-run script bị fail vì HDFS directory đã tồn tại từ lần trước

**Nguyên nhân:**
`hdfs dfs -put` fail nếu destination directory chứa files. Cần `-f` flag để force overwrite, hoặc delete directory trước.

**Giải pháp chi tiết:**
Trong [mysql_to_hdfs.py](src/ingest/mysql_to_hdfs.py) + [mongo_to_hdfs.py](src/ingest/mongo_to_hdfs.py) dòng 50-65:

```python
def upload_to_hdfs(local_filepath, hdfs_subdir, hdfs_filename):
    target_dir = f"{HDFS_RAW_DIR}/{hdfs_subdir}"
    hdfs_target_path = f"{target_dir}/{hdfs_filename}"

    # 1. Create HDFS directory if not exists
    mkdir_cmd = ["hdfs", "dfs", "-mkdir", "-p", target_dir]
    subprocess.run(mkdir_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # 2. Put file with force flag
    put_cmd = ["hdfs", "dfs", "-put", "-f", local_filepath, hdfs_target_path]
    subprocess.run(put_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # 3. Verify upload success
    ls_cmd = ["hdfs", "dfs", "-ls", hdfs_target_path]
    res = subprocess.run(ls_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    print(f"  -> HDFS Stat: {res.stdout.strip()}")
```

**Key flags:**

- `-p`: Create parent directories if not exist
- `-f`: Force overwrite if destination exists

**Kết quả:** Script idempotent - có thể re-run bao nhiêu lần mà không error.

---

### Vấn đề 4: Hive Table Location Path Not Found

**Triệu chứng:**

- Hive query fail: `FAILED: Execution Error, return code 1 from org.apache.hadoop.hive.ql.exec.DDLTask`
- `LOCATION '/data/raw/restaurants'` không tìm thấy trên HDFS

**Nguyên nhân:**
HDFS directory structure không match với Hive external table definition. Data file lưu ở `/data/raw/restaurants/restaurants.jsonl` nhưng Hive expect tìm file trực tiếp trong directory.

**Giải pháp chi tiết:**
Trong [hive_schema.sql](src/ingest/hive_schema.sql) dòng 30-40:

```sql
CREATE EXTERNAL TABLE mongodb_restaurants (
    id STRING,
    name STRING,
    ...
)
ROW FORMAT SERDE 'org.apache.hive.hcatalog.data.JsonSerDe'
STORED AS TEXTFILE
LOCATION '/data/raw/restaurants';  -- Hive tìm *.jsonl files trong dir này
```

HDFS structure phải là:

```
/data/raw/
├─ restaurants/
│  └─ restaurants.jsonl  ← Hive sẽ scan thư mục này
├─ meals/
│  └─ meals.jsonl
└─ mysql_restaurants/
   └─ mysql_restaurants.jsonl
```

**Kết quả:** Hive query thành công, select dữ liệu từ HDFS files.

---

### Vấn đề 5: HiveServer2 Connection Timeout

**Triệu chứng:**

- Streamlit app timeout khi query Hive
- Error: `Connection refused: 10000`
- Hive queries chậm hoặc fail

**Nguyên nhân:**
HiveServer2 daemon chưa start, hoặc port 10000 blocked, hoặc Hive memory không đủ.

**Giải pháp chi tiết:**
Trong [run.sh](bin/run.sh) cần start HiveServer2:

```bash
# 1. Verify HDFS/YARN running
start-dfs.sh
start-yarn.sh

# 2. Start HiveServer2 daemon (dùng nohup để background)
nohup hiveserver2 -hiveconf hive.exec.mode.local.auto=true &

# 3. Wait for startup
sleep 10

# 4. Verify connection
hive -e "SELECT 1"
```

Trong [hive_connector.py](src/streamlit_app/hive_connector.py) dòng 125-135:

```python
def _query_via_pyhive(sql: str, database: str) -> pd.DataFrame:
    """Execute SQL through pyhive and return a DataFrame."""
    from pyhive import hive

    conn = hive.connect(
        host="localhost",
        port=10000,
        database=database
    )
    try:
        # Enable local mode để tránh MapReduce overhead trên YARN
        cursor = conn.cursor()
        cursor.execute("set hive.exec.mode.local.auto=true")
        df = pd.read_sql(sql, conn)
        return df
    finally:
        conn.close()
```

**Kết quả:** HiveServer2 accessible, Hive queries return kết quả trong vài giây.

---

### Vấn đề 6: Nested Array Parsing trong Hive

**Triệu chứng:**

- MongoDB `reviews` array không parse được trong Hive
- Query `SELECT reviews FROM mongodb_restaurants` fail hoặc return NULL

**Nguyên nhân:**
Hive need proper schema definition cho nested structures. Array of Struct cần ROW FORMAT SERDE chỉ định rõ.

**Giải pháp chi tiết:**
Trong [hive_schema.sql](src/ingest/hive_schema.sql) dòng 35-45:

```sql
CREATE EXTERNAL TABLE mongodb_restaurants (
    id             STRING,
    name           STRING,
    rating         FLOAT,
    reviews        ARRAY<STRUCT<`user`:STRING, rating:FLOAT, comment:STRING>>
    ↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑
    └─ Define nested struct schema explicitly
)
ROW FORMAT SERDE 'org.apache.hive.hcatalog.data.JsonSerDe'
STORED AS TEXTFILE
LOCATION '/data/raw/restaurants';
```

JSONL file example:

```json
{
  "id": "rest_123",
  "name": "Pho King",
  "rating": 4.5,
  "reviews": [
    { "user": "John", "rating": 5.0, "comment": "Great!" },
    { "user": "Jane", "rating": 4.0, "comment": "Good" }
  ]
}
```

**Kết quả:** Hive explode/flatten nested arrays thành individual rows. MapReduce jobs có thể process reviews riêng lẻ.

---

## 4. WORKFLOW THỰC HIỆN & INPUT/OUTPUT

### Bước 1: MySQL to HDFS Sync

**File:** [mysql_to_hdfs.py](src/ingest/mysql_to_hdfs.py)

**Input:** MySQL `food_sentiment_db` tables

- restaurants
- reviews
- meals

**Lệnh chạy:**

```bash
python src/ingest/mysql_to_hdfs.py
```

**Output:**

```
HDFS:
├─ /data/raw/mysql_restaurants/mysql_restaurants.jsonl (1,334 rows)
├─ /data/raw/mysql_reviews/mysql_reviews.jsonl (~44,000 rows)
└─ /data/raw/mysql_meals/mysql_meals.jsonl (666 rows)

Local (temp):
├─ data/temp/mysql_restaurants.jsonl
├─ data/temp/mysql_reviews.jsonl
└─ data/temp/mysql_meals.jsonl (deleted after upload)
```

**Thời gian:** ~30 seconds

---

### Bước 2: MongoDB to HDFS Sync

**File:** [mongo_to_hdfs.py](src/ingest/mongo_to_hdfs.py)

**Input:** MongoDB `sentiment_db` collections

- restaurants
- meals

**Lệnh chạy:**

```bash
python src/ingest/mongo_to_hdfs.py
```

**Output:**

```
HDFS:
├─ /data/raw/restaurants/restaurants.jsonl (1,334 docs, with nested reviews)
└─ /data/raw/meals/meals.jsonl (666 docs, with ingredients array)

Local (temp):
├─ data/temp/restaurants.jsonl
└─ data/temp/meals.jsonl (deleted after upload)
```

**Thời gian:** ~20 seconds

---

### Bước 3: Hive Schema Registration

**File:** [hive_schema.sql](src/ingest/hive_schema.sql)

**Input:** HDFS raw data files

**Lệnh chạy:**

```bash
hive -f src/ingest/hive_schema.sql
```

**Output:**

```
Hive Metastore:
├─ DATABASE: food_sentiment_db
└─ TABLES:
   ├─ mongodb_restaurants (external, location: /data/raw/restaurants)
   ├─ mongodb_meals (external, location: /data/raw/meals)
   ├─ mysql_restaurants (external, location: /data/raw/mysql_restaurants)
   ├─ mysql_reviews (external, location: /data/raw/mysql_reviews)
   └─ mysql_meals (external, location: /data/raw/mysql_meals)
```

**Thời gian:** ~5 seconds

---

### Bước 4: Hive Views Creation

**File:** [hive_analytics.sql](src/ingest/hive_analytics.sql)

**Input:** Hive external tables

**Lệnh chạy:**

```bash
hive -f src/ingest/hive_analytics.sql
```

**Output:**

```
Hive Views:
├─ view_rating_by_district
├─ view_cuisine_frequency
├─ view_rating_histogram
├─ view_top_districts
├─ view_review_distribution
└─ view_delivery_sentiment

Each view = 1 SQL query, cached in Hive metastore
```

**Thời gian:** ~10 seconds

---

### Kiểm chứng Hive Data

```bash
# Test query
hive -e "USE food_sentiment_db; SELECT COUNT(*) FROM mongodb_restaurants;"

# Output: 1334

hive -e "USE food_sentiment_db; SELECT * FROM view_rating_by_district LIMIT 5;"

# Output:
# district    avg_rating  total_count
# Quận 1      4.35        312
# Quận 3      4.28        198
# ...
```

---

## 5. HƯỚNG DẪN CHẠY & DEBUGGING

### Full Sync Pipeline (Hadoop Infrastructure)

```bash
# 1. Verify Hadoop/Hive running
jps  # Should see NameNode, DataNode, ResourceManager, NodeManager

# 2. MySQL to HDFS
python src/ingest/mysql_to_hdfs.py

# 3. MongoDB to HDFS
python src/ingest/mongo_to_hdfs.py

# 4. Create Hive schema
hive -f src/ingest/hive_schema.sql

# 5. Create Hive views
hive -f src/ingest/hive_analytics.sql

# 6. Verify
hive -e "USE food_sentiment_db; SHOW TABLES;"
hive -e "USE food_sentiment_db; SHOW VIEWS;"
```

### Troubleshooting

```bash
# Check HDFS data
hdfs dfs -ls /data/raw/
hdfs dfs -cat /data/raw/restaurants/restaurants.jsonl | head -1 | python -m json.tool

# Check Hive table definition
hive -e "USE food_sentiment_db; DESCRIBE mongodb_restaurants;"

# Debug Hive query
hive -S -e "SELECT * FROM mongodb_restaurants LIMIT 1;"

# Check HiveServer2 status
jps | grep HiveServer
netstat -tln | grep 10000

# Check Hive log
tail -100 /tmp/hive.log
```

---

## 6. KIẾN TRÚC HDFS

```
HDFS (/data/raw/)
│
├─ restaurants/
│  └─ restaurants.jsonl
│     (1,334 restaurants with nested reviews)
│
├─ meals/
│  └─ meals.jsonl
│     (666 meals with ingredient arrays)
│
├─ mysql_restaurants/
│  └─ mysql_restaurants.jsonl
│     (1,334 restaurants, flattened)
│
├─ mysql_reviews/
│  └─ mysql_reviews.jsonl
│     (~44,000 reviews, separate table)
│
└─ mysql_meals/
   └─ mysql_meals.jsonl
      (666 meals, flattened)
```

**Replication factor:** 3 (default) = mỗi file replicate 3 DataNodes

---

## 7. HIVE QUERY EXAMPLES

```sql
-- Query 1: Restaurants by district
SELECT district, COUNT(*) as cnt, ROUND(AVG(rating), 2) as avg_rating
FROM mysql_restaurants
GROUP BY district
ORDER BY cnt DESC
LIMIT 10;

-- Query 2: Explode reviews (flatten nested array)
SELECT
    r.name,
    rev.user,
    rev.rating,
    rev.comment
FROM mongodb_restaurants r
LATERAL VIEW EXPLODE(r.reviews) exploded_reviews AS rev
WHERE r.rating > 4.0
LIMIT 100;

-- Query 3: Ingredient frequency
SELECT ingredient, COUNT(*) as cnt
FROM mongodb_meals
LATERAL VIEW EXPLODE(ingredients) exploded_ing AS ingredient
GROUP BY ingredient
ORDER BY cnt DESC
LIMIT 20;
```

---

## 8. KỲ VỌNG VỀ KỸ NĂNG CẦN CÓ

Để hoàn thành vai trò này, bạn cần:

1. **Hadoop Ecosystem**
   - HDFS directory structure & commands (`hdfs dfs -mkdir, -put, -ls`)
   - YARN job scheduling
   - NameNode/DataNode roles

2. **Data Format & Serialization**
   - JSON/JSONL format
   - Handling custom Python objects (Decimal, ObjectId)
   - Hive SerDe (Serialization/Deserialization)

3. **Apache Hive**
   - DDL: CREATE TABLE, CREATE VIEW
   - Complex types: ARRAY, STRUCT, MAP
   - External tables, SQL queries
   - HiveServer2 connection

4. **SQL**
   - GROUP BY, JOIN, LATERAL VIEW EXPLODE
   - Aggregate functions (COUNT, AVG, SUM)
   - Nested queries

5. **Debugging & Troubleshooting**
   - Log reading (Hive, Hadoop logs)
   - Network ports (9000, 10000, 8088)
   - File permissions on HDFS

---

## 9. KẾT LUẬN & ĐIỂM ĐÁNH GIÁ

**Kết quả dự kiến:**

- ✅ MySQL/MongoDB data synced to HDFS (~50,000 rows total)
- ✅ HDFS data accessible via Hive external tables
- ✅ 6 Hive analytics views created & ready for MapReduce
- ✅ Data integrity verified (checksum, replication)

**Điểm đạo được:** **1.00/1.00** (100%)

- Apache HDFS: 0.25
- Apache YARN: 0.25
- Apache Hive: 0.25
- Data sync pipeline: 0.25 (implicit)
