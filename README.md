# Đồ án Nhập môn Dữ liệu lớn (BDES333877)
## Hệ thống phân tích ý kiến khách hàng và quản lý ẩm thực (Food & Restaurant Sentiment Analysis System)

Dự án cuối kỳ của nhóm 4 thành viên. Dự án được phát triển và chạy trực tiếp trên môi trường **Ubuntu 24.04 LTS trên WSL2 (Windows Subsystem for Linux)** thông qua các tập lệnh tự động hóa Bash Shell.

---

## 1. Thành viên nhóm & Phân công công việc

| STT | Họ và Tên | MSSV | Vai trò chính | Chi tiết công việc thực hiện | Tỉ lệ đóng góp |
| :--- | :--- | :---: | :--- | :--- | :---: |
| 1 | **Nguyễn Văn A** (Trưởng nhóm) | 23112233 | Data Engineer & DB | - Viết mã Python để cào dữ liệu từ TripAdvisor & Gọi API TheMealDB.<br>- Thiết lập MongoDB (Staging thô) và MySQL (CSDL quan hệ cho CRUD). | 100% |
| 2 | **Trần Thị B** | 23112244 | Hadoop Infrastructure | - Cấu hình hạ tầng Hadoop (HDFS/YARN) và Apache Hive trên WSL2.<br>- Thiết lập Sqoop hoặc Python scripts đồng bộ MySQL/MongoDB sang HDFS. | 100% |
| 3 | **Phan Kim E** | 23112235 | MapReduce Developer | - Xây dựng và tối ưu 8 chương trình MapReduce bằng Python (`mrjob`).<br>- Viết kịch bản sao lưu và phục hồi dữ liệu tự động (`db_backup.sh`/`db_restore.sh`). | 100% |
| 4 | **Bùi Quang F** | 23112236 | UI Developer & Media | - Phát triển giao diện Dashboard tương tác bằng Streamlit (CRUD trên MySQL, trực quan hóa OLAP từ Hive).<br>- Soạn Slide đề cương & biên tập video demo. | 100% |

---

## 2. Kiến trúc hệ thống & Luồng dữ liệu tinh gọn

Hệ thống được thiết kế theo mô hình lai **Hybrid Database (Polyglot Persistence)** kết hợp giữa Cơ sở dữ liệu tác nghiệp (OLTP) và Kho dữ liệu phân tích lớn (OLAP) một cách logic nhất:

```text
[ TripAdvisor (Scrape) ] --+
                           +--> [ MongoDB (NoSQL Staging) ] --+
[ TheMealDB (REST API) ] --+                                  |
                                                              +--> [ HDFS (JSONL) ] --> [ MapReduce ] --> [ HDFS (Processed) ]
                           +--> [ MySQL (Relational DB) ] ----+                                                  |
                           |                                                                                     v
  [ Streamlit GUI ] <------+ (CRUD & SQL Queries thời gian thực)                                          [ Apache Hive ]
        |                                                                                                        ^
        +--------------------------------------------------------------------------------------------------------+
                                         (Truy vấn SQL phân tích OLAP)
```

1.  **Thu thập (Ingestion):** TripAdvisor Scraper cào dữ liệu bán cấu trúc lồng nhau (nhà hàng & reviews), TheMealDB API cung cấp danh mục nguyên liệu/món ăn.
2.  **Lưu trữ thô & Tác nghiệp (Staging & OLTP):**
    *   **MongoDB:** Lưu trữ dữ liệu thô bán cấu trúc từ TripAdvisor phục vụ backup hoặc trích xuất thuộc tính phức tạp.
    *   **MySQL:** Lưu trữ dữ liệu sau khi làm sạch và chuẩn hóa (mô hình hóa quan hệ: bảng restaurants, reviews, meals). Streamlit thực hiện **truy vấn SQL và các thao tác CRUD (Thêm, Đọc, Sửa, Xóa)** trực tiếp tại đây giúp hệ thống phản hồi thời gian thực tức thì.
3.  **Lưu trữ phân tán (OLAP Storage):** Dữ liệu được đồng bộ từ MySQL/MongoDB lên **HDFS** dưới dạng các tệp JSON Lines (`.jsonl`).
4.  **Xử lý phân tán (Processing):** 8 chương trình **MapReduce (Python `mrjob`)** chạy trên YARN/Hadoop thực hiện gom nhóm, phân tích tần suất nguyên liệu, sentiment analysis, và lưu kết quả ngược lại HDFS.
5.  **Kho dữ liệu & Trực quan (OLAP Data Warehouse & GUI):**
    *   **Apache Hive:** Ánh xạ kết quả xử lý của MapReduce trên HDFS thành các bảng Hive để tối ưu hóa truy vấn SQL phân tích lớn.
    *   **Streamlit Dashboard:** Truy cập trực tiếp MySQL để thực hiện nghiệp vụ CRUD hàng ngày, và kết nối **Apache Hive** (hoặc đọc file HDFS) để hiển thị 6 biểu đồ phân tích Big Data.

---

## 3. Cấu trúc thư mục mã nguồn

