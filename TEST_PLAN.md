# Kế Hoạch Kiểm Thử Toàn Hệ Thống (Master Manual Test Plan)

Tài liệu này cung cấp các lệnh chạy trực tiếp trên terminal WSL (Ubuntu 24.04) để kiểm tra thủ công toàn bộ các module và dịch vụ của hệ thống Phân tích Cảm xúc Đồ ăn & Nhà hàng. Bạn có thể tự mình copy/paste từng lệnh vào WSL để verify.

---

## 0. Kiểm tra Bin Scripts & Unit Tests (Pre-flight)
Mục tiêu: Đảm bảo các script điều khiển hệ thống và các hàm tiện ích cốt lõi hoạt động đúng.

### 0.1. Kiểm tra Script Parameters
* **Lệnh chạy**:
  ```bash
  bash bin/run.sh --help
  bash bin/stop.sh --help
  ```
* **Kỳ vọng**: In ra màn hình trợ giúp hiển thị đúng thông tin các flags (`--crawl`, `--jobs`, `--backup`, `--cleandata`).

### 0.2. Kiểm tra Python Unit Tests
* **Lệnh chạy**:
  ```bash
  source venv/bin/activate
  python src/mapreduce/test_district_parsing.py
  deactivate
  ```
* **Kỳ vọng**: In ra danh sách các test case và thông báo "All checks passed ✅".

---

## 1. Kiểm tra Hạ Tầng Dịch Vụ Nền (Cycle 0)
Mục tiêu: Đảm bảo các tiến trình daemon lõi (Big Data & DB) đang chạy bình thường.

### 1.1. Hadoop HDFS & YARN
* **Lệnh chạy**: 
  ```bash
  jps
  ```
* **Kỳ vọng**: Phải hiển thị đủ tối thiểu 5 tiến trình: `NameNode`, `DataNode`, `SecondaryNameNode`, `ResourceManager`, `NodeManager`.

### 1.2. SSH Passwordless Localhost
* **Lệnh chạy**:
  ```bash
  ssh localhost
  ```
* **Kỳ vọng**: Đăng nhập thành công vào chính máy ảo WSL mà không cần nhập mật khẩu. (Sau đó gõ `exit` để thoát ra session ban đầu).

### 1.3. Kiểm tra Port của các Dịch vụ
* **Lệnh chạy**: 
  ```bash
  ss -tln | grep -E "3306|27017|9000|10000|8501"
  ```
* **Kỳ vọng**: Sẽ thấy các port đang ở trạng thái `LISTEN`:
  - `3306`: MySQL Server
  - `27017`: MongoDB Server
  - `9000`: Hadoop HDFS NameNode
  - `10000`: HiveServer2 (nếu dịch vụ HiveServer2 đang chạy)
  - `8501`: Streamlit Web App (nếu app Streamlit đang bật)

---

## 2. Kiểm tra Môi trường Python (Cycle 1)
Mục tiêu: Đảm bảo `venv` đã cấu hình đúng và cài đặt đủ các thư viện cần thiết.

* **Lệnh chạy**:
  ```bash
  source venv/bin/activate
  python -V
  pip list | grep -E "mrjob|streamlit|pymongo|mysql-connector-python|scrapy|pyhive"
  deactivate
  ```
* **Kỳ vọng**: Trả về phiên bản Python (3.10 hoặc 3.11) và hiển thị danh sách các thư viện cốt lõi không bị báo lỗi thiếu package.

---

## 3. Kiểm tra Cơ sở Dữ liệu & Data Ingestion (Cycle 2)
Mục tiêu: Xác minh quá trình ETL đã cào dữ liệu và đẩy vào DB cục bộ.

### 3.1. MySQL (Dữ liệu đã làm sạch)
* **Lệnh chạy**:
  ```bash
  mysql -h 127.0.0.1 -u root food_sentiment_db -e "
    SHOW TABLES;
    SELECT COUNT(*) AS total_restaurants FROM restaurants;
    SELECT COUNT(*) AS total_reviews FROM reviews;
    SELECT COUNT(*) AS total_meals FROM meals;
    SELECT id, name, district_parsed, city FROM restaurants LIMIT 3;
  "
  ```
