# Hướng Dẫn Cài Đặt và Khởi Chạy Hệ Thống (WSL2 Ubuntu 24.04 LTS)

Tài liệu này cung cấp hướng dẫn từng bước để cài đặt toàn bộ hạ tầng dữ liệu lớn (Hadoop, Hive, MySQL, MongoDB, Java, Python venv) và chạy pipeline thu thập/đồng bộ dữ liệu của dự án. Quy trình này được thiết kế hoàn toàn tổng quát (generic), không phụ thuộc vào bất kỳ tên người dùng hay đường dẫn cứng nào.

---

## 1. Yêu Cầu Hệ Thống & Chuẩn Bị

* **Hệ điều hành**: Ubuntu 24.04 LTS chạy trên WSL2 (Windows Subsystem for Linux).
* **Quyền hạn**: Tài khoản của bạn phải có quyền `sudo` để thực hiện cài đặt các gói hệ thống.
* **Mạng**: Đảm bảo kết nối internet ổn định để tải các gói phần mềm và các file cài đặt Hadoop/Hive (~1.3 GB tổng cộng).

---

## 2. Quy Trình Cài Đặt Từng Bước (Step-by-Step)

Sau khi pull repository này về máy, hãy mở terminal WSL2 Ubuntu và thực hiện tuần tự các bước sau:

### Bước 2.1: Phân quyền thực thi cho các script shell
Chạy lệnh sau tại thư mục gốc của dự án:
```bash
chmod +x bin/*.sh
```

### Bước 2.2: Cài đặt và cấu hình Hạ tầng Dữ liệu lớn (Cycle 0)
Chạy script cài đặt hạ tầng:
```bash
./bin/install_infra.sh
```
**Script này sẽ tự động thực hiện:**
1. Cấu hình SSH Server và SSH passwordless localhost access (cần thiết cho Hadoop).
2. Cài đặt OpenJDK 11 (cho Hadoop) và OpenJDK 8 (cho Hive).
3. Thêm các biến môi trường cần thiết (`JAVA_HOME`, `HADOOP_HOME`, `HIVE_HOME`, `PATH`) vào phần đầu của file `~/.bashrc`.
4. Cài đặt và cấu hình MySQL Server, tạo CSDL `food_sentiment_db` và `hive_metastore` kèm theo phân quyền cho root/hive.
5. Cài đặt MongoDB Community Server 8.0.
6. Tải và giải nén Apache Hadoop 3.3.6, cấu hình các file XML (`core-site`, `hdfs-site`, `yarn-site`, `mapred-site`), định dạng NameNode và khởi động các service Hadoop.
7. Tải và cấu hình Apache Hive 3.1.3, tải MySQL JDBC Connector, sửa lỗi xung đột thư viện Guava và khởi tạo Hive Metastore Schema.

### Bước 2.3: Reload biến môi trường
Sau khi `install_infra.sh` hoàn thành, bạn **cần nạp lại (reload) biến môi trường** của terminal hiện tại để áp dụng các thay đổi trong `~/.bashrc`:
```bash
source ~/.bashrc
```

### Bước 2.4: Thiết lập môi trường ảo Python và khởi tạo database
Chạy kịch bản setup môi trường Python:
```bash
./bin/setup.sh
```
**Script này sẽ tự động thực hiện:**
1. Kiểm tra và cài đặt các gói hệ thống cơ bản (`python3`, `python3-venv`, `python3-pip`).
2. Khởi tạo môi trường ảo Python `venv` trong thư mục gốc dự án.
3. Cài đặt tất cả các thư viện Python cần thiết từ `requirements.txt`.
4. Chạy script `src/ingest/init_db.py` để di trú dữ liệu thô sang các bảng MySQL (`restaurants`, `reviews`, `meals`).

---

## 3. Khởi Chạy Toàn Bộ Hệ Thống (Run Pipeline)

Khi hạ tầng và môi trường ảo đã được chuẩn bị xong, bạn chạy lệnh sau để kích hoạt toàn bộ hệ thống pipeline và giao diện dashboard:

```bash
./bin/run.sh
```

**Script này sẽ tự động:**
1. Khởi động các dịch vụ nền (MySQL, MongoDB, Hadoop NameNode/DataNode, YARN ResourceManager/NodeManager).
2. Kiểm tra trạng thái cổng kết nối để đảm bảo các dịch vụ hoạt động bình thường.
3. Kích hoạt môi trường ảo Python `venv`.
4. Chạy crawler lấy dữ liệu công thức món ăn từ API TheMealDB và TripAdvisor.
5. Chạy các pipeline đồng bộ dữ liệu thô từ MongoDB và MySQL lên HDFS (`/data/raw/`).
6. Khởi chạy Dashboard Streamlit trên cổng `8501`.

Khi Streamlit khởi chạy thành công, bạn có thể mở trình duyệt trên Windows và truy cập địa chỉ:
👉 **[http://localhost:8501](http://localhost:8501)**
