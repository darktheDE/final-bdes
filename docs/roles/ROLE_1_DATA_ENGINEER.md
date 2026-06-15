# VAI TRÒ 1: DATA ENGINEER & DB - Nguyễn Văn A

**Mục tiêu chính:** Thu thập dữ liệu từ 2 nguồn khác nhau, làm sạch và lưu trữ vào MongoDB + MySQL  
**Điểm đạo được:** 1.75 điểm (Pipeline Dữ liệu & Làm sạch)

---

## 1. GIỚI THIỆU TỔNG QUÁT

### Vai trò trong Pipeline Dữ liệu

Data Engineer là **bước đầu tiên** trong pipeline xử lý dữ liệu lớn. Bạn chịu trách nhiệm:

1. **Thu thập dữ liệu** từ TripAdvisor (Scrapy Crawler) + TheMealDB (REST API)
2. **Làm sạch & chuẩn hóa** dữ liệu (xử lý duplicates, null values, format)
3. **Lưu trữ vào staging DBMS** (MongoDB NoSQL + MySQL Relational)

Dữ liệu bạn xử lý sẽ được các thành viên khác đưa lên HDFS, chạy MapReduce, và trực quan hóa trên Streamlit.

### Tại sao chọn công nghệ này?

| Công nghệ                | Lý do chọn                                                                                                                            |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------- |
| **Scrapy + Playwright**  | TripAdvisor là dynamic website (React JS), cần render thực tế. Scrapy là framework crawler mạnh nhất, Playwright là trình duyệt thực. |
| **REST API (TheMealDB)** | Đơn giản, không cần crawler, cung cấp dữ liệu cấu trúc tốt, free tier đủ 300+ meals                                                   |
| **MongoDB**              | NoSQL phù hợp dữ liệu nửa cấu trúc từ TripAdvisor (nested reviews), linh hoạt schema                                                  |
| **MySQL**                | Relational DB tối ưu cho CRUD ops tác nghiệp, query SQL nhanh cho Streamlit                                                           |
| **Python**               | Scripting ngôn ngữ duy nhất trong đồ án, dễ viết ETL scripts                                                                          |

---

## 2. CẤU TRÚC CÁC FILE LIÊN QUAN

### 2.1 Thu thập dữ liệu từ TripAdvisor (Scrapy)

**Vị trí:** `src/crawler/tripadvisor_job/`  
**File chính:**

- [tripadvisor.py](src/crawler/tripadvisor_job/tripadvisor_job/spiders/tripadvisor.py) - Spider chính
- [items.py](src/crawler/tripadvisor_job/tripadvisor_job/items.py) - Schema dữ liệu
- [pipelines.py](src/crawler/tripadvisor_job/tripadvisor_job/pipelines.py) - Data cleaning + MongoDB insertion
- [settings.py](src/crawler/tripadvisor_job/tripadvisor_job/settings.py) - Cấu hình Scrapy/Playwright

**Cách hoạt động:**

```
TripAdvisor Website (HTTPS)
    ↓
Playwright (headful browser + stealth mode)
    ↓
Scrapy CrawlSpider
    ├─ Rule 1: Tìm pagination links (-oa0-, -oa30-, ...)
    └─ Rule 2: Tìm restaurant URLs (Restaurant_Review-g293925-d...)
    ↓
parse_restaurant() callback
    ├─ Extract: name, rating, address, district, city
    ├─ Paginate reviews: -or0-, -or15-, -or30-, ..., -or75-
    └─ Aggregate reviews array across pages
    ↓
TripadvisorMongoPipeline
    ├─ Clean data (extract_float, extract_int)
    ├─ Handle nulls & missing fields
    └─ Upsert into MongoDB (restaurants collection)
    ↓
full_output.json (MongoDB backup)
```

**Input:** URL = `https://www.tripadvisor.com/Restaurants-g293925-oa0-Ho_Chi_Minh_City.html`

**Output:**

