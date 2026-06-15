# HƯỚNG DẪN ĐỌC - 4 FILE VAI TRÒ CỤ THỂ

## 📋 Giới thiệu

Dự án này được chia thành **4 vai trò rõ ràng** tương ứng với **4 bước trong pipeline xử lý dữ liệu lớn**.

Mỗi thành viên nhóm cần đọc file `.md` tương ứng với vai trò của mình để:

- ✅ Hiểu rõ trách nhiệm & mục tiêu cụ thể
- ✅ Biết các files code liên quan ở đâu
- ✅ Nắm workflow & input/output của role đó
- ✅ Hiểu các vấn đề đã gặp phải & giải pháp
- ✅ Giải thích kết quả công việc trong báo cáo & trình bày

---

## 📂 4 File Văn Bản

### **File 1: ROLE_1_DATA_ENGINEER.md**

**Vai trò:** Nguyễn Văn A (Thu thập & Làm sạch dữ liệu)

**Mục đích:** Thu thập dữ liệu từ 2 nguồn (TripAdvisor + TheMealDB), làm sạch & lưu MongoDB + MySQL

**Người cần đọc:** Nguyễn Văn A (Data Engineer)

**Nội dung chính:**

- Cách hoạt động của Scrapy Crawler (TripAdvisor)
- Cách lấy dữ liệu từ REST API (TheMealDB)
- Các vấn đề gặp phải (403 Forbidden, Infinite Loop, Dirty Data)
- Giải pháp chi tiết để khắc phục
- Input/output cụ thể ở mỗi bước

**Điểm đạo được:** 1.75 điểm (Pipeline Dữ liệu)

---

### **File 2: ROLE_2_HADOOP_INFRASTRUCTURE.md**

**Vai trò:** Trần Thị B (Hadoop & Data Sync)

**Mục đích:** Đồng bộ dữ liệu từ MySQL/MongoDB lên HDFS, quản lý Apache Hive

**Người cần đọc:** Trần Thị B (Hadoop Infrastructure Engineer)

**Nội dung chính:**

- MySQL → HDFS sync (mysql_to_hdfs.py)
- MongoDB → HDFS sync (mongo_to_hdfs.py)
- Hive schema definition & external tables
- Hive analytics views (6 views)
- Các vấn đề gặp phải (Decimal type, ObjectId, HDFS directory exists)
- Kiến trúc HDFS & file paths

**Điểm đạo được:** 1.00 điểm (HDFS, YARN, Hive)

---

### **File 3: ROLE_3_MAPREDUCE_DEVELOPER.md**

**Vai trò:** Phan Kim E (MapReduce Developer)

**Mục đích:** Xây dựng & thực thi 8 chương trình MapReduce phân tích dữ liệu

**Người cần đọc:** Phan Kim E (MapReduce Developer)

**Nội dung chính:**

- 8 MapReduce jobs chi tiết:
  1. Cuisine Count
  2. Rating by District
  3. Rating Bucket
  4. Sentiment Analysis
  5. Ingredient Match
  6. Delivery Analysis
  7. Review Distribution
  8. Top Reviewed
- Mapper/Combiner/Reducer logic cho mỗi job
- Input/output format
- Các vấn đề gặp phải (Malformed JSON, Memory overflow, Regex optimization)
- Local testing & Hadoop execution
- Performance tuning

**Điểm đạo được:** 2.00 điểm (8 jobs × 0.25)

---

### **File 4: ROLE_4_UI_DEVELOPER.md**

**Vai trò:** Bùi Quang F (UI Developer & Media)

**Mục đích:** Xây dựng Streamlit GUI, CRUD operations, trực quan hóa dữ liệu

**Người cần đọc:** Bùi Quang F (UI Developer)

**Nội dung chính:**

- Streamlit app structure (3 pages)
- Page 1: CRUD operations (MySQL)
  - View Records (SELECT)
  - Insert New (INSERT)
  - Update Record (UPDATE)
  - Delete Record (DELETE)
- Page 2: Big Data Reports (6 charts)
  - Avg Rating by District (Bar)
  - Cuisine Frequency (Donut)
  - Rating Histogram (Bar)
  - Top Districts (Bar)
  - Review Star Distribution (Line)
  - Delivery vs Dine-in (Grouped Bar)
- Hive Connector (3-layer fallback)
- Các vấn đề gặp phải (WSL2 connection, HiveServer2 timeout, Nested arrays)
- Chart responsiveness & export features

**Điểm đạo được:** 2.00 điểm (GUI + Trực quan hóa)

---

## 🔄 Pipeline Dữ liệu (Thứ tự đọc)

Nếu bạn muốn hiểu **toàn bộ dự án**, hãy đọc theo thứ tự này:

