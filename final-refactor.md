# Kế hoạch Refactor — Food & Restaurant Sentiment Analysis System

## Bối cảnh & Vấn đề

Dự án đã hoàn thiện vòng phát triển nhưng có nhiều điểm không khớp giữa **dữ liệu thực tế đã cào được** với **schema / MapReduce jobs / UI đã thiết kế sẵn trước đó**. Cần refactor theo đúng thứ tự pipeline dữ liệu.

---

## Phân tích vấn đề hiện tại

### 1. Schema lệch so với data thực tế

**TripAdvisor thực tế cào được:**
```json
{
  "_id": "https://www.tripadvisor.com/Restaurant_Review-...",
  "name": "Bún Chả Hà Thành by Hanoi Corner",
  "rating": 5.0,
  "review_count": "(112)",          ← chuỗi "(112)", không phải int
  "address": "18B/17 Đ. Nguyễn Thị Minh Khai...",
  "district": "18B/17 Đ. Nguyễn Thị Minh Khai Quận 1",  ← là địa chỉ đường, không phải quận
  "city": "Ho Chi Minh City 70000 Vietnam",  ← có số zip code
  "reviews": [{"user": "...", "rating": "5 of 5 bubbles", "comment": "..."}]
  // KHÔNG có field price_range
}
```

**Vấn đề:**
- `review_count` là string `"(112)"`, không phải int → cần parse
- `district` thực ra là chuỗi địa chỉ đường + quận → cần extract quận riêng
- `city` có số zip → cần normalize
- Review `rating` là `"5 of 5 bubbles"` → cần parse thành float
- **Không có `price_range`** → field này vô nghĩa với data TripAdvisor

**Meals data (TheMealDB):**
```json
{
  "_id": "meal_53262", "name": "Adana kebab",
  "category": "Lamb", "area": "Turkish",
  "instructions": "...", "ingredients": ["Romano Pepper", ...]
}
```
- Data meals chuẩn, đầy đủ field

### 2. Liên quan giữa TripAdvisor và TheMealDB

Hiện tại chưa có kết nối rõ ràng. Đề xuất làm rõ:
- **TripAdvisor**: dữ liệu nhà hàng HCMC (restaurant, review, rating)
- **TheMealDB**: dữ liệu công thức nấu ăn quốc tế (category, area, ingredients)
- **Điểm kết nối**: `mr_ingredient_match.py` — dùng danh sách ingredients từ MealDB để match trong comment review TripAdvisor → tìm ra nguyên liệu nào được đề cập nhiều nhất trong review nhà hàng HCMC

### 3. MapReduce jobs bị sai / vô nghĩa với data thực tế

| Job | Vấn đề |
|-----|--------|
| `mr_price_segment.py` | Field `price_range` không tồn tại trong data TripAdvisor |
| `mr_rating_by_district.py` | `district` là full address string, không phải tên quận |
| `mr_review_distribution.py` | `rating` trong review là `"5 of 5 bubbles"`, cần parse |
| `mr_top_reviewed.py` | `review_count` là `"(112)"`, cần parse |
| `mr_delivery_analysis.py` | Logic hợp lý, nhưng `rating` level restaurant dùng được |
| `mr_sentiment_analysis.py` | Logic hợp lý với comment data |
| `mr_ingredient_match.py` | Logic hợp lý, input đúng data |
| `mr_cuisine_count.py` | Chạy trên Meals data — OK |

### 4. Streamlit UI

- `app.py` dùng password MySQL `"root"` nhưng `install_infra.sh` set password là `""` → connection lỗi
- Charts 4 & 5 (`price_range`) sẽ toàn là "Unknown" vì không có field đó
- Backup logic: folder tạo với ký tự lỗi khi chạy lần 2 (do `set -e` crash)
- Không có phân trang trong View Records
- Search chỉ có Name/District, thiếu search by ID
- Update chỉ update rating, thiếu các field khác
- Không có incremental load indicator

### 5. Scripts bin/

