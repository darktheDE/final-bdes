# Đồ án Nhập môn Dữ liệu lớn (BDES333877)
## Hệ thống phân tích ý kiến khách hàng và quản lý ẩm thực (Food & Restaurant Sentiment Analysis System)

Dự án cuối kỳ của nhóm 4 thành viên. Dự án được phát triển và chạy trực tiếp trên môi trường **Ubuntu 24.04 LTS trên WSL2 (Windows Subsystem for Linux)** thông qua các tập lệnh tự động hóa Bash Shell.

---

## 1. Thành viên nhóm & Phân công công việc

| STT | Họ và Tên | MSSV | Vai trò chính | Chi tiết công việc thực hiện | Tỉ lệ đóng góp |
| :--- | :--- | :---: | :--- | :--- | :---: |
| 1 | **Nguyễn Văn A** (Trưởng nhóm) | 23112233 | Data Engineer & DB | - Viết mã Python để cào dữ liệu từ TripAdvisor & Gọi API TheMealDB.<br>- Thiết lập MongoDB (Staging thô) và MySQL (CSDL quan hệ cho CRUD). | 100% |
| 2 | **Trần Thị B** | 23112244 | Hadoop Infrastructure | - Cấu hình hạ tầng Hadoop (HDFS/YARN) và Apache Hive trên WSL2.<br>- Viết Python scripts đồng bộ MySQL/MongoDB sang HDFS. | 100% |
| 3 | **Phan Kim E** | 23112235 | MapReduce Developer | - Xây dựng và tối ưu 8 chương trình MapReduce bằng Python (`mrjob`).<br>- Viết kịch bản sao lưu và phục hồi dữ liệu tự động (`db_backup.sh`/`db_restore.sh`). | 100% |
| 4 | **Bùi Quang F** | 23112236 | UI Developer & Media | - Phát triển giao diện Dashboard tương tác bằng Streamlit (CRUD trên MySQL, trực quan hóa OLAP từ Hive).<br>- Soạn Slide đề cương & biên tập video demo. | 100% |

---

## 2. Kiến trúc hệ thống & Luồng dữ liệu

Hệ thống được thiết kế theo mô hình **Hybrid Database (Polyglot Persistence)** kết hợp OLTP và OLAP:

```text
[ TripAdvisor (Scrapy) ] --+
                           +--> [ MongoDB (NoSQL Staging) ] --+
[ TheMealDB (REST API) ] --+                                  |
                                                              +--> [ HDFS (.jsonl) ] --> [ MapReduce x8 ] --> [ HDFS (Results) ]
                           +--> [ MySQL (Relational OLTP) ] --+                                                       |
                                      |                                                                                v
                            [ Streamlit CRUD ]                                                               [ Apache Hive (OLAP) ]
                                      |                                                                                |
                                      +------------------------------------------------------------------------> [ Streamlit Reports ]
```

### Kết nối TripAdvisor ↔ TheMealDB
- **TripAdvisor**: Dữ liệu nhà hàng HCMC (restaurant info, customer reviews, ratings)
- **TheMealDB**: Dữ liệu công thức nấu ăn quốc tế (category, area, ingredients list)
- **Điểm kết nối** (`mr_ingredient_match.py`): Dùng danh sách `ingredients` từ TheMealDB làm từ điển để match các nguyên liệu được đề cập trong review TripAdvisor → tìm ra nguyên liệu nào phổ biến nhất trong đánh giá nhà hàng HCMC.

---

## 3. Tech Stack & Phiên bản

| Component | Version | Vai trò |
|---|---|---|
| OpenJDK | **8** LTS | Runtime cho Hadoop & Hive (bắt buộc, Java 11+ gây lỗi Kryo) |
| Apache Hadoop | **3.3.6** | HDFS phân tán + YARN task scheduler |
| Apache Hive | **3.1.3** | Data warehouse / OLAP SQL trên HDFS |
| MongoDB Community | **8.0** LTS | Raw data staging (semi-structured) |
| MySQL Server | **8.0** | Relational OLTP database |
| Python | 3.10 / 3.11 | MapReduce (mrjob), crawler, ingest scripts |
| Streamlit | **1.35.0** | Web dashboard (port 8501) |
| Scrapy | **2.11.0** | TripAdvisor spider |