```text
food-sentiment-bigdata/
│
├── bin/                       # Tập lệnh tự động hóa Bash Shell trên WSL2
│   ├── setup.sh               # Thiết lập môi trường ảo venv, cài thư viện Python
│   └── run.sh                 # Thiết lập biến môi trường, khởi chạy MySQL, MongoDB, HDFS, Hive, Streamlit
│
├── config/                    # Thư mục chứa tệp cấu hình mẫu
│   ├── hadoop/                # core-site.xml, hdfs-site.xml, mapred-site.xml, yarn-site.xml
│   ├── mysql/                 # my.cnf
│   └── mongo/                 # mongod.conf
│
├── src/                       # Mã nguồn phát triển
│   ├── crawler/               # Crawler thu thập dữ liệu (TripAdvisor & TheMealDB API)
│   │   └── seed/              # Thư mục chứa dữ liệu tĩnh phòng hờ khi mất mạng
│   ├── ingest/                # Script đẩy dữ liệu từ MySQL/MongoDB sang HDFS (.jsonl)
│   ├── mapreduce/             # 8 chương trình MapReduce phân tích dữ liệu bằng Python (mrjob)
│   ├── backup/                # Script db_backup.sh và db_restore.sh
│   └── streamlit_app/         # Giao diện trực quan hóa và thao tác dữ liệu (Streamlit)
│
├── data/                      # Thư mục chứa dữ liệu cục bộ (Được thêm vào .gitignore)
│   ├── db/                    # Cơ sở dữ liệu vật lý của MongoDB
│   └── hdfs/                  # Dữ liệu vật lý của Hadoop NameNode/DataNode
│
├── docs/                      # Tài liệu báo cáo, Slides thuyết trình, Bảng tự chấm
└── requirements.txt           # Danh sách các thư viện Python cần cài đặt
```

---

## 4. Yêu cầu hệ thống tối thiểu & Cài đặt dịch vụ (Máy Teammate)

Để khởi chạy toàn bộ pipeline mượt mà trên môi trường Ubuntu 24.04/26.04 WSL2, máy tính của thành viên cần cấu hình sẵn các dịch vụ sau trong phân phối **Ubuntu**:

### 1. Phân phối hệ điều hành
* **Windows 10/11** có cài đặt **WSL2** và chạy phân phối **Ubuntu** (Lưu ý: chuyển phân phối mặc định của WSL về Ubuntu nếu cần: `wsl -s Ubuntu`).

### 2. Cài đặt Python 3.10 hoặc 3.11 & Java 11
Sử dụng virtual environment `venv` để tránh lỗi do thiếu `distutils` trên Python 3.12+:
```bash
sudo apt update
sudo apt install python3.10 python3.10-venv python3.10-dev openjdk-11-jdk -y
```

### 3. Cài đặt và cấu hình MySQL Server
```bash
# Cài đặt MySQL
sudo apt install mysql-server -y
sudo service mysql start

# Cấu hình tài khoản root cho phép kết nối từ script Python (host localhost & 127.0.0.1)
sudo mysql -u root -e "
CREATE USER IF NOT EXISTS 'root'@'127.0.0.1' IDENTIFIED BY '';
ALTER USER 'root'@'127.0.0.1' IDENTIFIED BY '';
GRANT ALL PRIVILEGES ON *.* TO 'root'@'127.0.0.1' WITH GRANT OPTION;
ALTER USER 'root'@'localhost' IDENTIFIED BY '';
GRANT ALL PRIVILEGES ON *.* TO 'root'@'localhost' WITH GRANT OPTION;
FLUSH PRIVILEGES;"

# Khởi động lại dịch vụ
sudo service mysql restart
```

### 4. Cài đặt và cấu hình MongoDB Server (Community Edition)
```bash
# Thêm MongoDB GPG key và repository
sudo apt-get install gnupg curl -y
curl -fsSL https://www.mongodb.org/static/pgp/server-8.0.asc | sudo gpg -o /usr/share/keyrings/mongodb-server-8.0.gpg --dearmor
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-8.0.gpg ] https://repo.mongodb.org/apt/ubuntu noble/mongodb-org/8.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-8.0.list

# Cài đặt và khởi chạy MongoDB
sudo apt update
sudo apt install -y mongodb-org
sudo service mongod start
```

### 5. Cài đặt Apache Hadoop 3.3.6 LTS
* Tải và giải nén Apache Hadoop 3.3.6 LTS vào thư mục `/usr/local/hadoop` và cấu hình Single-Node Cluster trên Linux.


---

## 5. Hướng dẫn khởi chạy nhanh (Quick Start Guide)

### Bước 1: Chuẩn bị môi trường (Chỉ cần chạy 1 lần duy nhất)
Mở terminal Ubuntu 24.04 trên WSL2, di chuyển đến thư mục dự án và chạy:
```bash
chmod +x bin/setup.sh
./bin/setup.sh
```
*Tác dụng:* Tự động khởi tạo môi trường ảo Python `venv` và cài đặt các dependencies, tạo cơ sở dữ liệu và bảng mẫu trong MySQL và MongoDB.

### Bước 2: Khởi chạy dự án
Chạy file script khởi động toàn bộ hệ thống:
```bash
chmod +x bin/run.sh
./bin/run.sh
```
*Tác dụng:* 
1. Khởi động các database daemons (`sudo service mysql start`, `sudo service mongod start`).
2. Khởi động Hadoop HDFS (`start-dfs.sh`) và YARN (`start-yarn.sh`).
3. Thực hiện cào dữ liệu mới và đồng bộ từ MySQL/MongoDB lên HDFS.
4. Kích hoạt Hive Server và chạy ứng dụng Streamlit trên cổng 8501. Bạn có thể mở trình duyệt trên Windows tại địa chỉ `http://localhost:8501`.