- `setup.sh` cài JDK-11 nhưng dự án yêu cầu JDK-8
- `setup.sh` và `install_infra.sh` có vai trò trùng lặp
- `run.sh` luôn chạy crawling khi khởi động → tốn thời gian, cần flag `-data`
- Thiếu `stop.sh`
- Config XML files viết inline trong `.sh` → cần tách ra folder riêng

### 6. Cấu trúc file

- `mrjob.conf`, `test_hive.py`, `rules.md` đang nằm ở root, cần sắp xếp
- `tmp-pandas/` không cần thiết

---

## Open Questions

> [!IMPORTANT]
> **Q1**: Field `district` thực tế là chuỗi địa chỉ (VD: `"18B/17 Đ. Nguyễn Thị Minh Khai Quận 1"`). Có muốn dùng regex extract tên quận (VD: `"Quận 1"`) không, hay giữ nguyên chuỗi và chấp nhận kết quả groupby sẽ ít ý nghĩa?

> [!IMPORTANT]
> **Q2**: `mr_price_segment.py` hoàn toàn vô nghĩa với TripAdvisor data. Có muốn **xóa job này** và thay bằng job khác có ý nghĩa hơn (VD: `mr_top_districts.py` — top quận có nhiều nhà hàng nhất, hoặc `mr_rating_bucket.py` — phân nhóm nhà hàng theo rating 1-2 / 3 / 4-5)?

> [!IMPORTANT]
> **Q3**: Có muốn tôi truy cập WSL2 để lấy nội dung các config file hiện tại (Hadoop XML, Hive site...) trước khi refactor `install_infra.sh` không? Điều này đảm bảo config đúng với môi trường đã test.

> [!NOTE]
> **Q4**: `setup.sh` — đồng ý gộp vào `install_infra.sh` không? Sau khi gộp, flow sẽ là: `install_infra.sh` → `run.sh`. Người dùng không cần chạy `setup.sh` nữa.

---

## Các Module Refactor (Thứ tự triển khai)

```
Module 1 → Module 2 → Module 3 → Module 4 → Module 5 → Module 6
 Schema      MapReduce   Ingest     Streamlit   Bin/       Docs &
  Fix         Jobs        Fix        CRUD/UI    Scripts    Cleanup
```

---

## Module 1 — Schema & Data Normalization

**Mục tiêu**: Đảm bảo schema MySQL + Hive phản ánh đúng data thực tế.

> [!WARNING]
> Đây là module nền tảng — các module sau đều phụ thuộc vào đây. Phải test thành công trước khi tiếp tục.

### [MODIFY] [init_db.py](file:///d:/Project/final-bdes/src/ingest/init_db.py)
- Xóa field `price_range` khỏi bảng `restaurants`
- Thêm hàm `_parse_review_count(s)` → parse `"(112)"` thành `112`
- Thêm hàm `_extract_district(address_str)` → regex extract `"Quận X"` / `"Huyện Y"` từ địa chỉ
- Thêm hàm `_normalize_city(city_str)` → strip zip code, chuẩn hóa tên thành phố
- Thêm hàm `_parse_review_rating(rating_str)` → parse `"5 of 5 bubbles"` thành `5.0`
- Thêm hàm `_parse_restaurant_id(url_str)` → tạo short ID từ URL (hoặc dùng URL hash ngắn)
- Cập nhật MySQL connection password khớp với `install_infra.sh` (`""` → empty)

### [MODIFY] [hive_schema.sql](file:///d:/Project/final-bdes/src/ingest/hive_schema.sql)
- Bỏ field `price_range` trong `mysql_restaurants` external table
- Thêm field `district_parsed` (sau khi extract quận)
- Cập nhật schema `mongodb_restaurants` cho đúng với data thực (review rating là STRING)

