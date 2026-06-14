# Refactor Log — Food & Restaurant Sentiment Analysis System

## Module 1: Schema & Data Normalization

**Ngày thực hiện**: 2026-06-14
**Mục tiêu**: Align schema với data thực tế đã cào được từ TripAdvisor và TheMealDB.

---

### Vấn đề phát hiện

| Vấn đề | File bị ảnh hưởng | Mô tả |
|--------|------------------|-------|
| `price_range` không tồn tại | init_db.py, hive_schema.sql, hive_analytics.sql, app.py | TripAdvisor không trả về field này |
| `review_count` là string `"(112)"` | init_db.py, mr_top_reviewed.py | Cần parse số từ chuỗi |
| `district` là chuỗi địa chỉ đầy đủ | init_db.py, mr_rating_by_district.py | Cần extract tên quận |
| `city` có zip code `"Ho Chi Minh City 70000 Vietnam"` | init_db.py | Cần normalize |
| review `rating` là `"5 of 5 bubbles"` | init_db.py, mr_review_distribution.py | Cần parse sang float |
| MySQL password mismatch | app.py dùng `"root"`, install_infra.sh tạo `""` | Fix password |

---

### Thay đổi thực hiện

#### `src/ingest/init_db.py`
- **Thêm hàm** `_parse_review_count(value)` → parse `"(112)"` → `112`
- **Thêm hàm** `_extract_district(address_str)` → regex extract `"Quận 1"` từ chuỗi địa chỉ
- **Thêm hàm** `_normalize_city(city_str)` → strip zip code và `"Vietnam"` suffix
- **Thêm hàm** `_parse_review_rating(rating_val)` → parse `"5 of 5 bubbles"` → `5.0`
- **Thêm hàm** `_make_short_id(raw_id)` → extract `rest_dXXXXXXXX` từ URL
- **Xóa** `price_range` khỏi `CREATE TABLE restaurants`
- **Thêm** `district_parsed VARCHAR(100)` vào `CREATE TABLE restaurants`
- **Thêm** `_alter_tables_if_needed()` để handle backward compat khi table đã tồn tại
- **Fix** MySQL password từ `"root"` → `""` (empty string, khớp với install_infra.sh)
- **Thêm** sample output sau migrate để verify district parsing

#### `src/ingest/hive_schema.sql`
- **Xóa** `price_range` khỏi `mysql_restaurants` external table
- **Thêm** `district_parsed STRING` vào `mysql_restaurants`
- **Cập nhật** `mongodb_restaurants.reviews` → `rating` type là FLOAT (đã parsed bởi init_db.py)
- **Thêm** `DROP TABLE IF EXISTS` trước mỗi `CREATE` để idempotent
- **Thêm** `STORED AS TEXTFILE` explicit

#### `src/ingest/hive_analytics.sql`
- **Xóa** `view_price_segment` (dùng `price_range` — không có trong data)
- **Xóa** `view_sentiment_by_price` (dùng `price_range` — không có trong data)
- **Thêm** `view_rating_histogram` — phân nhóm nhà hàng theo rating: 1-2 / 2-3 / 3-4 / 4-4.5 / 4.5-5 sao
- **Thêm** `view_top_districts` — top quận theo số lượng nhà hàng
- **Cập nhật** `view_rating_by_district` → dùng `district_parsed` thay vì `district`
- **Thêm** `view_cuisine_area` — phân bố vùng ẩm thực từ TheMealDB
- **Mở rộng** `view_delivery_sentiment` keywords: thêm `shopeefood`, `grab food`
- **Tổng views**: 7 (tăng từ 6)

#### `GEMINI.md`
- **Cập nhật** Data Schema Reference với data thực tế
- **Cập nhật** Project Structure (thêm `conf/`, `bin/stop.sh`, xóa `bin/setup.sh`)
- **Thêm** bảng 8 MapReduce jobs
- **Ghi rõ** mối liên hệ TripAdvisor ↔ TheMealDB

---

### Troubleshooting & Hotfixes
- **Sự cố MySQL `ON DUPLICATE KEY UPDATE`**: Khi thêm cột mới (`district_parsed`) vào bảng đã có dữ liệu, các record bị dính giá trị `Unknown` cũ và lệnh migration không đè được do behavior của `VALUES()` trong MySQL 8.0.
- **Giải pháp**: Phải `TRUNCATE TABLE restaurants` (và tắt check khóa ngoại) để ép script chạy lệnh `INSERT` mới hoàn toàn.

---

### Verification Checklist

Chạy các lệnh sau để verify Module 1 (trong WSL2 với venv đã activate):

