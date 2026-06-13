# Kế hoạch triển khai & Nhật ký (Cycle 0 & Cycle 2)

## 1. Trạng thái hiện tại từ MASTERPLAN.md
- **Cycle 0**:
  - [x] Task 0.1: Khởi tạo cấu trúc cây thư mục (Đã hoàn thành)
  - [ ] Task 0.2: Viết kịch bản `bin/setup.sh` (Cần triển khai)
  - [ ] Task 0.3: Viết kịch bản `bin/run.sh` (Cần triển khai)
- **Cycle 1**:
  - [x] Task 1.1: TripAdvisor Crawler (Đã hoàn thành)
  - [x] Task 1.2: TheMealDB API Parser (Đã hoàn thành)
  - [x] Task 1.3: Database Schema & Ingestion (Đã được tích hợp vào các pipeline thu thập)
- **Cycle 2**:
  - [ ] Task 2.1: Đồng bộ MySQL/MongoDB sang HDFS (`src/ingest/mongo_to_hdfs.py`, `src/ingest/mysql_to_hdfs.py`) (Cần triển khai)
  - [ ] Task 2.2: Thiết lập Schema cho Apache Hive (`src/ingest/hive_schema.sql`) (Cần triển khai)

---

## 2. Kế hoạch chi tiết cho các bước tiếp theo

### Bước 2.1: Triển khai kịch bản Setup môi trường (`bin/setup.sh`)
- **Mục tiêu**: Tự động cài đặt các thư viện cần thiết, thiết lập môi trường ảo Python `venv` trên WSL2 và khởi tạo CSDL MySQL, MongoDB.
- **Nội dung chính**:
  1. Kiểm tra và cài đặt `python3-pip`, `python3-venv`, `openjdk-11-jdk`.
  2. Tạo môi trường ảo: `python3 -m venv venv`.
  3. Activate môi trường ảo và chạy `pip install -r requirements.txt`.
  4. Khởi tạo CSDL MySQL `food_sentiment_db` với các bảng: `restaurants`, `reviews`, `meals`.

### Bước 2.2: Triển khai kịch bản Chạy hệ thống (`bin/run.sh`)
- **Mục tiêu**: Tự động quản lý khởi động và tắt các dịch vụ nền (MySQL, MongoDB, HDFS, YARN), chạy pipeline đồng bộ dữ liệu và kích hoạt dashboard Streamlit.
- **Nội dung chính**:
  1. Export các biến môi trường (`JAVA_HOME`, `HADOOP_HOME`, `PATH`).
  2. Start MySQL và MongoDB daemon.
  3. Start HDFS (`start-dfs.sh`) và YARN (`start-yarn.sh`).
  4. Đồng bộ dữ liệu sang HDFS và chạy Streamlit.

### Bước 2.3: Viết mã nguồn đồng bộ dữ liệu sang HDFS (`src/ingest/`)
- **Mục tiêu**: Xuất dữ liệu từ MySQL/MongoDB ra định dạng `.jsonl` và tải lên HDFS tại đường dẫn `/data/raw/`.
- **Tập tin**:
  - `src/ingest/mongo_to_hdfs.py`
  - `src/ingest/mysql_to_hdfs.py`

### Bước 2.4: Khởi tạo Schema cho Apache Hive (`src/ingest/hive_schema.sql`)
- **Mục tiêu**: Định nghĩa các External Tables trong Apache Hive liên kết trực tiếp với dữ liệu thô trên HDFS để phục vụ các truy vấn phân tích OLAP.

---

## 3. Nhật ký cập nhật tiến độ (Logs)
- **13/06/2026**:
  - Đã rà soát lại toàn bộ dự án và đối chiếu với `MASTERPLAN.md`.
  - Phát hiện các phần code Python cào dữ liệu đã xong nhưng chưa có kịch bản chạy shell script và đồng bộ lên HDFS.
  - Thiết lập thành công kế hoạch triển khai cho Cycle 0 & Cycle 2.
