# Kế Hoạch Kiểm Thử (Test Plan) - Cycle 0 & Cycle 2

Tài liệu này hướng dẫn cách kiểm thử độc lập để xác minh tính chính xác của hạ tầng dữ liệu lớn (Cycle 0) và việc đồng bộ hóa dữ liệu lên HDFS & tích hợp Apache Hive (Cycle 2).

---

## 1. Kiểm Thử Cycle 0: Hạ Tầng Dịch Vụ Nền

Mục tiêu: Đảm bảo toàn bộ các dịch vụ nền đã chạy đúng cổng, đúng phiên bản cấu hình và không xảy ra xung đột.

### 1.1. Kiểm tra SSH Passwordless Localhost
Hadoop yêu cầu đăng nhập localhost không mật khẩu.
* **Lệnh chạy**:
  ```bash
  ssh localhost
  ```
* **Kết quả kỳ vọng**: Bạn đăng nhập được vào localhost thành công mà không bị hỏi mật khẩu (có thể gõ `exit` để quay lại phiên làm việc cũ).

### 1.2. Kiểm tra Java Environment
* **Lệnh chạy**:
  ```bash
  echo $JAVA_HOME
  java -version
  ```
* **Kết quả kỳ vọng**:
  * `$JAVA_HOME` trả về đúng `/usr/lib/jvm/java-11-openjdk-amd64`.
  * Phiên bản Java in ra là `11.0.x`.

### 1.3. Kiểm tra MySQL & Cơ cấu Database
* **Lệnh chạy**:
  ```bash
  mysql -h 127.0.0.1 -u root -e "SHOW DATABASES; USE food_sentiment_db; SHOW TABLES;"
  ```
* **Kết quả kỳ vọng**:
  * Hiển thị danh sách CSDL bao gồm `food_sentiment_db` và `hive_metastore`.
  * Có 3 bảng dữ liệu chuẩn hóa trong `food_sentiment_db`: `restaurants`, `reviews`, `meals`.

### 1.4. Kiểm tra MongoDB
* **Lệnh chạy**:
  ```bash
  mongosh --eval "db.adminCommand('ping')"
  ```
  *(Hoặc `mongo --eval` nếu dùng phiên bản cũ hơn, nhưng với MongoDB 8.0 sử dụng lệnh `mongosh`)*
* **Kết quả kỳ vọng**: In ra kết quả `ok: 1`.

### 1.5. Kiểm tra Hadoop (HDFS & YARN)
* **Lệnh chạy**:
  ```bash
  jps
  ```
* **Kết quả kỳ vọng**:
  Hiển thị danh sách các tiến trình Hadoop tối thiểu gồm:
  - `NameNode`
  - `DataNode`
  - `SecondaryNameNode`
  - `ResourceManager`
  - `NodeManager`

---

## 2. Kiểm Thử Cycle 2: Đồng Bộ HDFS & Tích Hợp Hive

Mục tiêu: Đảm bảo dữ liệu thô đã được đẩy thành công lên HDFS và Apache Hive có thể thực hiện truy vấn ngoài (External Table) dựa trên cấu trúc file JSONL đó.

### 2.1. Kiểm tra Dữ liệu trên HDFS
* **Lệnh chạy**:
  ```bash
  hdfs dfs -ls -R /data/raw
  ```
* **Kết quả kỳ vọng**:
  Hệ thống liệt kê đầy đủ các file dữ liệu `.jsonl` trong các thư mục HDFS:
  - `/data/raw/restaurants/`
  - `/data/raw/meals/`
  - `/data/raw/mysql_restaurants/`
  - `/data/raw/mysql_reviews/`
  - `/data/raw/mysql_meals/`

### 2.2. Kiểm tra Hive Integration & Query
* **Lệnh chạy**:
  ```bash
  # Chạy Hive CLI để truy vấn dữ liệu từ bảng External
  hive -e "USE food_sentiment_db; SHOW TABLES; SELECT * FROM restaurants LIMIT 5;"
  ```
* **Kết quả kỳ vọng**:
  * Hiển thị danh sách các bảng external (ví dụ: `restaurants`, `reviews`, `meals`, `mysql_restaurants`, v.v.).
  * Trả về kết quả truy vấn 5 bản ghi dữ liệu dưới dạng các cột rõ ràng, chứng tỏ Hive ánh xạ đúng file JSONL trên HDFS thông qua `JsonSerDe`.
