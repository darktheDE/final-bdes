# Hướng Dẫn Vận Hành Thủ Công Hệ Thống (Big Data Stack Manual Operational Guide)

Tài liệu này cung cấp toàn bộ các lệnh và hướng dẫn vận hành thủ công từng thành phần trong hệ thống (Hadoop, HDFS, YARN, Hive, MySQL, MongoDB, Streamlit) mà không sử dụng các file kịch bản tự động hóa (`.sh`) có sẵn trong repo. 

Hướng dẫn này rất phù hợp để chạy thử từng bước, kiểm tra dữ liệu và sử dụng làm nội dung minh họa cho **Báo cáo đồ án/bài tập lớn**.

---

## 1. Thiết Lập Môi Trường (Java 8 & Path Variables)

Trước khi chạy bất kỳ lệnh thủ công nào của Hadoop hoặc Hive, bạn bắt buộc phải nạp các biến môi trường vào session Terminal hiện tại.

```bash
# Thiết lập JAVA_HOME trỏ tới OpenJDK 8 (bắt buộc cho Hadoop 3.3.6 & Hive 3.1.3)
export JAVA_HOME="/usr/lib/jvm/java-1.8.0-openjdk-amd64"
export HADOOP_HOME="/usr/local/hadoop"
export HIVE_HOME="/usr/local/hive"

# Cập nhật đường dẫn PATH ưu tiên Java 8 và các thư mục bin của Big Data
export PATH="${JAVA_HOME}/bin:${HADOOP_HOME}/bin:${HADOOP_HOME}/sbin:${HIVE_HOME}/bin:${PATH}"

# Đăng ký thư viện Classpath cho MapReduce và Hive SerDe
export HADOOP_CLASSPATH="${HIVE_HOME}/lib/hive-hcatalog-core-3.1.3.jar:${HIVE_HOME}/lib/hive-exec-3.1.3.jar:${HADOOP_CLASSPATH}"
```

---

## 2. Quản Lý Các Dịch Vụ Nền Thủ Công (Start/Stop Services)

### 2.1. CSDL MySQL (Metadata Store)
* **Khởi động:** `sudo service mysql start`
* **Dừng:** `sudo service mysql stop`
* **Kiểm tra trạng thái:** `sudo service mysql status`

### 2.2. CSDL MongoDB (Staging Store)
* **Khởi động:** `sudo service mongod start`
* **Dừng:** `sudo service mongod stop`
* **Kiểm tra trạng thái:** `sudo service mongod status`

### 2.3. Hệ thống Hadoop HDFS (Storage Layer)
* **Format NameNode (Chỉ chạy lần đầu tiên):**
  ```bash
  hdfs namenode -format
  ```
* **Khởi động HDFS (NameNode, DataNode, Secondary NameNode):**
  ```bash
  start-dfs.sh
  ```
* **Dừng HDFS:**
  ```bash
  stop-dfs.sh
  ```
* **Kiểm tra giao diện Web NameNode:** Mở trình duyệt truy cập: `http://localhost:9870`

### 2.4. Hadoop YARN (Resource Management & Execution Layer)
* **Khởi động YARN (ResourceManager & NodeManager):**
  ```bash
  start-yarn.sh
  ```
* **Dừng YARN:**
  ```bash
  stop-yarn.sh
  ```
* **Kiểm tra giao diện Web ResourceManager:** Mở trình duyệt truy cập: `http://localhost:8088`

### 2.5. Apache Hive Services
* **Khởi động Hive Metastore (Kết nối MySQL để quản lý Metadata):**
  ```bash
  nohup hive --service metastore > /tmp/hive-metastore.log 2>&1 &
  ```
* **Khởi động HiveServer2 (Lắng nghe cổng JDBC 10000 phục vụ Streamlit/Thrift client):**
  ```bash
  nohup hive --service hiveserver2 > /tmp/hiveserver2.log 2>&1 &
  ```
* **Kiểm tra trạng thái các cổng dịch vụ Hive:**
  ```bash
  ss -tln | grep -E "9083|10000"
  ```
  *(Cổng `9083` là Hive Metastore, `10000` là HiveServer2)*

---

## 3. Quy Trình Chạy Pipeline Dữ Liệu Từng Bước (Manual Pipeline Run)

Dưới đây là các bước thủ công để nạp, đồng bộ dữ liệu, chạy MapReduce và cập nhật kho dữ liệu.

### Bước 3.1: Kích hoạt môi trường Python ảo
```bash
source venv/bin/activate
```