```bash
# 1. Test các hàm normalize (không cần MySQL)
python3 -c "
import sys; sys.path.insert(0, '.')
from src.ingest.init_db import _parse_review_count, _extract_district, _normalize_city, _parse_review_rating, _make_short_id

# Test parse review count
assert _parse_review_count('(112)') == 112, 'FAIL: parse_review_count'
assert _parse_review_count('1,234') == 1234, 'FAIL: parse_review_count comma'
assert _parse_review_count(128) == 128, 'FAIL: parse_review_count int'
assert _parse_review_count(None) == 0, 'FAIL: parse_review_count None'

# Test extract district
assert _extract_district('18B/17 Đ. Nguyễn Thị Minh Khai Quận 1') == 'Quận 1', 'FAIL: extract_district'
assert _extract_district('') == 'Unknown', 'FAIL: extract_district empty'

# Test normalize city
assert _normalize_city('Ho Chi Minh City 70000 Vietnam') == 'Ho Chi Minh City', 'FAIL: normalize_city'
assert _normalize_city(None) == 'Unknown', 'FAIL: normalize_city None'

# Test parse review rating
assert _parse_review_rating('5 of 5 bubbles') == 5.0, 'FAIL: parse_review_rating'
assert _parse_review_rating('4 of 5 bubbles') == 4.0, 'FAIL: parse_review_rating 4'
assert _parse_review_rating(None) is None, 'FAIL: parse_review_rating None'

# Test make short id
result = _make_short_id('https://www.tripadvisor.com/Restaurant_Review-g293925-d33215720-Reviews-...')
assert result == 'rest_d33215720', f'FAIL: make_short_id got {result}'

print('[PASS] All normalize function tests passed!')
"

# 2. Full migration test (cần MySQL + MongoDB running)
python src/ingest/init_db.py

# 3. Verify schema in MySQL
mysql -h 127.0.0.1 -u root food_sentiment_db -e "DESCRIBE restaurants;"
mysql -h 127.0.0.1 -u root food_sentiment_db -e "SELECT COUNT(*) FROM restaurants;"
mysql -h 127.0.0.1 -u root food_sentiment_db -e "SELECT name, district_parsed, city FROM restaurants LIMIT 5;"
```

**Pass criteria**:
- `[ ]` Tất cả assert test pass
- `[ ]` Bảng `restaurants` không có cột `price_range`
- `[ ]` Bảng `restaurants` có cột `district_parsed`
- `[ ]` `district_parsed` cho các restaurant HCMC hiển thị tên quận đúng (VD: `Quận 1`)
- `[ ]` `city` là `Ho Chi Minh City` (không có số zip)
- `[ ]` `review_count` là số nguyên

---

## Module 2: MapReduce Jobs Alignment

**Ngày thực hiện**: 2026-06-14
**Mục tiêu**: Refactor các MapReduce jobs để phản ánh đúng schema thực tế và in ra báo cáo thống kê tốt hơn.

### Các thay đổi
- **`mr_rating_by_district.py`**: Áp dụng regex `_extract_district` để gom nhóm các nhà hàng theo quận chuẩn thay vì chuỗi địa chỉ đầy đủ.
- **`mr_review_distribution.py`**: Rời rạc hóa rating thành các nhóm chuỗi (VD: "5 Stars", "4 Stars") thay vì float.
- **`mr_rating_bucket.py`**: Xóa bỏ `mr_price_segment.py` không còn ý nghĩa, thay bằng bucket phân nhóm rating 1-2, 3, 4-5 sao.
- **`run_all_jobs.py`**: Cập nhật danh sách job, chỉ định `--conf-path conf/mrjob.conf`, và bổ sung hàm `print_summary` để in trực tiếp top 10 results từ HDFS ra console.

### Kiểm thử cục bộ (Local Testing)
- Cập nhật file `test_local.py` để test `mr_rating_bucket.py` thay cho job bị xóa.
- Cài đặt `mrjob` và chạy thành công trên Windows qua Python môi trường cục bộ. Toàn bộ 8 jobs đều trả về kết quả hợp lệ, xử lý sạch các field lỗi.

---

## Module 3: Ingest Pipeline Fix

**Ngày thực hiện**: 2026-06-14
**Mục tiêu**: Đảm bảo pipeline ingest data từ nguồn → MongoDB → MySQL → HDFS hoạt động đúng với schema mới.

### Các thay đổi
- **`import_tripadvisor.py`**: 
  - Import và tái sử dụng các hàm chuẩn hóa (`_parse_review_count`, `_extract_district`, `_normalize_city`, v.v.) từ `init_db.py`.
  - Cập nhật logic để định dạng lại các field trước khi đưa vào MongoDB.
  - Sử dụng `_make_short_id` để de-duplicate dữ liệu dựa trên URL của nhà hàng.