### [MODIFY] [hive_analytics.sql](file:///d:/Project/final-bdes/src/ingest/hive_analytics.sql)
- Xóa `view_price_segment` và `view_sentiment_by_price` (dựa vào `price_range`)
- Thêm views mới thay thế:
  - `view_top_districts` — Top quận theo số lượng nhà hàng
  - `view_rating_histogram` — Phân bố nhà hàng theo nhóm rating (1-2 sao / 3 sao / 4-5 sao)
  - Giữ nguyên: `view_rating_by_district`, `view_cuisine_frequency`, `view_review_distribution`, `view_delivery_sentiment`

### [MODIFY] [GEMINI.md](file:///d:/Project/final-bdes/GEMINI.md)
- Cập nhật Data Schema Reference: xóa `price_range`, cập nhật kiểu dữ liệu thực tế

**Manual test**: Chạy `python src/ingest/init_db.py` → verify bảng tạo đúng, data migrate đúng quận, đúng rating.

---

## Module 2 — MapReduce Jobs Alignment

**Mục tiêu**: Đảm bảo tất cả 8 jobs chạy được và cho kết quả có ý nghĩa với data thực tế.

### Jobs cần sửa:

#### [MODIFY] [mr_rating_by_district.py](file:///d:/Project/final-bdes/src/mapreduce/mr_rating_by_district.py)
- Thêm hàm `_extract_district(district_str)` để parse tên quận đúng từ field `district` thực tế

#### [MODIFY] [mr_review_distribution.py](file:///d:/Project/final-bdes/src/mapreduce/mr_review_distribution.py)
- Đã có xử lý `"5 of 5 bubbles"` → giữ nguyên, nhưng thêm bucket hóa thay vì float key (1.0→1, 2.0→2...)

#### [MODIFY] [mr_top_reviewed.py](file:///d:/Project/final-bdes/src/mapreduce/mr_top_reviewed.py)
- Đã có parse `"(112)"` → giữ nguyên, kiểm tra edge cases

#### [DELETE / REPLACE] [mr_price_segment.py](file:///d:/Project/final-bdes/src/mapreduce/mr_price_segment.py)
- **Thay thế** bằng `mr_rating_bucket.py` — phân loại nhà hàng theo nhóm rating

### Jobs cần bổ sung plot output:

**Tất cả 8 jobs** cần được cập nhật `run_all_jobs.py` để sau khi chạy xong, in ra:
- Tổng số records processed
- Top 5/10 kết quả
- Summary statistics (min/max/avg nếu áp dụng)

#### [MODIFY] [run_all_jobs.py](file:///d:/Project/final-bdes/src/mapreduce/run_all_jobs.py)
- Thêm hàm `print_summary(job_name, results)` → format kết quả đẹp sau mỗi job

### [NEW] conf/mrjob.conf
- Di chuyển `mrjob.conf` từ root vào folder `conf/`

**Manual test**: Chạy từng job với local mode: `python src/mapreduce/mr_xxx.py src/crawler/seed/XXX.json`

---

## Module 3 — Ingest Pipeline Fix

**Mục tiêu**: Đảm bảo pipeline ingest data từ nguồn → MongoDB → MySQL → HDFS hoạt động đúng.

### [MODIFY] [mongo_to_hdfs.py](file:///d:/Project/final-bdes/src/ingest/mongo_to_hdfs.py)
- Verify data sau normalize đúng format trước khi export
- Thêm logging số records exported

### [MODIFY] [mysql_to_hdfs.py](file:///d:/Project/final-bdes/src/ingest/mysql_to_hdfs.py)
- Bỏ export field `price_range` (hoặc set `NULL`)

### [MODIFY] [import_tripadvisor.py](file:///d:/Project/final-bdes/src/ingest/import_tripadvisor.py)
- Áp dụng các hàm normalize từ Module 1
- Thêm de-duplicate logic theo URL

**Manual test**: Chạy pipeline `mongo_to_hdfs.py` → `mysql_to_hdfs.py` → verify HDFS files.

---

## Module 4 — Streamlit UI Refactor

