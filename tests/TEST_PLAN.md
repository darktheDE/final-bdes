# Kế Hoạch Kiểm Thử Toàn Hệ Thống (Master Manual & Automated Test Plan)

Tài liệu này cung cấp kế hoạch kiểm thử chi tiết và các lệnh chạy để kiểm tra toàn bộ các module, cơ sở dữ liệu, dịch vụ Hadoop/Hive, MapReduce và giao diện Streamlit của hệ thống Phân tích Cảm xúc Đồ ăn & Nhà hàng trên môi trường **Ubuntu 24.04 WSL2 LTS**.

---

## 1. Tổng Quan Kế Hoạch Kiểm Thử

Hệ thống được kiểm thử theo chiến lược phân tầng từ dưới lên (Bottom-Up), chia làm 7 chu kỳ kiểm thử chính (Cycles 0 - 6) kèm theo bộ kiểm thử tự động tích hợp (Integration Test Suite) nhằm đảm bảo tính ổn định và chính xác của toàn bộ dữ liệu pipeline.

```text
+-------------------------------------------------------+
|                CYCLE 6: Streamlit GUI                 |
+-------------------------------------------------------+
                           ^
+-------------------------------------------------------+
|             CYCLE 5: Backup & Restore                 |
+-------------------------------------------------------+
                           ^
+-------------------------------------------------------+
|             CYCLE 4: Hadoop MapReduce                 |
+-------------------------------------------------------+
                           ^
+-------------------------------------------------------+
|          CYCLE 3: HDFS & Apache Hive DW               |
+-------------------------------------------------------+
                           ^
+-------------------------------------------------------+
|             CYCLE 2: Data Ingestion                   |
+-------------------------------------------------------+
                           ^
+-------------------------------------------------------+
|        CYCLE 1: Môi trường & Dependency               |
+-------------------------------------------------------+
                           ^
+-------------------------------------------------------+
|          CYCLE 0: Hạ tầng Dịch vụ Nền                 |
+-------------------------------------------------------+
```

---

## 2. Kiểm Thử Tự Động (Automated Integration Tests)

Để tự động hóa việc xác minh toàn bộ các thành phần, hệ thống cung cấp một script kiểm thử tự động toàn diện giúp kiểm tra nhanh trạng thái hạ tầng và tính nhất quán của dữ liệu.

### 2.1. Lệnh chạy bộ kiểm thử tự động:
Chạy lệnh sau từ thư mục gốc của dự án trên WSL2:
```bash
bash bin/run_tests.sh
```

### 2.2. Các thành phần được kiểm tra tự động:
1. **Kiểm tra Cổng Dịch Vụ (Service Ports)**:
   - MySQL (Cổng `3306`)
   - MongoDB (Cổng `27017`)
   - HDFS NameNode (Cổng `9000`)
   - HiveServer2 (Cổng `10000`)
   - Streamlit (Cổng `8501`)
2. **Kiểm tra Dữ liệu MySQL (MySQL DB Verification)**:
   - Kết nối thành công tới database `food_sentiment_db`.
   - Kiểm tra cấu trúc các bảng `restaurants`, `reviews`, và `meals`.
   - Đếm số lượng bản ghi thực tế (Đảm bảo > 0).
3. **Kiểm tra Dữ liệu MongoDB (MongoDB Verification)**:
   - Kết nối thành công tới database `sentiment_db`.
   - Kiểm tra số lượng documents trong các collection `restaurants` và `meals`.
4. **Kiểm tra Hadoop HDFS (HDFS Storage Verification)**:
   - Kiểm tra kết nối HDFS.
   - Xác minh sự tồn tại của các tệp dữ liệu thô: `/data/raw/restaurants/restaurants.jsonl` và `/data/raw/meals/meals.jsonl`.
5. **Kiểm tra Apache Hive Connection (Hive Connection)**:
   - Kết nối tới HiveServer2 qua cổng `10000`.
   - Thực thi truy vấn thử nghiệm để lấy dữ liệu từ các view phân tích đã tạo.
6. **Kiểm tra Luồng Chạy MapReduce cục bộ (MapReduce Local Smoke Test)**:
   - Thực thi thử nghiệm các file MapReduce bằng dữ liệu giả lập (mock data) để đảm bảo code python `mrjob` không lỗi cú pháp.
7. **Kiểm tra DevOps Backup/Restore**:
   - Chạy thử script backup sinh file zip/tar và phục hồi thử dữ liệu MySQL/MongoDB trên bảng tạm.

---

## 3. Các Chu Kỳ Kiểm Thử Thủ Công Chi Tiết (Manual Verification Cycles)

Nếu muốn xác minh thủ công từng bộ phận riêng lẻ, thực hiện theo các bước dưới đây:

### 3.1. Cycle 0: Kiểm tra Hạ Tầng Dịch Vụ Nền
*Mục tiêu: Đảm bảo các tiến trình daemon lõi (Big Data & DB) đang chạy bình thường.*

1. **Hadoop HDFS & YARN**:
   * **Lệnh chạy**: `jps`
   * **Kỳ vọng**: Phải hiển thị đủ tối thiểu 5 tiến trình: `NameNode`, `DataNode`, `SecondaryNameNode`, `ResourceManager`, `NodeManager`.
2. **SSH Passwordless Localhost**:
   * **Lệnh chạy**: `ssh localhost`
   * **Kỳ vọng**: Đăng nhập thành công vào chính máy ảo WSL mà không cần nhập mật khẩu.
