# Nhật ký thực thi (Execution Log) - Cycle 0 & Cycle 2

**Ngày thực hiện:** 13/06/2026

## 1. Các hạng mục đã triển khai

### Cycle 0: Thiết lập & Kiểm tra Môi trường
- [x] **Setup Script (`bin/setup.sh`)**:
  - Tự động kiểm tra và cài đặt Python virtual environment `venv`, pip dependencies, và Java JDK 11.
  - Tích hợp chạy file khởi tạo và di trú dữ liệu MySQL.
- [x] **Run Script (`bin/run.sh`)**:
  - Quản lý nạp biến môi trường (`JAVA_HOME`, `HADOOP_HOME`, `PATH`).
  - Kiểm tra và tự động khởi động các daemon `mysql`, `mongod`, `start-dfs.sh` (HDFS) và `start-yarn.sh` (YARN).
  - Tích hợp kiểm tra cổng (Ports 3306, 27017, 9000, 10000).
  - Chạy chuỗi pipeline và khởi chạy giao diện dashboard Streamlit.
- [x] **MySQL Database Init (`src/ingest/init_db.py`)**:
  - Khởi tạo CSDL `food_sentiment_db`.
  - Tạo cấu trúc bảng chuẩn hóa: `restaurants`, `reviews`, `meals` với các khóa chính và khóa ngoại liên kết.
  - Đọc dữ liệu thô từ MongoDB để phân tách và di trú sang các bảng MySQL tránh trùng lặp.

### Cycle 2: Đồng bộ HDFS & Apache Hive Integration
- [x] **MongoDB to HDFS (`src/ingest/mongo_to_hdfs.py`)**:
  - Kết nối và kết xuất dữ liệu bộ sưu tập MongoDB thành tệp JSON Lines (`.jsonl`).
  - Đổi tên trường `_id` của MongoDB thành `id` để tương thích cấu trúc cột của Hive.
  - Đẩy dữ liệu lên thư mục riêng biệt của HDFS (`/data/raw/restaurants/` và `/data/raw/meals/`).
- [x] **MySQL to HDFS (`src/ingest/mysql_to_hdfs.py`)**:
  - Kết xuất trực tiếp các bảng quan hệ sạch từ MySQL sang `.jsonl` và tải lên HDFS (`/data/raw/mysql_restaurants/`, `/data/raw/mysql_reviews/`, `/data/raw/mysql_meals/`).
- [x] **Hive Schema Definition (`src/ingest/hive_schema.sql`)**:
  - Định nghĩa cơ sở dữ liệu `food_sentiment_db` trên Apache Hive.
  - Tạo các bảng External định dạng JSON (`org.apache.hive.hcatalog.data.JsonSerDe`) ánh xạ trực tiếp đến các thư mục lưu trữ dữ liệu thô tương ứng trên HDFS.

---

## 2. Các tệp tin được tạo mới và cập nhật

- [requirements.txt](file:///d:/Project/final-bdes/requirements.txt) (Cập nhật thư viện `mysql-connector-python`)
- [bin/setup.sh](file:///d:/Project/final-bdes/bin/setup.sh) (Mới)
- [bin/run.sh](file:///d:/Project/final-bdes/bin/run.sh) (Mới)
- [src/ingest/init_db.py](file:///d:/Project/final-bdes/src/ingest/init_db.py) (Mới)
- [src/ingest/mongo_to_hdfs.py](file:///d:/Project/final-bdes/src/ingest/mongo_to_hdfs.py) (Mới)
- [src/ingest/mysql_to_hdfs.py](file:///d:/Project/final-bdes/src/ingest/mysql_to_hdfs.py) (Mới)
- [src/ingest/hive_schema.sql](file:///d:/Project/final-bdes/src/ingest/hive_schema.sql) (Mới)

---

## 3. Hướng dẫn kiểm tra nhanh trên WSL2

Mở terminal Ubuntu trên WSL2 và thực hiện các lệnh sau để khởi chạy:

```bash
# 1. Chạy thiết lập môi trường và di trú CSDL
chmod +x bin/setup.sh
./bin/setup.sh

# 2. Kích hoạt môi trường ảo Python (Virtual Environment) trong terminal hiện tại
source venv/bin/activate

# 3. Chạy toàn bộ hệ thống (khởi động Hadoop, MySQL, MongoDB và Streamlit)
chmod +x bin/run.sh
./bin/run.sh
```

---

## 4. Nhật ký xử lý sự cố trong quá trình thực thi

### Sự cố 4.1: Thiếu dịch vụ MySQL & MongoDB (Unit not found)
* **Triệu chứng**: Kịch bản chạy `sudo service mysql start` hoặc `mongod start` báo lỗi dịch vụ không tồn tại.
* **Nguyên nhân**: Phân phối Ubuntu trên WSL2 là môi trường mới hoàn toàn và chưa được cài đặt các dịch vụ cơ sở dữ liệu.
* **Giải pháp khắc phục**:
  1. Cài đặt MySQL Server thông qua gói chính thức: `sudo apt install mysql-server -y`.
  2. Thêm GPG key và repo chính thức của MongoDB 8.0 cho Ubuntu, sau đó cài đặt `mongodb-org`.

### Sự cố 4.2: Lỗi phân quyền truy cập MySQL `Access denied for user 'root'@'localhost'` (Error 1698/1524)
* **Triệu chứng**: Khi script `init_db.py` chạy kết nối tới `127.0.0.1:3306` bằng tài khoản `root` và mật khẩu rỗng thì bị từ chối kết nối. Thử dùng plugin `mysql_native_password` thì báo lỗi `Plugin is not loaded`.
* **Nguyên nhân**: 
  * MySQL trên Ubuntu mặc định dùng `auth_socket` ngăn chặn ứng dụng kết nối trực tiếp với tài khoản root mà không qua sudo.
  * MySQL 8.4+ đã tắt mặc định plugin cũ `mysql_native_password`.
  * MySQL coi kết nối từ `localhost` (Unix socket) và `127.0.0.1` (TCP/IP) là hai host profile độc lập.
* **Giải pháp khắc phục**:
  1. Đăng nhập vào MySQL CLI qua sudo: `sudo mysql -u root`.
  2. Cập nhật mật khẩu trống cho cả hai host bằng plugin xác thực mặc định mới (`caching_sha2_password`):
     ```sql
     CREATE USER IF NOT EXISTS 'root'@'127.0.0.1' IDENTIFIED BY '';
     ALTER USER 'root'@'127.0.0.1' IDENTIFIED BY '';
     GRANT ALL PRIVILEGES ON *.* TO 'root'@'127.0.0.1' WITH GRANT OPTION;
     ALTER USER 'root'@'localhost' IDENTIFIED BY '';
     GRANT ALL PRIVILEGES ON *.* TO 'root'@'localhost' WITH GRANT OPTION;
     FLUSH PRIVILEGES;
     ```
  3. Khởi động lại MySQL: `sudo service mysql restart`.