```
1. ROLE_1_DATA_ENGINEER.md
   ↓ (Output: MySQL + MongoDB)

2. ROLE_2_HADOOP_INFRASTRUCTURE.md
   ↓ (Output: HDFS + Hive tables)

3. ROLE_3_MAPREDUCE_DEVELOPER.md
   ↓ (Output: Aggregated results in /data/output/)

4. ROLE_4_UI_DEVELOPER.md
   ↓ (Output: Interactive Dashboard)

   ✅ Hoàn thành Pipeline
```

---

## 📝 Cấu trúc mỗi File

Mỗi file `.md` được tổ chức như sau:

### **1. GIỚI THIỆU TỔNG QUÁT**

- Vai trò trong pipeline
- Trách nhiệm cụ thể
- Tại sao chọn công nghệ (tech stack reasoning)

### **2. CẤU TRÚC CÁC FILE LIÊN QUAN**

- Vị trí files code (`src/...`)
- Cách hoạt động (workflow diagram)
- Input/Output format

### **3. CÁC VẤN ĐỀ GẶP PHẢI & GIẢI PHÁP**

- Triệu chứng (symptoms)
- Nguyên nhân sâu tầng (root causes)
- Giải pháp chi tiết (solutions with code)
- Kết quả đạt được

### **4. WORKFLOW THỰC HIỆN & INPUT/OUTPUT**

- Bước-by-bước hướng dẫn
- Lệnh chạy cụ thể
- Output dự kiến

### **5. HƯỚNG DẪN CHẠY & DEBUGGING**

- Full pipeline commands
- Troubleshooting tips
- Testing strategies

### **6. KỲ VỌNG VỀ KỸ NĂNG CẦN CÓ**

- Kiến thức yêu cầu
- Kỹ năng technical
- Background knowledge

### **7. KẾT LUẬN & ĐIỂM ĐÁNH GIÁ**

- Kết quả dự kiến
- Điểm đạo được (theo tiêu chuẩn giảng viên)
- Checklist hoàn thành

---

## 🎯 Cách Sử Dụng File

### Tình huống 1: **Bạn là Nguyễn Văn A (Data Engineer)**

```
1. Mở: ROLE_1_DATA_ENGINEER.md
2. Đọc section "CẤU TRÚC CÁC FILE"
   → Hiểu tripadvisor.py, fetch_mealdb.py, init_db.py nằm ở đâu
3. Đọc section "CÁC VẤN ĐỀ GẶP PHẢI"
   → Hiểu 6 vấn đề chính (403 Forbidden, Infinite Loop, Null Address, ...)
   → Hiểu giải pháp & code cụ thể
4. Đọc section "WORKFLOW THỰC HIỆN"
   → Biết input, output, lệnh chạy ở mỗi bước
5. Lúc trình bày:
   → Giải thích vấn đề & cách giải quyết (referring to doc)
   → Show code snippets từ file path cụ thể
   → Giải thích tại sao chọn Scrapy, Playwright, MongoDB, MySQL
```

### Tình huống 2: **Bạn là Trần Thị B (Hadoop Infrastructure)**

```
1. Mở: ROLE_2_HADOOP_INFRASTRUCTURE.md
2. Đọc section "CẤU TRÚC CÁC FILE"
   → Hiểu mysql_to_hdfs.py, mongo_to_hdfs.py, hive_schema.sql
3. Đọc section "CÁC VẤN ĐỀ GẶP PHẢI"
   → Học cách giải quyết Decimal type, ObjectId, HDFS errors
4. Đọc section "KIẾN TRÚC HDFS"
   → Hiểu file structure trên HDFS
5. Lúc trình bày:
   → Show cách MongoDB & MySQL data được synced
   → Explain Hive external tables & views
   → Demo queries trên Hive
```

### Tình huống 3: **Bạn là Phan Kim E (MapReduce Developer)**

```
1. Mở: ROLE_3_MAPREDUCE_DEVELOPER.md
2. Đọc section "DETAILED JOB SPECIFICATIONS"
   → Chi tiết 8 jobs (mapper, combiner, reducer logic)
3. Đọc section "CÁC VẤN ĐỀ GẶP PHẢI"
   → Học memory optimization, regex performance, case sensitivity
4. Chạy test_local.py để verify mỗi job hoạt động
5. Chạy run_all_jobs.py trên Hadoop cluster
6. Lúc trình bày:
   → Giải thích mapper/reducer logic cho mỗi job
   → Show real output từ HDFS
   → Explain performance tuning decisions
```

### Tình huống 4: **Bạn là Bùi Quang F (UI Developer)**

```
1. Mở: ROLE_4_UI_DEVELOPER.md
2. Đọc section "DETAILED PAGE SPECIFICATIONS"
   → Hiểu CRUD operations & chart rendering
3. Đọc section "CÁC VẤN ĐỀ GẶP PHẢI"
   → Fix MySQL connection issues, Hive timeouts, responsive design
4. Start Streamlit app
5. Test CRUD operations & Analytics charts
6. Lúc trình bày:
   → Show GUI screenshots
   → Explain CRUD workflow
   → Demo interactive charts
   → Explain fallback mechanisms (offline mode)
```

---

## 🔗 File References