**Mục tiêu**: Cải thiện CRUD, bổ sung tính năng, fix bug backup, cập nhật charts.

### [MODIFY] [app.py](file:///d:/Project/final-bdes/src/streamlit_app/app.py)

**CRUD Page:**
- **View Records**: Bổ sung search by ID; thêm phân trang (10/20/50 records per page bằng `st.slider` hoặc `LIMIT/OFFSET`)
- **Update Record**: Cho phép update thêm fields (name, address, district, city) bên cạnh rating
- **Insert**: Bỏ field `price_range` khỏi form insert
- **Incremental Load**: Thêm button "Sync từ MongoDB" → trigger `init_db.py` migration

**Reports Page:**
- Thay Chart 4 (`view_sentiment_by_price`) bằng chart `view_top_districts`
- Thay Chart 5 (`view_price_segment`) bằng chart `view_rating_histogram`
- Giữ nguyên Charts 1, 2, 3, 6

**DevOps Page:**
- Fix backup button: Wrap trong `try/except` không dùng `set -e`, thêm kiểm tra success/failure rõ ràng

**Connection fix:**
- Đổi `password="root"` → `password=""` trong `get_db_connection()`

### [MODIFY] [hive_connector.py](file:///d:/Project/final-bdes/src/streamlit_app/hive_connector.py)
- Cập nhật `batch_query_all_views()` để query các views mới

**Manual test**: Khởi động Streamlit `streamlit run src/streamlit_app/app.py` → test từng tab.

---

## Module 5 — Bin Scripts Refactor

**Mục tiêu**: Hợp lý hóa flow 3 scripts, thêm `stop.sh`, bổ sung tham số.

### [MODIFY] [install_infra.sh](file:///d:/Project/final-bdes/bin/install_infra.sh)

**Bổ sung kiểm tra version trước khi cài:**
```bash
# Kiểm tra Java
if java -version 2>&1 | grep -q "1.8"; then
    echo "[+] Java 8 already installed."
else
    # Cài mới hoặc switch về Java 8
fi
```

**Tách XML config ra folder riêng:**
- Tạo `conf/hadoop/` chứa `core-site.xml`, `hdfs-site.xml`, `yarn-site.xml`, `mapred-site.xml`
- Tạo `conf/hive/hive-site.xml`
- `install_infra.sh` copy từ `conf/` vào đúng thư mục install

**Gộp Python venv setup từ setup.sh:**
- Di chuyển toàn bộ logic Python venv + `requirements.txt` install vào `install_infra.sh`
- Kiểm tra phiên bản Hadoop/Hive/MongoDB/MySQL trước khi cài lại

### [DELETE] [setup.sh](file:///d:/Project/final-bdes/bin/setup.sh)
- Gộp vào `install_infra.sh` → xóa file này

### [MODIFY] [run.sh](file:///d:/Project/final-bdes/bin/run.sh)
- Thêm kiểm tra version (Java 8, Hadoop 3.3.6, Hive 3.1.3) → nếu sai thì báo chạy `install_infra.sh`
- Thêm flag `-data` hoặc `--crawl`:
  ```bash
  if [[ "$*" == *"--crawl"* ]]; then
      # Run scraper + ingest
  else
      echo "[*] Skipping data collection (use --crawl to fetch fresh data)"
  fi
  ```
- Thêm flag `--jobs` để chạy toàn bộ MapReduce jobs sau khi có data

### [NEW] [stop.sh](file:///d:/Project/final-bdes/bin/stop.sh)
- Stop Streamlit process
- Stop HDFS và YARN
- Stop MongoDB
- Stop MySQL
- Tham số `--backup`: chạy `src/backup/db_backup.sh` trước khi stop
- Tham số `--cleandata`: xóa toàn bộ data trong MongoDB, MySQL, HDFS (dùng cho demo)

### [NEW] conf/hadoop/core-site.xml
### [NEW] conf/hadoop/hdfs-site.xml
### [NEW] conf/hadoop/yarn-site.xml
### [NEW] conf/hadoop/mapred-site.xml
### [NEW] conf/hive/hive-site.xml
- Tách toàn bộ XML config ra đây từ `install_infra.sh`