### Bước 3.2: Crawl dữ liệu thô (Offline Seeds)
Nếu không muốn crawl trực tiếp từ web, hãy nạp dữ liệu seed từ thư mục dự phòng:
```bash
# Nạp dữ liệu công thức món ăn của TheMealDB vào MongoDB
python src/crawler/fetch_mealdb.py --offline

# Nạp dữ liệu đánh giá nhà hàng từ TripAdvisor vào MongoDB
python src/ingest/import_tripadvisor.py
```

### Bước 3.3: Chuẩn hóa dữ liệu & Migrations
Tiến hành phân tích cú pháp dữ liệu thô từ MongoDB, chuẩn hóa cấu trúc địa chỉ/rating, và nạp sang MySQL:
```bash
python src/ingest/init_db.py
```

### Bước 3.4: Đồng bộ dữ liệu sạch lên hệ thống HDFS
```bash
# Xuất dữ liệu nhà hàng MongoDB thành JSONL và đẩy lên HDFS
python src/ingest/mongo_to_hdfs.py

# Xuất dữ liệu đánh giá/món ăn MySQL thành JSONL và đẩy lên HDFS
python src/ingest/mysql_to_hdfs.py
```

### Bước 3.5: Đăng ký Schemas và phân tích dữ liệu trên Hive Warehouse
Chạy trực tiếp các file SQL định nghĩa bảng và tạo các view tổng hợp:
```bash
# Định nghĩa cấu trúc bảng ánh xạ HDFS
hive -f src/ingest/hive_schema.sql

# Tạo các View tổng hợp và phân tích
hive -f src/ingest/hive_analytics.sql
```

### Bước 3.6: Thực thi thủ công các Job MapReduce trên YARN
Mỗi job MapReduce được lập trình bằng thư viện `mrjob`. Để chạy thủ công một Job trên cụm Hadoop thật (YARN), sử dụng tham số `-r hadoop`:

```bash
# Ví dụ 1: Tính điểm rating trung bình theo quận huyện
python src/mapreduce/mr_rating_by_district.py -r hadoop \
  hdfs:///data/raw/restaurants/restaurants.jsonl \
  --output hdfs:///data/processed/rating_by_district

# Ví dụ 2: Lọc các từ khóa nguyên liệu món ăn trong đánh giá nhà hàng
python src/mapreduce/mr_ingredient_match.py -r hadoop \
  hdfs:///data/raw/restaurants/restaurants.jsonl \
  --output hdfs:///data/processed/ingredient_match
```
*(Bạn có thể làm tương tự với 6 job MapReduce còn lại trong thư mục `src/mapreduce/`)*

### Bước 3.7: Khởi động giao diện hiển thị báo cáo (Streamlit)
```bash
streamlit run src/streamlit_app/app.py
```

---

## 4. Truy Vấn & Kiểm Tra Dữ Liệu Thủ Công (Data Verification)

### 4.1. Truy vấn MySQL (Dữ liệu quan hệ sạch)
Khởi động client tương tác của MySQL:
```bash
mysql -h 127.0.0.1 -u root -p
```
*(Ấn Enter nếu không cấu hình mật khẩu)*

Các câu lệnh SQL mẫu để báo cáo:
```sql
-- Kiểm tra các database hiện có
SHOW DATABASES;
USE food_sentiment_db;

-- Đếm số lượng nhà hàng và xem thông tin cơ bản
SELECT COUNT(*) FROM restaurants;
SELECT name, rating, district_parsed, city FROM restaurants LIMIT 5;

-- Thống kê số lượng đánh giá theo từng mức điểm rating của người dùng
SELECT rating, COUNT(*) as count FROM reviews GROUP BY rating ORDER BY rating DESC;
```

### 4.2. Truy vấn MongoDB (Dữ liệu thô JSON)
Khởi động client tương tác của MongoDB (`mongosh` hoặc `mongo` tùy phiên bản cài đặt):
```bash
mongosh
```
Các lệnh truy vấn mẫu:
```javascript
// Xem danh sách DB và sử dụng database dự án
show dbs
use sentiment_db

// Kiểm tra danh sách collections
show collections

// Xem một bản ghi dữ liệu thô của nhà hàng
db.restaurants.findOne()

// Đếm tổng số lượng món ăn đã lưu
db.meals.countDocuments()
```

### 4.3. Quản trị hệ thống file HDFS (Hadoop Shell Commands)
Sử dụng công cụ `hdfs dfs` để tương tác trực tiếp với bộ lưu trữ HDFS:
```bash
# 1. Liệt kê cấu trúc thư mục dữ liệu thô và đã xử lý
hdfs dfs -ls -R /data

# 2. Xem nội dung dữ liệu JSONL của nhà hàng trên HDFS (lấy 5 dòng đầu)
hdfs dfs -cat /data/raw/restaurants/restaurants.jsonl | head -n 5

# 3. Kiểm tra dung lượng lưu trữ đang sử dụng trên HDFS
hdfs dfs -du -h /data

# 4. Sao chép thủ công một file từ local lên HDFS
hdfs dfs -put local_file.txt /data/raw/
```