- **`mongo_to_hdfs.py`**:
  - Thêm logic in ra sample fields cho record đầu tiên (bao gồm việc kiểm tra `district_parsed` và sự vắng mặt của `price_range`).
  - Cải thiện log hiển thị trong lúc export sang HDFS.
- **`mysql_to_hdfs.py`**:
  - Thay vì dùng `SELECT * FROM restaurants`, chỉ định rõ các cột cần xuất (`id, name, rating, review_count, address, district, district_parsed, city`) để tránh trường hợp `price_range` vẫn còn tồn tại từ schema cũ.

---

## Module 4: Streamlit UI Refactor

**Ngày thực hiện**: 2026-06-14
**Mục tiêu**: Nâng cấp và sửa lỗi giao diện dashboard Streamlit để phản ánh đúng schema mới, an toàn hơn và loại bỏ mockup data giả.

### Các thay đổi
- **`app.py`**:
  - **Data Management (CRUD)**: Bổ sung thanh tìm kiếm (theo ID, name, district) và phân trang. Xoá trường `price_range` khỏi các biểu mẫu thêm/sửa. Bổ sung nút **"Sync từ MongoDB"** dùng `subprocess` chạy `init_db.py` để incremental load data trực tiếp từ web.
  - **Big Data Reports**: Thay đổi các chart cũ dựa trên `price_range` thành các biểu đồ mới (`view_rating_histogram`, `view_top_districts`). Xoá toàn bộ các hàm fallback tạo mockup data, thay vào đó hiển thị dữ liệu rỗng (`pd.DataFrame()`) nếu chế độ `offline` để tránh gây hiểu lầm số liệu.
  - **DevOps & Jobs Execution**: Bọc lệnh gọi `db_backup.sh` vào `try/except` kết hợp `subprocess.run` để không gây sập (crash) ứng dụng Streamlit; Cập nhật danh sách MapReduce jobs (thay `mr_price_segment.py` bằng `mr_rating_bucket.py`) và sửa đường dẫn cấu hình `mrjob.conf` trỏ đúng vào thư mục `conf/`.
  - **Database Connection**: Thêm cơ chế dự phòng mật khẩu (fallback) cho `mysql.connector`. Hệ thống sẽ thử kết nối với mật khẩu `""` trước, nếu thất bại do `Access denied` sẽ thử tiếp với mật khẩu `"root"` (giúp tương thích ngược khi user chưa chạy `install_infra.sh` mới).
- **`hive_connector.py`**:
  - Gỡ bỏ hằng số dictionary `_MOCK_DATA` cùng với hàm `_get_mock()`. Mọi xử lý offline hoặc lỗi timeout từ Hive sẽ đều trả về dictionary chứa DataFrame rỗng thay vì dữ liệu cứng.
- **`init_db.py` (Hotfixes)**:
  - Đồng bộ cơ chế dự phòng mật khẩu kết nối cơ sở dữ liệu (`""` -> `"root"`) giống như `app.py`.
  - Nâng cấp regex trong hàm `_extract_district` nhằm trích xuất chính xác tên Quận ở nhiều định dạng đa dạng (tiền tố tiếng Việt, hậu tố tiếng Anh, v.v.).

---

## Module 5: Bin Scripts Refactor

**Ngày thực hiện**: 2026-06-14
**Mục tiêu**: Hợp lý hóa 3 scripts bin/, tách XML config ra folder riêng, thêm stop.sh, bổ sung flags cho run.sh.

### Vấn đề phát hiện

| Vấn đề | File bị ảnh hưởng | Mô tả |
|--------|------------------|-------|
| XML config inline trong .sh | install_infra.sh | Khó maintain, không tái sử dụng được |
| setup.sh cài JDK 11 | setup.sh | Sai version, overlap với install_infra.sh |
| run.sh luôn crawl | run.sh | Tốn 10-15 phút mỗi lần start, không có flag |
| Refer đến setup.sh | run.sh (dòng 73) | Hướng dẫn sai khi venv không tồn tại |
| Không có stop.sh | — | Người dùng phải kill process thủ công |
| db_backup.sh dùng set -e | db_backup.sh | Script crash nếu MySQL hoặc Mongo down |

### Các thay đổi thực hiện

#### `conf/hadoop/` (files mới)
- **Tạo** `core-site.xml` — HDFS defaultFS `hdfs://localhost:9000`
- **Tạo** `hdfs-site.xml` — `dfs.replication=1`
- **Tạo** `yarn-site.xml` — mapreduce_shuffle, disable vmem-check (bắt buộc cho WSL2)
- **Tạo** `mapred-site.xml` — framework=yarn, classpath