* **Kỳ vọng**: Trả về danh sách 3 bảng, số lượng records lớn hơn 0, và dữ liệu cột `district_parsed` được extract chính xác, không phải "Unknown".

### 3.2. MongoDB (Dữ liệu thô)
* **Lệnh chạy**:
  ```bash
  mongosh sentiment_db --eval "db.restaurants.countDocuments(); db.meals.countDocuments();"
  ```
* **Kỳ vọng**: Lệnh thực thi thành công và in ra số lượng document (khác 0) cho mỗi collection.

---

## 4. Kiểm tra Đồng bộ HDFS và Apache Hive (Cycle 3)
Mục tiêu: Dữ liệu đã ở trên HDFS và Hive đã map thành bảng External thành công.

### 4.1. Dữ liệu thô trên HDFS Storage
* **Lệnh chạy**: 
  ```bash
  hdfs dfs -ls -R /data/raw
  ```
* **Kỳ vọng**: Liệt kê cấu trúc thư mục chứa các file `/data/raw/restaurants/restaurants.jsonl` và `/data/raw/meals/meals.jsonl`.

### 4.2. Truy vấn Apache Hive
* **Lệnh chạy**:
  ```bash
  hive -e "USE food_sentiment_db; SHOW TABLES; SELECT * FROM mr_rating_by_district LIMIT 3;"
  ```
* **Kỳ vọng**: Truy cập Metastore thành công, hiển thị các bảng Hive View đã tạo và in ra 3 dòng dữ liệu hợp lệ (nếu MapReduce job đã chạy).

---

## 5. Kiểm tra Engine MapReduce (Cycle 4)
Mục tiêu: Đảm bảo luồng chạy job MapReduce thông qua thư viện `mrjob` hoạt động trơn tru trên YARN.

* **Lệnh chạy**:
  ```bash
  source venv/bin/activate
  python src/mapreduce/mr_rating_by_district.py -r hadoop hdfs:///data/raw/restaurants/restaurants.jsonl
  deactivate
  ```
* **Kỳ vọng**: Hadoop YARN sẽ cấp phát container, khởi chạy Map và Reduce tasks (sẽ hiển thị log tiến trình như `map 0% reduce 0%` -> `map 100% reduce 100%`). Cuối cùng sẽ in ra kết quả phân tích thống kê (điểm trung bình rating theo từng quận).

---

## 6. Kiểm tra Backup & Restore (Cycle 5)
Mục tiêu: Test kịch bản DevOps tự động sao lưu an toàn CSDL.

* **Lệnh chạy**:
  ```bash
  # MySQL và MongoDB phải đang chạy
  bash src/backup/db_backup.sh
  ls -lah data/backups/
  ```
* **Kỳ vọng**: Bash script không báo lỗi. Thư mục `data/backups/` có sinh ra một folder chứa timestamp (ví dụ: `backup_20260614_xxx`) và bên trong chứa các tệp tin dump (`.sql` cho MySQL và `.bson`/`.archive` cho MongoDB) có dung lượng > 0 bytes.

---

## 7. Kiểm tra Tương tác Streamlit GUI (Cycle 6)
Mục tiêu: Chạy thử luồng ứng dụng Frontend Dashboard.

* **Lệnh chạy**:
  ```bash
  source venv/bin/activate
  streamlit run src/streamlit_app/app.py
  ```
* **Kỳ vọng**: 
  1. Terminal in ra URL: `Network URL: http://<ip>:8501`.
  2. Mở trình duyệt web bên phía hệ điều hành Windows host và truy cập `http://localhost:8501`.
  3. Giao diện Web App hiển thị lên mà không có lỗi Exception màu đỏ.
  4. Thử bấm vào tab báo cáo (Reports) để kiểm tra các biểu đồ Hive/MapReduce có hiển thị dữ liệu thành công hay không.