---

## 4. Cấu trúc thư mục

```text
final-bdes/
│
├── bin/                        # Bash scripts — entry points
│   ├── install_infra.sh        # Chạy 1 lần: cài Java, Hadoop, Hive, MySQL, MongoDB, venv
│   ├── run.sh                  # Chạy pipeline: start services + Streamlit
│   └── stop.sh                 # Dừng tất cả dịch vụ
│
├── conf/                       # Config files (tách riêng khỏi scripts)
│   ├── hadoop/                 # core-site.xml, hdfs-site.xml, yarn-site.xml, mapred-site.xml
│   ├── hive/                   # hive-site.xml
│   └── mrjob.conf              # mrjob Hadoop runner config
│
├── src/
│   ├── crawler/                # Data crawling
│   │   ├── tripadvisor_job/    # Scrapy spider
│   │   ├── fetch_mealdb.py     # TheMealDB API client
│   │   └── seed/               # Offline fallback data (restaurants.json, meals.json, ...)
│   ├── ingest/                 # Data normalization & DB initialization
│   │   ├── init_db.py          # MySQL schema init + normalize data from MongoDB
│   │   ├── import_tripadvisor.py  # Load scraped data into MongoDB
│   │   ├── mongo_to_hdfs.py    # Export MongoDB → HDFS (.jsonl)
│   │   ├── mysql_to_hdfs.py    # Export MySQL → HDFS (.jsonl)
│   │   ├── hive_schema.sql     # Hive external table definitions
│   │   └── hive_analytics.sql  # Hive analytics views (7 views)
│   ├── mapreduce/              # 8 MapReduce jobs (Python mrjob)
│   │   ├── mr_rating_by_district.py
│   │   ├── mr_cuisine_count.py
│   │   ├── mr_rating_bucket.py
│   │   ├── mr_sentiment_analysis.py
│   │   ├── mr_ingredient_match.py
│   │   ├── mr_top_reviewed.py
│   │   ├── mr_review_distribution.py
│   │   ├── mr_delivery_analysis.py
│   │   ├── run_all_jobs.py         # Run all 8 jobs with summary output
│   │   ├── test_local.py           # Local mode test (no Hadoop needed)
│   │   ├── test_hive_connection.py # HiveServer2 smoke test
│   │   └── test_district_parsing.py # District normalization unit test
│   ├── streamlit_app/          # Web dashboard
│   │   ├── app.py              # Main Streamlit app (CRUD + Reports + DevOps)
│   │   └── hive_connector.py   # Hive query module (pyhive → CLI → offline fallback)
│   └── backup/                 # Backup & restore scripts
│       ├── db_backup.sh        # Backup MySQL + MongoDB
│       └── db_restore.sh       # Restore from backup
│
├── data/                       # Local data (gitignored)
│   └── backups/                # db_backup.sh output
│
├── docs/                       # Documentation
│   ├── ARCHITECTURE.md
│   ├── MASTERPLAN.md
│   ├── REQUIREMENTS.md
│   ├── TROUBLESHOOTING.md
│   ├── rules.md                # Team working rules
│   └── process/                # Execution logs & debug notes
│
├── requirements.txt
├── GEMINI.md                   # AI agent rules & schema reference
├── SETUP_GUIDE.md
└── TEST_PLAN.md
```

---

## 5. Hướng dẫn khởi chạy nhanh (Quick Start)

### Yêu cầu
- Windows 10/11 với WSL2 cài **Ubuntu 24.04 LTS**
- RAM tối thiểu 8 GB, ổ cứng còn trống 10 GB+
- Kết nối internet (để tải Hadoop, Hive lần đầu)