3. **Kiểm tra Port của các Dịch vụ**:
   * **Lệnh chạy**: `ss -tln | grep -E "3306|27017|9000|10000|8501"`
   * **Kỳ vọng**: Sẽ thấy các port tương ứng hiển thị trạng thái `LISTEN`.

### 3.2. Cycle 1: Kiểm tra Môi trường Python & Dependencies
*Mục tiêu: Đảm bảo venv đã được cấu hình chính xác và cài đặt đầy đủ các thư viện cần thiết.*

* **Lệnh chạy**:
  ```bash
  source venv/bin/activate
  python -V
  pip list | grep -E "mrjob|streamlit|pymongo|mysql-connector-python|scrapy|pyhive"
  deactivate
  ```
* **Kỳ vọng**: Trả về phiên bản Python (3.10 hoặc 3.11) và hiển thị danh sách các thư viện cốt lõi không bị thiếu hay báo lỗi.

### 3.3. Cycle 2: Kiểm tra Cơ sở Dữ liệu & Data Ingestion (ETL)
*Mục tiêu: Xác minh quá trình ETL đã cào dữ liệu và đẩy vào DB cục bộ thành công.*

1. **MySQL (Dữ liệu đã làm sạch)**:
   * **Lệnh chạy**:
     ```bash
     mysql -h 127.0.0.1 -u root -proot food_sentiment_db -e "
       SHOW TABLES;
       SELECT COUNT(*) AS total_restaurants FROM restaurants;
       SELECT COUNT(*) AS total_reviews FROM reviews;
       SELECT COUNT(*) AS total_meals FROM meals;
       SELECT id, name, district_parsed, city FROM restaurants LIMIT 3;
     "
     ```
   * **Kỳ vọng**: Trả về danh sách 3 bảng (`restaurants`, `reviews`, `meals`), số lượng records > 1000, và dữ liệu cột `district_parsed` được trích xuất chính xác (ví dụ: "Quận 1", "Quận Bình Thạnh").
2. **MongoDB (Dữ liệu thô)**:
   * **Lệnh chạy**:
     ```bash
     mongosh sentiment_db --eval "db.restaurants.countDocuments(); db.meals.countDocuments();"
     ```
   * **Kỳ vọng**: Lệnh thực thi thành công và in ra số lượng document (khác 0) cho mỗi collection.

### 3.4. Cycle 3: Kiểm tra Đồng bộ HDFS và Apache Hive
*Mục tiêu: Dữ liệu đã ở trên HDFS và Hive đã map thành công.*

1. **Dữ liệu thô trên HDFS Storage**:
   * **Lệnh chạy**: `hdfs dfs -ls -R /data/raw`
   * **Kỳ vọng**: Liệt kê cấu trúc thư mục chứa các file `/data/raw/restaurants/restaurants.jsonl` và `/data/raw/meals/meals.jsonl`.
2. **Truy vấn Apache Hive**:
   * **Lệnh chạy**:
     ```bash
     hive -e "USE food_sentiment_db; SHOW TABLES; SELECT * FROM mr_rating_by_district LIMIT 3;"
     ```
   * **Kỳ vọng**: Truy cập Metastore thành công, hiển thị các bảng Hive View đã tạo và in ra 3 dòng dữ liệu hợp lệ (nếu MapReduce job đã chạy).

### 3.5. Cycle 4: Kiểm tra Engine MapReduce (YARN Execution)
*Mục tiêu: Đảm bảo các job MapReduce chạy trơn tru trên YARN.*

* **Lệnh chạy**:
  ```bash
  source venv/bin/activate
  python src/mapreduce/mr_rating_by_district.py -r hadoop hdfs:///data/raw/restaurants/restaurants.jsonl
  deactivate
  ```
* **Kỳ vọng**: Hadoop YARN sẽ cấp phát container, khởi chạy Map và Reduce tasks, in ra log tiến trình (`map 0% reduce 0%` -> `map 100% reduce 100%`). Cuối cùng hiển thị kết quả phân tích thống kê điểm đánh giá trung bình của từng quận.

### 3.6. Cycle 5: Kiểm tra Backup & Restore tự động
*Mục tiêu: Đảm bảo an toàn dữ liệu trước khi nâng cấp hoặc xóa trắng.*

* **Lệnh chạy**:
  ```bash
  bash src/backup/db_backup.sh
  ls -lah data/backups/
  ```
* **Kỳ vọng**: Bash script chạy không báo lỗi. Thư mục `data/backups/` sinh ra một thư mục timestamp chứa các file `.sql` và `.archive` có dung lượng > 0 bytes.

### 3.7. Cycle 6: Kiểm tra Tương tác Giao Diện Streamlit App
*Mục tiêu: Chạy thử luồng ứng dụng Frontend Dashboard.*

1. **Lệnh chạy**:
   ```bash
   source venv/bin/activate
   streamlit run src/streamlit_app/app.py
   ```
2. **Kỳ vọng**:
   * Terminal in ra URL: `Network URL: http://<ip>:8501`.
   * Mở trình duyệt web của máy host và truy cập `http://localhost:8501`.
   * Giao diện Streamlit hiển thị thành công.
   * Thao tác CRUD (Create, Read, Update, Delete) trực quan trên tab dữ liệu.
   * Tab báo cáo hiển thị chính xác 6 biểu đồ phân tích tích hợp dữ liệu từ Hive.
