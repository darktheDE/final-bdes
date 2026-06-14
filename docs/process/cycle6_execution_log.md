# Nhật ký thực thi (Execution Log) - Cycle 6: Interactive GUI (Streamlit Web Dashboard)

**Ngày thực hiện:** 14/06/2026  
**Thực hiện bởi:** AI Agent (Antigravity)

---

## 1. Mục tiêu Cycle 6

Xây dựng giao diện web dashboard tương tác sử dụng **Streamlit 1.35+** chạy trên WSL2 Ubuntu, kết nối trực tiếp đến MySQL/Hive và cho phép kích hoạt HDFS/MapReduce từ giao diện người dùng.

---

## 2. Các hạng mục đã triển khai

### Task 6.1 — Streamlit Base Layout
- Tạo file `src/streamlit_app/app.py` từ đầu.
- Cấu hình `st.set_page_config()` với page title, icon, layout wide.
- Thiết lập **dark mode** CSS tùy chỉnh (màu nền `#1e1e1e`, accent màu `#fca311`).
- Sidebar navigation dùng `st.sidebar.radio()` với 3 trang: *Data Management (CRUD)*, *Big Data Reports*, *DevOps & Jobs Execution*.

### Task 6.2 — MySQL CRUD Interface
- Kết nối MySQL thông qua `mysql.connector` (pure-Python TCP mode).
- Triển khai 4 tab: View, Insert, Update, Delete.
  - **View**: Search theo name/district, hiển thị `st.dataframe`.
  - **Insert**: Form nhập đầy đủ các trường schema (`id`, `name`, `rating`, `address`...).
  - **Update**: Cập nhật rating theo `id`.
  - **Delete**: Xóa bản ghi theo `id`.

### Task 6.3 — Visualization Page (6 Charts)
- Sử dụng `plotly.express` để vẽ 6 biểu đồ tương tác:
  - **Biểu đồ 1** (Bar): Đánh giá trung bình theo quận.
  - **Biểu đồ 2** (Bar): Điểm sentiment theo phân khúc giá.
  - **Biểu đồ 3** (Pie/Donut): Phân bổ ẩm thực theo loại (Cuisine).
  - **Biểu đồ 4** (Pie): Phân khúc giá (Budget/Moderate/Luxury).
  - **Biểu đồ 5** (Line): Đường phân phối số sao đánh giá (Review Distribution Curve).
  - **Biểu đồ 6** (Scatter): So sánh sentiment Delivery vs Dine-in.
- Thêm hàm `run_hive_query()` dùng `subprocess` để chạy HiveQL và parse TSV output thành DataFrame.

### Task 6.4 — DevOps Operations Triggers
- Nút **"Run Backup Script"**: Gọi `subprocess.check_output(['bash', 'src/backup/db_backup.sh'])`.
- Dropdown chọn MapReduce job + nút **"Execute Job"**: Gọi job với tham số `-r hadoop` trỏ đến HDFS path.
- Hiển thị stdout/stderr log trong `st.code()`.

---

## 3. Các tệp tin được tạo mới và cập nhật

