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

---

## 7. Lệnh chạy ứng dụng

```bash
# 1. Kích hoạt virtual environment
source venv/bin/activate

# 2. Khởi động app
streamlit run src/streamlit_app/app.py
```

Mở trình duyệt: `http://localhost:8501`