```json
{
  "_id": "https://www.tripadvisor.com/Restaurant_Review-g293925-d1234567-...",
  "name": "Pho King",
  "rating": 4.5,
  "review_count": 324,
  "address": "123 Nguyen Hue, Quận 1, Ho Chi Minh City",
  "district": "Quận 1",
  "city": "Ho Chi Minh City",
  "reviews": [
    {
      "user": "John Doe",
      "rating": 5.0,
      "comment": "Excellent pho! Highly recommend."
    },
    ...
  ]
}
```

### 2.2 Thu thập dữ liệu từ TheMealDB (REST API)

**Vị trí:** `src/crawler/fetch_mealdb.py`

**Cách hoạt động:**

```
TheMealDB Open API (HTTP)
    ├─ Endpoint 1: search.php?f={A-Z} (26 calls = 300+ meals)
    ├─ Endpoint 2: list.php?c=list (Categories)
    ├─ Endpoint 3: list.php?a=list (Areas)
    └─ Endpoint 4: list.php?i=list (Ingredients)
    ↓
parse_meal() function
    ├─ Map idMeal → _id (e.g., "meal_52772")
    ├─ Collapse strIngredient1..20 → ingredients array
    └─ Extract: name, category, area, instructions
    ↓
Offline Fallback (seed files)
    └─ Save to: src/crawler/seed/{meals.json, categories.json, areas.json, ingredients.json}
    ↓
MongoDB Insertion
    └─ Upsert into MongoDB (meals collection)
```

**Input:** API calls (26 alphabet searches)

**Output:**

```json
{
  "_id": "meal_52772",
  "name": "Pho",
  "category": "Beef",
  "area": "Vietnamese",
  "instructions": "Simmer beef bones for 12 hours...",
  "ingredients": ["Beef", "Rice Noodles", "Star Anise", "Cinnamon", ...]
}
```

### 2.3 Làm sạch dữ liệu & MySQL Ingestion

**Vị trí:** `src/ingest/init_db.py`

**Cách hoạt động:**

```
MongoDB Collections (restaurants, meals)
    ↓
init_db.py ETL Pipeline
    ├─ Step 1: Connect to MongoDB → Extract
    ├─ Step 2: Data Normalization
    │   ├─ _parse_review_count(): "(112)" → 112
    │   ├─ _extract_district(): "18B/17 Đ. Nguyễn Thị Minh Khai Quận 1" → "Quận 1"
    │   ├─ _normalize_city(): "Ho Chi Minh City 70000 Vietnam" → "Ho Chi Minh City"
    │   └─ Parse review ratings: "5 of 5 bubbles" → 5.0
    ├─ Step 3: Schema Transformation
    │   └─ Flatten nested MongoDB structure into relational tables
    └─ Step 4: Load into MySQL
        ├─ restaurants: (id, name, rating, review_count, address, district, district_parsed, city, price_range)
        ├─ reviews: (id, restaurant_id, user, rating, comment)
        └─ meals: (id, name, category, area, ingredients_list)
```

**Input:** MongoDB collections

**Output:** MySQL tables with normalized schema

---

## 3. CÁC VẤN ĐỀ GẶP PHẢI & GIẢI PHÁP

### Vấn đề 1: HTTP 403 Forbidden từ TripAdvisor

**Triệu chứng:**

- Scrapy nhận lỗi `HTTP 403 Forbidden` ngay lần request đầu tiên
- Spider không thể extract link nào

**Nguyên nhân sâu tầng:**
TripAdvisor sử dụng anti-bot system (DataDome/PerimeterX) để phát hiện crawler. Dù Playwright dùng Chromium thực, nhưng browser vẫn expose `navigator.webdriver = true` cho phép các hệ thống anti-bot phát hiện.

**Giải pháp chi tiết:**
Áp dụng **Stealth Mode** trong [settings.py](src/crawler/tripadvisor_job/tripadvisor_job/settings.py) dòng 70-83:

```python
PLAYWRIGHT_LAUNCH_OPTIONS = {
    "headless": False,  # Mở browser thực (không headless)
    "args": [
        "--disable-blink-features=AutomationControlled",  # Ẩn webdriver flag
    ]
}
```

Thêm `playwright-stealth` package và cấu hình User-Agent đúng thực trong `DEFAULT_REQUEST_HEADERS`.