### Bước 1: Clone repo & cấp quyền thực thi

```bash
# Trong Ubuntu WSL2 terminal
cd /mnt/d/Project   # hoặc thư mục bạn muốn
git clone <repo-url> final-bdes
cd final-bdes
chmod +x bin/*.sh src/backup/*.sh
```

### Bước 2: Cài đặt hạ tầng (chỉ chạy 1 lần trên máy mới)

```bash
./bin/install_infra.sh
```

Script này tự động:
- Kiểm tra và cài Java 8, Hadoop 3.3.6, Hive 3.1.3, MongoDB 8.0, MySQL 8.0
- Copy XML config từ `conf/` vào các thư mục cài đặt
- Tạo Python `venv` và cài dependencies từ `requirements.txt`
- Khởi tạo MySQL schema và load dữ liệu mẫu (seed data)

### Bước 3: Khởi chạy pipeline

```bash
# Chạy với data đã có (không cào lại):
./bin/run.sh

# Cào dữ liệu mới → ingest → Streamlit:
./bin/run.sh --crawl

# Cào + chạy 8 MapReduce jobs + Streamlit:
./bin/run.sh --crawl --jobs
```

Mở trình duyệt Windows tại: **http://localhost:8501**

### Bước 4: Dừng dịch vụ

```bash
./bin/stop.sh                   # Dừng tất cả
./bin/stop.sh --backup          # Backup trước khi dừng
./bin/stop.sh --cleandata       # Wipe data (demo reset)
```

---

## 6. MapReduce Jobs (8 jobs)

| Job | Input | Mô tả |
|-----|-------|-------|
| `mr_rating_by_district.py` | restaurants.jsonl | Rating trung bình theo quận (extract từ địa chỉ) |
| `mr_cuisine_count.py` | meals.jsonl | Tần suất danh mục & vùng ẩm thực (TheMealDB) |
| `mr_rating_bucket.py` | restaurants.jsonl | Phân nhóm nhà hàng theo rating (1-2 / 2-3 / 3-4 / 4-5 sao) |
| `mr_sentiment_analysis.py` | restaurants.jsonl | Sentiment score từ review comments |
| `mr_ingredient_match.py` | restaurants.jsonl | Nguyên liệu được đề cập trong review (kết nối TheMealDB) |
| `mr_top_reviewed.py` | restaurants.jsonl | Top 10 nhà hàng được review nhiều nhất |
| `mr_review_distribution.py` | restaurants.jsonl | Phân phối sao đánh giá (1→5 sao) |
| `mr_delivery_analysis.py` | restaurants.jsonl | So sánh rating: đề cập delivery vs dine-in |

---

## 7. Hive Analytics Views (7 views)

| View | Mô tả |
|------|-------|
| `view_rating_by_district` | Avg rating + số nhà hàng theo quận (dùng `district_parsed`) |
| `view_cuisine_frequency` | Phân bố danh mục ẩm thực từ TheMealDB |
| `view_cuisine_area` | Phân bố vùng ẩm thực từ TheMealDB |
| `view_top_districts` | Top quận theo số lượng nhà hàng |
| `view_rating_histogram` | Phân bố nhà hàng theo nhóm rating |
| `view_review_distribution` | Phân phối sao trong reviews |
| `view_delivery_sentiment` | Delivery-mentioned vs dine-in avg rating |

---

## 8. Troubleshooting nhanh

| Lỗi | Giải pháp |
|-----|-----------|
| Java không phải 1.8 | `sudo update-alternatives --config java` → chọn Java 8 |
| Hive `NoSuchFieldException: parentOffset` | Kiểm tra JAVA_HOME trỏ đúng Java 8 |
| MySQL `Access denied` | Chạy lại `./bin/install_infra.sh` để reset password |
| HDFS NameNode không start | `hdfs namenode -format -force` rồi start lại |
| Streamlit import error | `source venv/bin/activate` rồi `pip install -r requirements.txt` |

Xem chi tiết: [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md)