#### `conf/hive/hive-site.xml` (file mới)
- **Tạo** `hive-site.xml` — MySQL metastore (user=hive/hive), warehouse dir, thêm `hive.stats.autogather=false` để tránh lỗi Kryo

#### `bin/install_infra.sh` (refactor hoàn toàn)
- **Thêm** version-check trước khi cài: Java 8, Hadoop 3.3.6, Hive 3.1.3, MongoDB, MySQL
- **Thay** inline XML heredoc → `cp "${BASE_DIR}/conf/hadoop/*.xml"` và `cp "${BASE_DIR}/conf/hive/hive-site.xml"`
- **Gộp** Python venv setup từ setup.sh: cài python3-venv, tạo venv, cài requirements.txt
- **Thêm** `init_db.py` call ở cuối để khởi tạo schema và seed data
- **Thêm** idempotent guards: SSH key chỉ thêm nếu chưa có, NameNode format chỉ chạy lần đầu
- **Fix** `.bashrc` append: dùng `>>` thay vì overwrite, có guard để không duplicate

#### `bin/run.sh` (refactor)
- **Thêm** flag `--crawl`: chỉ chạy scraper + `init_db.py` + HDFS sync khi có flag này
- **Thêm** flag `--jobs`: chỉ chạy `run_all_jobs.py` khi có flag này
- **Thêm** flag `--help`: in hướng dẫn sử dụng
- **Thêm** version-check Java 8 và Hadoop 3.3.6 — exit nếu sai, yêu cầu chạy install_infra.sh
- **Fix** refer đến setup.sh → thay bằng install_infra.sh
- **Thêm** port summary rõ ràng sau khi start services
- **Cải thiện** service start: dùng check_port() để skip nếu đã running

#### `bin/stop.sh` (tạo mới)
- **Tạo** script dừng toàn bộ theo thứ tự: Streamlit → YARN → HDFS → MongoDB → MySQL
- **Thêm** flag `--backup`: chạy db_backup.sh trước khi stop
- **Thêm** flag `--cleandata`: xóa MySQL food_sentiment_db, MongoDB sentiment_db, HDFS /data/raw
- **Không dùng** `set -e` — từng bước tự xử lý lỗi, không crash khi service đã down

#### `src/backup/db_backup.sh` (fix)
- **Xóa** `set -e`
- **Thêm** kiểm tra return code của `mysqldump` và `mongodump` riêng biệt
- **Thêm** biến `BACKUP_SUCCESS=true` — báo cáo partial failure thay vì crash hoàn toàn
- **Thêm** hiển thị kích thước file backup sau khi hoàn thành

---

## Module 6: Docs & File Cleanup

**Ngày thực hiện**: 2026-06-14
**Mục tiêu**: Di chuyển file stray, cập nhật README, dọn dẹp cấu trúc.

### Các thay đổi thực hiện

#### File stray di chuyển từ root
| File cũ | File mới | Ghi chú |
|---------|----------|---------|
| `rules.md` (root) | `docs/rules.md` | Quy tắc làm việc nhóm |
| `test_hive.py` (root) | `src/mapreduce/test_hive_connection.py` | Đổi tên rõ ràng hơn, thêm docstring |
| `test_district.py` (root) | `src/mapreduce/test_district_parsing.py` | Fix sys.path để chạy từ bất kỳ thư mục nào |

#### Files cần xóa thủ công (user tự xóa)
- `rules.md` (root)
- `test_hive.py` (root)
- `test_district.py` (root)
- `refactor.md` (root)
- `final-refactor.md` (root)
- `bin/setup.sh`
- `tmp-pandas/` (thư mục)

#### `README.md` (rewrite hoàn toàn)
- **Cập nhật** quick start: bỏ setup.sh, flow mới `install_infra.sh` → `run.sh [--crawl] [--jobs]` → `stop.sh [--backup] [--cleandata]`
- **Thêm** bảng Tech Stack & Version
- **Cập nhật** cấu trúc thư mục đúng với thực tế hiện tại (có `conf/hadoop/`, `conf/hive/`, bỏ `setup.sh`)
- **Thêm** bảng 8 MapReduce jobs
- **Thêm** bảng 7 Hive analytics views
- **Ghi rõ** mối liên hệ TripAdvisor ↔ TheMealDB (qua `mr_ingredient_match.py`)
- **Thêm** bảng Troubleshooting nhanh

#### `.gitignore`
- Đã đầy đủ (`venv/`, `tmp-pandas/`, `data/backups/`, etc.) — không cần thay đổi