### 4.4. Truy vấn Apache Hive (Data Warehouse & OLAP)
Khởi động giao diện dòng lệnh interactive của Hive:
```bash
hive
```
Các câu lệnh truy vấn HiveQL để trích xuất báo cáo:
```sql
SHOW DATABASES;
USE food_sentiment_db;
SHOW TABLES;

-- Xem cấu trúc bảng của View phân tích điểm rating theo quận huyện
DESCRIBE FORMATTED view_rating_by_district;

-- Thực hiện truy vấn phân tích trực tiếp trên Hive Server
SELECT district, avg_rating, total_count 
FROM view_rating_by_district 
ORDER BY avg_rating DESC 
LIMIT 10;
```

---

## 5. Sao Lưu & Phục Hồi Dữ Liệu Thủ Công (Backup & Restore)

Để minh chứng cho khả năng chịu lỗi và an toàn dữ liệu trong báo cáo, bạn có thể thực hiện sao lưu thủ công bằng các lệnh nguyên bản sau:

### 5.1. Sao lưu CSDL (Backup)
Tạo một thư mục chứa backup ở local, ví dụ `/home/$USER/db_backup/`:
```bash
mkdir -p ~/db_backup
```

* **Sao lưu MySQL (food_sentiment_db):**
  ```bash
  mysqldump -h 127.0.0.1 -u root food_sentiment_db > ~/db_backup/mysql_backup.sql
  ```
* **Sao lưu MongoDB (sentiment_db):**
  ```bash
  mongodump --host localhost --port 27017 --db sentiment_db --out ~/db_backup/mongo_backup
  ```

### 5.2. Phục hồi dữ liệu (Restore)
Trước khi restore, bạn có thể xóa sạch CSDL hiện có để thử nghiệm:
* **Khôi phục MySQL:**
  ```bash
  # Khởi tạo lại db rỗng
  mysql -h 127.0.0.1 -u root -e "DROP DATABASE IF EXISTS food_sentiment_db; CREATE DATABASE food_sentiment_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
  # Thực thi khôi phục
  mysql -h 127.0.0.1 -u root food_sentiment_db < ~/db_backup/mysql_backup.sql
  ```
* **Khôi phục MongoDB:**
  ```bash
  mongorestore --host localhost --port 27017 --db sentiment_db --drop ~/db_backup/mongo_backup/sentiment_db
  ```

---

## 6. Chẩn Đoán & Xử Lý Sự Cố Cơ Bản (Troubleshooting)

### 6.1. HDFS NameNode bị rơi vào trạng thái Safe Mode (Chỉ đọc)
* **Triệu chứng:** Khi đẩy file lên HDFS báo lỗi `NameNode is in safe mode`.
* **Cách xử lý thủ công:** Buộc NameNode thoát khỏi Safe Mode bằng lệnh:
  ```bash
  hdfs dfsadmin -safemode leave
  ```

### 6.2. Lỗi phân quyền mạo danh (Impersonation / Proxyuser)
* **Triệu chứng:** PyHive kết nối lỗi báo `User: <username> is not allowed to impersonate <username>`.
* **Cách xử lý:** Đảm bảo file cấu hình `$HADOOP_HOME/etc/hadoop/core-site.xml` của bạn chứa đúng tên người dùng hiện tại của hệ thống thay thế cho `USER_PLACEHOLDER` ở các khoá:
  ```xml
  <property>
      <name>hadoop.proxyuser.<USER_NAME>.hosts</name>
      <value>*</value>
  </property>
  <property>
      <name>hadoop.proxyuser.<USER_NAME>.groups</name>
      <value>*</value>
  </property>
  ```

### 6.3. Hive CLI bị treo hoặc crash do xung đột phiên bản thư viện Guava
* **Triệu chứng:** Chạy lệnh `hive` lỗi ngay lập tức về `Preconditions.checkArgument`.
* **Cách xử lý:** Xóa file Guava cũ trong Hive và copy file Guava mới từ Hadoop sang:
  ```bash
  rm -f /usr/local/hive/lib/guava-19.0.jar
  cp /usr/local/hadoop/share/hadoop/common/lib/guava-27.0-jre.jar /usr/local/hive/lib/
  ```

### 6.4. Kiểm tra Logs khi các dịch vụ Hive không khởi động được
Khi chạy ngầm các dịch vụ Hive, bạn hãy xem log trực tiếp để tìm lỗi:
* **Log của Hive Metastore:** `cat /tmp/hive-metastore.log | tail -n 100`
* **Log của HiveServer2:** `cat /tmp/hiveserver2.log | tail -n 100`
