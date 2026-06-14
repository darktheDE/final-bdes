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