Các file markdown này **reference trực tiếp** các files code trong project:

| Markdown File                   | References                                                                                 |
| ------------------------------- | ------------------------------------------------------------------------------------------ |
| ROLE_1_DATA_ENGINEER.md         | `src/crawler/tripadvisor_job/`, `src/crawler/fetch_mealdb.py`, `src/ingest/init_db.py`     |
| ROLE_2_HADOOP_INFRASTRUCTURE.md | `src/ingest/mysql_to_hdfs.py`, `mongo_to_hdfs.py`, `hive_schema.sql`, `hive_analytics.sql` |
| ROLE_3_MAPREDUCE_DEVELOPER.md   | `src/mapreduce/*.py`, `test_local.py`, `run_all_jobs.py`                                   |
| ROLE_4_UI_DEVELOPER.md          | `src/streamlit_app/app.py`, `hive_connector.py`                                            |

Khi đọc, bạn có thể **trực tiếp xem code** ở các vị trí đó.

---

## 💡 Mẹo Sử Dụng

### ✅ Làm tốt hơn khi trình bày

1. **Trích dẫn code cụ thể** từ các files
   - "Xem [tripadvisor.py dòng 135-145] để hiểu MAX_REVIEWS logic"
   - "Trong [hive_schema.sql dòng 40] định nghĩa ARRAY<STRUCT>"

2. **Giải thích vấn đề → Giải pháp** (theo cấu trúc markdown)
   - Triệu chứng: "Crawler bị infinite loop"
   - Nguyên nhân: "30 nhà hàng nổi tiếng có hàng nghìn reviews"
   - Giải pháp: "Thêm MAX_REVIEWS = 75 constant"
   - Kết quả: "1,334 restaurants lưu thành công"

3. **Demo thực tế**
   - Run commands ở terminal
   - Show output thực tế
   - Giải thích kết quả

---

## 📊 Điểm Đánh Giá Tổng Hợp

| Vai trò                                | Điểm     | File Tham Khảo                  |
| -------------------------------------- | -------- | ------------------------------- |
| **Nguyễn Văn A** (Data Engineer)       | 1.75     | ROLE_1_DATA_ENGINEER.md         |
| **Trần Thị B** (Hadoop Infrastructure) | 1.00     | ROLE_2_HADOOP_INFRASTRUCTURE.md |
| **Phan Kim E** (MapReduce Developer)   | 2.00     | ROLE_3_MAPREDUCE_DEVELOPER.md   |
| **Bùi Quang F** (UI Developer)         | 2.00     | ROLE_4_UI_DEVELOPER.md          |
| **TOTAL**                              | **6.75** | ---                             |

---

## 🚀 Quick Start

### Nếu bạn muốn nhanh hiểu dự án:

1. Đọc **ROLE_1_DATA_ENGINEER.md** (7 phút)
   → Hiểu dữ liệu từ đâu, format như thế nào

2. Đọc **ROLE_2_HADOOP_INFRASTRUCTURE.md** (7 phút)
   → Hiểu dữ liệu được đưa lên HDFS thế nào

3. Đọc **ROLE_3_MAPREDUCE_DEVELOPER.md** (10 phút)
   → Hiểu dữ liệu được xử lý thế nào

4. Đọc **ROLE_4_UI_DEVELOPER.md** (7 phút)
   → Hiểu dữ liệu được trực quan hóa thế nào

**Tổng cộng: ~31 phút → Hiểu toàn bộ pipeline**

---

## ❓ FAQ

**Q: Tôi nên đọc file nào?**
A: Đọc file tương ứng với vai trò của bạn trong README.md (bảng phân công công việc).

**Q: File có sắp xếp theo pipeline không?**
A: Có! File 1 → 2 → 3 → 4 theo thứ tự dữ liệu chảy trong hệ thống.

**Q: Tôi có thể đọc file của người khác không?**
A: **CÓ!** Đó là cách tốt nhất để hiểu toàn bộ dự án. Đội tốt khi mỗi người biết hàng xóm của mình làm gì.

**Q: Khi nào tôi nên tham khảo file này?**
A:

- Lúc **chuẩn bị báo cáo** (quên phần nào, đọc lại)
- Lúc **trình bày** (biết giải thích gì)
- Lúc **debug** (vấn đề đã từng gặp)
- Lúc **học thêm** (từ công nghệ khác)

**Q: Các file này có chính xác không?**
A: Các file này dựa trên code thực tế + process logs (`docs/process/`). Nếu phát hiện sai lệch, cập nhật file.

---

## 📞 Liên Hệ & Hỗ Trợ

Nếu có câu hỏi về:

- **Data Engineer role**: Hỏi Nguyễn Văn A
- **Hadoop role**: Hỏi Trần Thị B
- **MapReduce role**: Hỏi Phan Kim E
- **UI role**: Hỏi Bùi Quang F

Hoặc **đọc file tương ứng** để tìm câu trả lời.

---

**Chúc bạn học tập hiệu quả! 🚀**