**Kết quả:** Spider nhận `HTTP 200 OK` và extract được 35+ restaurant links từ trang đầu.

---

### Vấn đề 2: Infinite Loop & Review Array Overwrite

**Triệu chứng:**

- Crawler bị stuck vòng lặp vô hạn ở 30 nhà hàng đầu tiên
- File output JSON chỉ chứa max 15 reviews/nhà hàng (không phải 75)
- Chỉ reviews từ trang cuối cùng được lưu; reviews từ trang 1-4 bị xóa

**Nguyên nhân sâu tầng:**

1. **Vòng lặp:** 30 nhà hàng đầu tiên rất nổi tiếng, có hàng nghìn reviews. Để lấy 3000+ reviews/nhà hàng cần 200 trang = hàng giờ xử lý
2. **Overwrite:** Trong callback `parse_restaurant()` dòng 61-72, biến `reviews = []` được khởi tạo **mỗi lần request**, ghi đè reviews từ trang trước

**Giải pháp chi tiết:**
Xem [tripadvisor.py](src/crawler/tripadvisor_job/tripadvisor_job/spiders/tripadvisor.py) dòng 61-75:

```python
# Conditional initialization (chỉ lần đầu)
if 'restaurant_item' in response.meta:
    item = response.meta['restaurant_item']
    reviews = item['reviews']  # Lấy reviews từ trang trước
else:
    # Lần đầu: khởi tạo item mới
    item = TripadvisorJobItem()
    item['name'] = ...
    reviews = []  # Khởi tạo lần đầu

# Append reviews (không overwrite)
for block in review_blocks:
    ...
    reviews.append({...})

item['reviews'] = reviews
```

Thêm constant `MAX_REVIEWS = 75` dòng 135-145:

```python
if (total_reviews > 0 and next_offset >= total_reviews) or next_offset >= MAX_REVIEWS:
    yield item  # Dừng pagination
else:
    # Tiếp tục tới trang tiếp
    yield response.follow(next_url, ...)
```

**Kết quả:** 1,334 restaurants với trung bình 34 reviews/nhà hàng (capped at 75), **không infinite loop**.

---

### Vấn đề 3: Null Address trên Paginated Pages

**Triệu chứng:**

- Trang 1 extract address thành công: "123 Nguyen Hue, Quận 1"
- Trang 2-5 address trở thành `null`

**Nguyên nhân sâu tầng:**
XPath để extract address `//*[@id="lithium-root"]/main/div/.../button/span/text()` được chạy **lại trên mỗi trang paginated**. DOM structure khác nhau giữa trang chính và review pages, nên XPath fail = return `null`, overwrite giá trị address tốt từ trang 1.

**Giải pháp chi tiết:**
Trong [tripadvisor.py](src/crawler/tripadvisor_job/tripadvisor_job/spiders/tripadvisor.py) dòng 61-75:

```python
if 'restaurant_item' not in response.meta:
    # Chỉ extract address lần đầu (trang chính)
    address = response.xpath('//*[@id="lithium-root"]/main/div/.../button/span/text()').get()
    item['address'] = address
else:
    # Lần paginate: KHÔNG re-extract address
    item = response.meta['restaurant_item']
    # address giữ nguyên giá trị từ trang 1
```

**Kết quả:** Address được bảo toàn qua tất cả 5 trang pagination.

---

### Vấn đề 4: Fake HTTP 200 CAPTCHA từ DataDome

**Triệu chứng:**

- Trang hiển thị HTTP 200 OK nhưng nội dung là DataDome CAPTCHA challenge
- XPath extraction không match vì DOM structure khác

**Nguyên nhân sâu tầng:**
DataDome hoạt động ở tầng JavaScript. Khi phát hiện traffic lạ, nó inject CAPTCHA page nhưng vẫn return `200 OK` (trái ngược với 403) để bypass middleware của crawler.

**Giải pháp chi tiết:**
Sử dụng **headful browser rendering** trong [settings.py](src/crawler/tripadvisor_job/tripadvisor_job/settings.py) dòng 70-81:

```python
PLAYWRIGHT_LAUNCH_OPTIONS = {
    "headless": False,  # Mở browser UI (không headless)
    ...
}
```

Khi Playwright chạy browser thực (headful), nó tự động:

1. Execute DataDome's JS behavior checks
2. DataDome validate browser là thật → issue valid session cookie
3. CAPTCHA challenge không bao giờ hiển thị → bypass tự động

**Kết quả:** Crawler bypass 403 và extract được dữ liệu sạch.

---

### Vấn đề 5: Dirty Data - Rating/Review Count Formats

**Triệu chứng:**

- MongoDB chứa rating: `"4 of 5 bubbles"` (STRING, không phải FLOAT)
- Review count: `"(112)"` (STRING, không phải INT)
- Không thể tính toán avg rating trên SQL

**Nguyên nhân:**
Scrapy extract HTML text trực tiếp, nên lưu string thô thay vì parsed value.

**Giải pháp chi tiết:**
Trong [pipelines.py](src/crawler/tripadvisor_job/tripadvisor_job/pipelines.py) dòng 32-54:

```python
def extract_float(self, value):
    """Convert "4 of 5 bubbles" → 4.0"""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    match = re.search(r'(\d+(\.\d+)?)', str(value))
    if match:
        return float(match.group(1))
    return None

def extract_int(self, value):
    """Convert "(112)" → 112"""
    if value is None:
        return 0
    if isinstance(value, int):
        return value
    digits = re.sub(r'\D', '', str(value))  # Loại bỏ tất cả non-digits
    if digits:
        return int(digits)
    return 0

def process_item(self, item, spider):
    rest['rating'] = self.extract_float(rest.get('rating'))
    rest['review_count'] = self.extract_int(rest.get('review_count'))
    ...
```

**Kết quả:** Rating lưu dạng `4.0` (FLOAT), Review count lưu dạng `112` (INT).

---

### Vấn đề 6: TheMealDB API Network Failure Fallback

**Triệu chứng:**

- Internet bị mất trong khi fetch từ API
- Script crash và phải re-run từ đầu

**Giải pháp chi tiết:**
Trong [fetch_mealdb.py](src/crawler/fetch_mealdb.py) dòng 101-139:

```python
try:
    # Priority 1: Fetch from live API
    meals_data, categories, areas, ingredients = fetch_from_api()
    # Save to seed for next time
    save_to_seed(meals_data, "meals.json")
except Exception as e:
    # Priority 2: Fallback to offline seed files
    print("[!] Network error encountered: {e}")
    print("[!] Engaging Offline Fallback Mechanism...")
    meals_data, categories, areas, ingredients = load_from_seed()

if not meals_data:
    print("[-] Critical Failure: Could not retrieve meal data")
    sys.exit(1)
```

Seed files lưu trong `src/crawler/seed/`:

- `meals.json` (666 meals)
- `categories.json`
- `areas.json`
- `ingredients.json`

**Kết quả:** Nếu API down, script tự động dùng seed file local. **Zero downtime untuk pipeline.**

---

## 4. WORKFLOW THỰC HIỆN & INPUT/OUTPUT

### Bước 1: Thu thập TripAdvisor

**File:** [tripadvisor.py](src/crawler/tripadvisor_job/tripadvisor_job/spiders/tripadvisor.py)

**Input:**

- Start URL: `https://www.tripadvisor.com/Restaurants-g293925-oa0-Ho_Chi_Minh_City.html`
- Pagination rules: `-oa{number}-`, `Restaurant_Review-...`

**Lệnh chạy:**

```bash
cd src/crawler/tripadvisor_job
scrapy crawl tripadvisor -o full_output.json
```

**Output:** `src/crawler/tripadvisor_job/full_output.json`

- 1,334 nhà hàng
- ~44,000 reviews tổng cộng
- File size: ~15 MB

---

### Bước 2: Thu thập TheMealDB & Offline Seed

**File:** [fetch_mealdb.py](src/crawler/fetch_mealdb.py)

**Input:** TheMealDB API endpoints

**Lệnh chạy:**

```bash
python src/crawler/fetch_mealdb.py
```

**Output:**