**Manual test**: Chạy `./bin/run.sh` (không `--crawl`) → verify services start, Streamlit mở được.

---

## Module 6 — Docs & Cấu trúc File

**Mục tiêu**: Cập nhật docs sai, sắp xếp file stray, plan cleanup.

### Files cần di chuyển / dọn dẹp:
| File hiện tại | Hành động | Vị trí mới |
|---------------|-----------|------------|
| `mrjob.conf` (root) | Di chuyển | `conf/mrjob.conf` |
| `test_hive.py` (root) | Di chuyển | `src/mapreduce/test_hive.py` |
| `rules.md` (root) | Di chuyển | `docs/rules.md` |
| `tmp-pandas/` (root) | Đề xuất xóa | — |
| `refactor.md` (root) | Đề xuất xóa sau khi xong | — |
| `venv/` | Thêm vào `.gitignore` | — |

### [MODIFY] [README.md](file:///d:/Project/final-bdes/README.md)
- Cập nhật flow sử dụng: 3 scripts → `install_infra.sh` → `run.sh` → `stop.sh`
- Bỏ `setup.sh` khỏi hướng dẫn
- Cập nhật architecture diagram
- Ghi rõ mối liên hệ TripAdvisor ↔ TheMealDB

### [MODIFY] [GEMINI.md](file:///d:/Project/final-bdes/GEMINI.md)
- Cập nhật schema đúng với data thực
- Cập nhật danh sách 8 MapReduce jobs (thay `mr_price_segment` bằng `mr_rating_bucket`)
- Bổ sung `conf/` vào Project Structure

### [NEW] docs/process/refactor_log.md
- Log quá trình refactor từng module

**Manual test**: Đọc README từ đầu, clone repo mới, làm theo hướng dẫn.

---

## Verification Plan

### Automated Tests
```bash
# Module 1: Schema test
python src/ingest/init_db.py

# Module 2: MapReduce local test
python src/mapreduce/mr_rating_by_district.py src/crawler/seed/restaurants.json
python src/mapreduce/mr_cuisine_count.py src/crawler/seed/meals.json
python src/mapreduce/mr_rating_bucket.py src/crawler/seed/restaurants.json
python src/mapreduce/mr_sentiment_analysis.py src/crawler/seed/restaurants.json

# Module 3: HDFS pipeline test
python src/ingest/mongo_to_hdfs.py
python src/ingest/mysql_to_hdfs.py

# Module 5: Script test
bash bin/install_infra.sh --check-only  # (thêm flag này để chỉ verify version)
bash bin/run.sh                          # start without crawling
bash bin/stop.sh --backup                # stop with backup
```

### Manual Verification
- Streamlit: test CRUD (search by ID, pagination, multi-field update)
- Charts: verify không còn chart "Unknown" giả
- MapReduce output: mỗi job có summary statistics in ra console
- stop.sh --cleandata → run.sh --crawl → verify fresh data flow

---

## Thứ tự ưu tiên triển khai

```
┌─────────────────────────────────────────────────────────────────┐
│  Module 1: Schema Fix          (Nền tảng — làm trước tiên)     │
│  Module 2: MapReduce Alignment (Sau khi schema đúng)           │
│  Module 3: Ingest Pipeline     (Sau khi schema & MR đúng)      │
│  Module 4: Streamlit UI        (Sau khi data & views đúng)     │
│  Module 5: Bin Scripts         (Độc lập, làm song song M3/M4)  │
│  Module 6: Docs & Cleanup      (Sau cùng)                      │
└─────────────────────────────────────────────────────────────────┘
```

> [!NOTE]
> Mỗi module kết thúc bằng manual test. Sau khi bạn confirm pass, chúng ta tạo chat mới để refactor module tiếp theo — đảm bảo context sạch và tập trung.