| File | Trạng thái | Ghi chú |
|:-----|:-----------|:--------|
| [`src/streamlit_app/app.py`](file:///d:/Project/final-bdes/src/streamlit_app/app.py) | **Tạo mới** | File chính toàn bộ Streamlit dashboard |
| [`docs/MASTERPLAN.md`](file:///d:/Project/final-bdes/docs/MASTERPLAN.md) | **Cập nhật** | Đánh dấu `[x]` tất cả task Cycle 6 hoàn thành |

---

## 4. Quy trình triển khai dịch vụ

### Bước 4.1: Khởi động tất cả dịch vụ backend (WSL2)
Do môi trường WSL2 không chạy `systemd` theo mặc định, các dịch vụ phải được khởi động thủ công:

```bash
# Khởi động MySQL và MongoDB (cần quyền root WSL)
wsl -d Ubuntu -u root service mysql start
wsl -d Ubuntu -u root service mongod start

# Khởi động Hadoop DFS và YARN
wsl -d Ubuntu bash -c "export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64; /usr/local/hadoop/sbin/start-dfs.sh; /usr/local/hadoop/sbin/start-yarn.sh"
```

**Kết quả:** NameNode, DataNode, SecondaryNameNode, ResourceManager, NodeManager đều khởi động thành công.

### Bước 4.2: Đồng bộ dữ liệu từ MongoDB lên HDFS
```bash
wsl -d Ubuntu bash -c "export PATH=/usr/local/hadoop/bin:/usr/local/hadoop/sbin:$PATH; source venv/bin/activate; python src/ingest/mongo_to_hdfs.py"
```

**Kết quả:**
```
[*] Exporting collection 'restaurants' from MongoDB...
  -> Exported 1334 records to data/temp/restaurants.jsonl
  -> Successfully uploaded restaurants.jsonl to HDFS.
  -> HDFS Stat: -rw-r--r-- 1 kien_hung supergroup 17178955 2026-06-14 09:48 /data/raw/restaurants/restaurants.jsonl
[*] Exporting collection 'meals' from MongoDB...
  -> Exported 666 records to data/temp/meals.jsonl
  -> Successfully uploaded meals.jsonl to HDFS.
  -> HDFS Stat: -rw-r--r-- 1 kien_hung supergroup 858583 2026-06-14 09:48 /data/raw/meals/meals.jsonl
[+] MongoDB to HDFS Ingestion completed successfully.
```

---

## 5. Nhật ký xử lý sự cố trong Cycle 6

### Sự cố 6.1: MySQL Access Denied — `auth_socket` Plugin

**Triệu chứng:**
```
Failed to connect to MySQL: 1045 (28000): Access denied for user 'root'@'localhost' (using password: YES)
```

**Nguyên nhân gốc (Root Cause):**
Trên Ubuntu 24.04, MySQL mặc định cấu hình `root@localhost` dùng plugin xác thực `auth_socket`. Plugin này bỏ qua mật khẩu và chỉ cho phép truy cập nếu Linux user hiện tại là `root`. Khi Python/Streamlit gửi kết nối có mật khẩu `"root"`, MySQL từ chối vì plugin không nhận mật khẩu.

**Giải pháp:**
```sql
-- Truy cập bằng: wsl -d Ubuntu -u root mysql
ALTER USER 'root'@'localhost' IDENTIFIED WITH caching_sha2_password BY 'root';
ALTER USER 'root'@'127.0.0.1' IDENTIFIED BY 'root';
ALTER USER 'root'@'%' IDENTIFIED BY 'root';
FLUSH PRIVILEGES;
```

---

### Sự cố 6.2: MySQL bind-address Chặn Kết Nối TCP

**Triệu chứng:**
Sau khi fix plugin auth, kết nối TCP từ Streamlit (chạy trong WSL) vẫn bị từ chối.

**Nguyên nhân gốc:**
`/etc/mysql/mysql.conf.d/mysqld.cnf` có cấu hình:
```ini
bind-address = 127.0.0.1
```
Tuy nhiên `root@127.0.0.1` có `authentication_string` **rỗng** (mật khẩu trống) do lệnh `CREATE USER IF NOT EXISTS` trước đó tạo user mà không set password. Khi Python gửi password `root`, MySQL từ chối vì mật khẩu không khớp (trống vs "root").

**Giải pháp 1:** Đổi bind-address để MySQL lắng nghe mọi interface:
```bash
sudo sed -i 's/^bind-address.*= 127.0.0.1/bind-address\t\t= 0.0.0.0/' /etc/mysql/mysql.conf.d/mysqld.cnf
sudo service mysql restart
```

**Giải pháp 2:** Set lại mật khẩu đúng cho tất cả entries root:
```sql
ALTER USER 'root'@'localhost' IDENTIFIED BY 'root';
ALTER USER 'root'@'127.0.0.1' IDENTIFIED BY 'root';
ALTER USER 'root'@'%' IDENTIFIED BY 'root';
FLUSH PRIVILEGES;
```

---

### Sự cố 6.3: `mysql-connector-python` Dùng Unix Socket Thay Vì TCP

**Triệu chứng:**
Kể cả khi set `host='127.0.0.1'`, connector vẫn báo lỗi `'root'@'localhost'` (không phải `'root'@'127.0.0.1'`), chứng tỏ đang dùng Unix socket thay TCP.

**Nguyên nhân:**
`mysql-connector-python` có thể fallback về Unix socket (`/var/run/mysqld/mysqld.sock`) khi host là `127.0.0.1` trong một số cấu hình.

**Giải pháp:**
```python
mysql.connector.connect(
    host="127.0.0.1",
    port=3306,
    user="root",
    password="root",
    database="food_sentiment_db",
    use_pure=True   # <-- Buộc dùng pure-Python TCP driver
)
```

---

### Sự cố 6.4: MapReduce IOError — Không Tìm Thấy File Input

**Triệu chứng** (giao diện DevOps tab):
```
IOError: Cannot read data/raw/restaurants.jsonl
```

**Nguyên nhân:**
MapReduce job được gọi với đường dẫn local `data/raw/restaurants.jsonl` trong khi job cần đọc từ HDFS, và file này cũng chưa tồn tại ở local.

**Giải pháp:**
1. Đồng bộ dữ liệu lên HDFS trước (chạy `mongo_to_hdfs.py`).
2. Cập nhật lệnh gọi trong Streamlit để dùng tham số `-r hadoop` và HDFS URI:
```python
cmd = ['python', f'src/mapreduce/{job_choice}', '-r', 'hadoop',
       'hdfs://localhost:9000/data/raw/restaurants/restaurants.jsonl']
```

---

### Sự cố 6.5: Hadoop NameNode Không Khởi Động (Connection Refused Port 9000)

**Triệu chứng:**
```
Call From KienHung/127.0.1.1 to localhost:9000 failed on connection exception: java.net.ConnectException: Connection refused
```

**Nguyên nhân:**
Sau khi reformat HDFS (chạy `hdfs namenode -format`), NameNode cần restart. Tuy nhiên lệnh `stop-all.sh` có thêm warning 10 giây dừng, làm quá trình bị gián đoạn.

**Giải pháp:**
```bash
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
/usr/local/hadoop/sbin/stop-all.sh   # Đợi đủ 10 giây
/usr/local/hadoop/sbin/start-dfs.sh
/usr/local/hadoop/sbin/start-yarn.sh
```

**Kết quả xác nhận (`jps`):**
```
NameNode
DataNode
SecondaryNameNode
ResourceManager
NodeManager
```

---

## 6. Kết quả nghiệm thu (Definition of Done)

| Task | Tiêu chí | Kết quả |
|:-----|:---------|:--------|
| 6.1 Base Layout | App chạy port 8501, có sidebar navigation | ✅ Đạt |
| 6.2 MySQL CRUD | C/R/U/D hoạt động với phản hồi tức thì | ✅ Đạt (sau fix auth) |
| 6.3 Visualization | 6 biểu đồ Plotly hiển thị đủ 3 loại | ✅ Đạt |
| 6.4 DevOps Triggers | Backup script và MapReduce job trigger được từ UI | ✅ Đạt |
| 6.5 Hive OLAP Integration | Big Data Reports kết nối live Hive, fallback offline mode | ✅ Đạt |

---

## 7. Lệnh chạy ứng dụng

```bash
# 1. Kích hoạt virtual environment
source venv/bin/activate

# 2. Khởi động app
streamlit run src/streamlit_app/app.py
```

Mở trình duyệt: `http://localhost:8501`

---

## 8. Task 6.5 — Apache Hive OLAP Integration (Bổ sung 14/06/2026)

### 8.1 Phạm vi triển khai

Trang *Big Data Reports* trong Streamlit đã dùng mock data tĩnh từ đầu. Task 6.5 thay thế toàn bộ bằng live OLAP queries từ Apache Hive, có graceful fallback 3 lớp.

### 8.2 Các file mới tạo

| File | Mô tả |
|:-----|:------|
| [`src/ingest/hive_analytics.sql`](file:///d:/Project/final-bdes/src/ingest/hive_analytics.sql) | 6 `CREATE VIEW` HiveQL tương ứng 6 biểu đồ Plotly |
| [`src/streamlit_app/hive_connector.py`](file:///d:/Project/final-bdes/src/streamlit_app/hive_connector.py) | Module kết nối Hive 3 lớp: pyhive → subprocess CLI → offline mock |

### 8.3 Các file cập nhật

| File | Thay đổi |
|:-----|:---------|
| [`src/streamlit_app/app.py`](file:///d:/Project/final-bdes/src/streamlit_app/app.py) | `render_reports_page()`: mock → live Hive queries + status badge |
| [`requirements.txt`](file:///d:/Project/final-bdes/requirements.txt) | Thêm `pyhive[hive]`, `thrift`, `thrift-sasl` |
| [`docs/MASTERPLAN.md`](file:///d:/Project/final-bdes/docs/MASTERPLAN.md) | Bổ sung và đánh dấu `[x]` Task 6.5 |

### 8.4 Quy trình chạy Hive views (WSL2)

```bash
# Bước 1: Tạo database và external tables (chỉ cần chạy 1 lần)
hive -f src/ingest/hive_schema.sql

# Bước 2: Tạo 6 OLAP views (chỉ cần chạy 1 lần)
hive -f src/ingest/hive_analytics.sql

# Bước 3 (tuỳ chọn): Khởi động HiveServer2 để Streamlit dùng pyhive mode
hive --service hiveserver2 &
```

### 8.5 Nhật ký xử lý sự cố

#### Sự cố 6.6: Hive ClassCastException với Java 11

**Triệu chứng:**
```
Exception in thread "main" java.lang.ClassCastException:
  class jdk.internal.loader.ClassLoaders$AppClassLoader cannot be cast to
  class java.net.URLClassLoader
    at org.apache.hadoop.hive.ql.session.SessionState.<init>(SessionState.java:413)
```

**Nguyên nhân:**
Hive 3.1.3 hardcode cast `AppClassLoader` sang `URLClassLoader` tại `SessionState.java:413`. Từ Java 9+, `AppClassLoader` không còn extend `URLClassLoader` nên ClassCastException xảy ra.

**Giải pháp — Fix vĩnh viễn qua `hive-env.sh`:**
```bash
cp /usr/local/hive/conf/hive-env.sh.template /usr/local/hive/conf/hive-env.sh
echo 'export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64' >> /usr/local/hive/conf/hive-env.sh
```

Sau khi tạo file này, Hive tự động dùng Java 8 mà không cần prefix `JAVA_HOME=...` mỗi lần.

#### Sự cố 6.7: `SemanticException: Database does not exist: food_sentiment_db`

**Triệu chứng:**
```
FAILED: SemanticException [Error 10072]: Database does not exist: food_sentiment_db
```

**Nguyên nhân:**
`hive_analytics.sql` mở đầu bằng `USE food_sentiment_db;` nhưng database này chưa được khởi tạo trong Hive metastore.

**Giải pháp:**
Chạy `hive_schema.sql` trước (tạo database + external tables), sau đó mới chạy `hive_analytics.sql`:
```bash
hive -f src/ingest/hive_schema.sql  # Tạo DB + external tables trước
hive -f src/ingest/hive_analytics.sql  # Sau đó tạo 6 views
```

### 8.6 Kết quả xác nhận — SHOW VIEWS

```
SHOW VIEWS trong food_sentiment_db:
  view_cuisine_frequency       ✅
  view_delivery_sentiment      ✅
  view_price_segment           ✅
  view_rating_by_district      ✅
  view_review_distribution     ✅
  view_sentiment_by_price      ✅
```

**Lệnh xác nhận đã chạy:**
```bash
hive -S -e 'USE food_sentiment_db; SHOW VIEWS;' 2>/dev/null
```

**Output thực tế:**
```
tab_name
view_cuisine_frequency
view_delivery_sentiment
view_price_segment
view_rating_by_district
view_review_distribution
view_sentiment_by_price
```

---

### 8.7 Kết quả Streamlit UI sau triển khai

Sau khi reload app, trang Big Data Reports hiển thị:

- ✅ **Status badge "🟡 Hive CLI Mode"** — App tự phát hiện HiveServer2 chưa chạy và chuyển sang subprocess fallback (`hive -S -e`)
- ✅ **Nút "🔄 Re-probe"** — Cho phép force re-detect kết nối Hive
- ✅ **Spinner "⏳ Loading analytics data from Hive..."** — Hiển thị khi đang fetch dữ liệu lần đầu
- ✅ **Nút "🔄 Refresh Data"** — Xóa cache `session_state`, fetch lại từ Hive
- ✅ **6 biểu đồ Plotly** — Render từ kết quả Hive thật (HDFS data)

---

### 8.8 Tối ưu hoá: Batch Query + Session State Caching

#### Vấn đề phát hiện

Thiết kế ban đầu gọi `query_hive(sql)` riêng lẻ cho từng biểu đồ (6 lần). Mỗi lần gọi subprocess Hive:
- Spawn một JVM mới (~5–10 giây khởi động)
- Kết nối MySQL metastore
- Biên dịch HiveQL plan
- Thực thi MapReduce job trên HDFS

→ **Tổng thời gian chờ: 6 × JVM overhead** = có thể lên đến 10–15 phút.

Ngoài ra Streamlit re-render toàn bộ page mỗi khi user tương tác bất kỳ widget nào → trigger 6 queries lại từ đầu.

#### Giải pháp triển khai

**1. `batch_query_all_views()` trong `hive_connector.py`**

Thay vì 6 subprocess riêng lẻ, build một script HiveQL duy nhất chứa tất cả 6 SELECT, dùng sentinel `!echo ---BATCH_SEP---` để tách output:

```python
# Trong hive_connector.py
_BATCH_SEP = "---BATCH_SEP---"

BATCH_QUERIES = [
    ("view_rating_by_district",   "SELECT district, avg_rating, total_count FROM view_rating_by_district LIMIT 20"),
    ("view_cuisine_frequency",    "SELECT category, cnt FROM view_cuisine_frequency LIMIT 15"),
    ("view_price_segment",        "SELECT price_range, cnt FROM view_price_segment"),
    ("view_sentiment_by_price",   "SELECT price_range, avg_sentiment, review_count FROM view_sentiment_by_price"),
    ("view_review_distribution",  "SELECT stars, cnt FROM view_review_distribution"),
    ("view_delivery_sentiment",   "SELECT service_type, avg_rating, review_count FROM view_delivery_sentiment"),
]

# Một subprocess duy nhất thay vì 6
proc = subprocess.run(["hive", "-S", "-e", full_sql], ...)
blocks = raw.split(_BATCH_SEP)  # Tách output thành 6 DataFrame
```

**Kết quả:** 6×JVM overhead → **1×JVM overhead**. Tiết kiệm ~80% thời gian.

**2. `st.session_state` caching trong `app.py`**

```python
cache_key = f"hive_data_{hive_mode}"

if force_refresh or cache_key not in st.session_state:
    with st.spinner("⏳ Loading analytics data from Hive..."):
        data = batch_query_all_views()   # 1 lần duy nhất
    st.session_state[cache_key] = data
else:
    data = st.session_state[cache_key]  # Instant từ cache
```

**Kết quả:** Lần đầu vào trang: chờ 1–3 phút. Mọi lần sau + mọi interaction: **instant** (không re-query).

#### Thứ tự fallback hoàn chỉnh

```
User vào trang Big Data Reports
         │
         ▼
  get_hive_status() → probe pyhive TCP port 10000
         │
    ┌────┴────┐
  live?      fail
    │          │
  pyhive    probe hive CLI binary
  queries      │
           ┌───┴────┐
         OK?       fail
           │         │
      subprocess   OFFLINE
      batch query  mock data
           │
      parse TSV output
      split by sentinel
           │
      6 DataFrames → session_state cache
           │
      6 Plotly charts render
```

#### Danh sách file cuối cùng liên quan Task 6.5

| File | Thay đổi chính |
|:-----|:---------------|
| [`src/ingest/hive_schema.sql`](file:///d:/Project/final-bdes/src/ingest/hive_schema.sql) | Không đổi — 5 external tables đã có |
| [`src/ingest/hive_analytics.sql`](file:///d:/Project/final-bdes/src/ingest/hive_analytics.sql) | **MỚI** — 6 CREATE VIEW HiveQL |
| [`src/streamlit_app/hive_connector.py`](file:///d:/Project/final-bdes/src/streamlit_app/hive_connector.py) | **MỚI** — module 3-lớp fallback + `batch_query_all_views()` + `HIVE_QUERY_TIMEOUT=180` |
| [`src/streamlit_app/app.py`](file:///d:/Project/final-bdes/src/streamlit_app/app.py) | Cập nhật — `render_reports_page()` dùng batch + session_state cache |
| [`requirements.txt`](file:///d:/Project/final-bdes/requirements.txt) | Cập nhật — thêm `pyhive[hive]`, `thrift`, `thrift-sasl` |
| `/usr/local/hive/conf/hive-env.sh` | **MỚI** (hệ thống) — `JAVA_HOME=java-8-openjdk-amd64` |

---

### 8.9 Hướng dẫn vận hành (Quick Reference)

#### Khởi động đầy đủ từ đầu (fresh boot WSL2)

```bash
# 1. Khởi động dịch vụ
sudo service mysql start
sudo service mongod start
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
/usr/local/hadoop/sbin/start-dfs.sh
/usr/local/hadoop/sbin/start-yarn.sh

# 2. (Lần đầu) Init Hive schema
hive -f src/ingest/hive_schema.sql
hive -f src/ingest/hive_analytics.sql

# 3. (Tuỳ chọn) Khởi động HiveServer2 để dùng pyhive mode
hive --service hiveserver2 > /tmp/hiveserver2.log 2>&1 &
sleep 20  # Đợi daemon sẵn sàng

# 4. Chạy Streamlit
source venv/bin/activate
streamlit run src/streamlit_app/app.py
```

#### Kiểm tra trạng thái Hive

```bash
# Xem views hiện có
hive -S -e 'USE food_sentiment_db; SHOW VIEWS;' 2>/dev/null

# Test query mẫu
hive -S -e 'USE food_sentiment_db; SELECT district, avg_rating FROM view_rating_by_district LIMIT 5;' 2>/dev/null

# Kiểm tra HiveServer2 port (nếu đang chạy)
ss -tln | grep 10000
```

#### Recreate views (nếu metastore bị reset)

```bash
hive -f src/ingest/hive_schema.sql    # Tạo lại DB + external tables
hive -f src/ingest/hive_analytics.sql # Tạo lại 6 OLAP views
```

---

### 8.10 Tổng kết Cycle 6 (đầy đủ)

| Task | Mô tả | Kết quả |
|:-----|:------|:--------|
| 6.1 Base Layout | Streamlit app với dark mode, sidebar nav | ✅ Đạt |
| 6.2 MySQL CRUD | 4-tab CRUD interface cho bảng `restaurants` | ✅ Đạt |
| 6.3 Visualization | 6 biểu đồ Plotly (3 loại: bar/pie/line+scatter) | ✅ Đạt |
| 6.4 DevOps Triggers | Backup script + MapReduce trigger từ UI | ✅ Đạt |
| 6.5 Hive OLAP | Live HDFS data qua Hive CLI, batch query, session cache | ✅ Đạt |

**Tổng số files đã tạo/cập nhật trong toàn bộ Cycle 6:** 7 files  
**Tổng số sự cố đã xử lý:** 7 (6.1–6.7)  
**Thời gian load Big Data Reports (lần đầu):** ~1–3 phút (Hive subprocess)  
**Thời gian load Big Data Reports (lần sau):** Instant (session_state cache)