- `src/crawler/seed/meals.json` (666 meals)
- `src/crawler/seed/categories.json`
- `src/crawler/seed/areas.json`
- `src/crawler/seed/ingredients.json`

---

### Bước 3: MongoDB Ingestion (Auto trong Pipeline)

**File:** [tripadvisor.py](src/crawler/tripadvisor_job/tripadvisor_job/spiders/tripadvisor.py) (pipeline) + [fetch_mealdb.py](src/crawler/fetch_mealdb.py) (direct insert)

**Pipeline tự động:**

1. Scrapy spider → TripadvisorMongoPipeline (clean + upsert)
2. fetch_mealdb.py → save_to_mongodb()

**Output:**

- MongoDB `sentiment_db.restaurants` (1,334 docs)
- MongoDB `sentiment_db.meals` (666 docs)

---

### Bước 4: MySQL Normalization & Ingestion

**File:** [init_db.py](src/ingest/init_db.py)

**Input:** MongoDB collections (restaurants, meals)

**Lệnh chạy:**

```bash
python src/ingest/init_db.py
```

**Quá trình:**

1. Extract từ MongoDB
2. Normalize fields (rating, review_count, district, city)
3. Flatten nested reviews vào separate table
4. Upsert vào MySQL tables

**Output:**

- MySQL `food_sentiment_db.restaurants` (1,334 rows)
- MySQL `food_sentiment_db.reviews` (~44,000 rows)
- MySQL `food_sentiment_db.meals` (666 rows)

---

## 5. HƯỚNG DẪN CHẠY & DEBUGGGING

### Chạy hoàn toàn (Data Engineer)

```bash
# 1. Activate venv
source venv/bin/activate

# 2. TripAdvisor Scraping (có thể mất 2-6 tiếng)
cd src/crawler/tripadvisor_job
scrapy crawl tripadvisor -o full_output.json

# 3. TheMealDB Fetch
cd ../../../
python src/crawler/fetch_mealdb.py

# 4. Verify MongoDB
python src/ingest/import_tripadvisor.py  # (optional, import full_output.json)

# 5. MySQL Ingestion
python src/ingest/init_db.py
```

### Test trước khi full run

```bash
# Test scraper trên 1-2 restaurants
scrapy crawl tripadvisor -o test_output.json -a max_restaurants=2

# Test fetch_mealdb (dùng seed file nếu Internet down)
python src/crawler/fetch_mealdb.py --offline

# Test MySQL connection
python -c "import mysql.connector; conn = mysql.connector.connect(...); print('OK')"
```

---

## 6. KỲ VỌNG VỀ KỸ NĂNG CẦN CÓ

Để hoàn thành vai trò này hiệu quả, bạn cần:

1. **Web Scraping & Automation**
   - Hiểu Scrapy framework (spiders, pipelines, rules)
   - Biết CSS/XPath selectors
   - Nắm Playwright/Selenium để bypass anti-bot

2. **Database Design**
   - Normalize schema cho MySQL (1NF, 2NF, 3NF)
   - Hiểu BSON/Document model cho MongoDB
   - Indexing để query nhanh

3. **Data Cleaning & ETL**
   - Regular expressions để parse messy strings
   - Pandas/Python để transform data
   - Error handling & logging

4. **API Integration**
   - HTTP requests, headers, rate limiting
   - JSON parsing
   - Error handling (network failures, 403, 429, etc.)

---

## 7. KẾT LUẬN & ĐIỂM ĐÁNH GIÁ

**Kết quả dự kiến:**

- ✅ Thu thập 1,000+ records từ 2 nguồn khác nhau (TripAdvisor + TheMealDB)
- ✅ Xử lý clean data (remove nulls, normalize formats)
- ✅ Staging vào MongoDB (NoSQL) + MySQL (Relational)
- ✅ Data ready cho HDFS ingestion (bước tiếp theo)

**Điểm đạo được:** **1.75/1.75** (100%)

- Nguồn dữ liệu: 0.25
- Kích thước dữ liệu: 0.25
- Làm sạch dữ liệu: 0.75
- Staging DBMS: 0.50
