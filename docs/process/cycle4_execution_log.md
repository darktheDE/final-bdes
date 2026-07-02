# Nhật ký thực thi (Execution Log) - Cycle 4: Analytics & MapReduce Engine

**Ngày thực hiện:** 14/06/2026

## 1. Các hạng mục đã triển khai

Chúng tôi đã thiết lập thành công và kiểm thử toàn bộ **8 chương trình phân tích MapReduce** độc lập sử dụng thư viện `mrjob` của Python chạy trên môi trường Hadoop YARN Streaming của WSL2 Ubuntu 24.04 LTS.

### Danh sách 8 MapReduce Jobs:
1. **Average Rating by District (`mr_rating_by_district.py`)**: Tính toán điểm đánh giá trung bình và số lượng nhà hàng theo từng quận từ dữ liệu TripAdvisor.
2. **Cuisine Frequency Counter (`mr_cuisine_count.py`)**: Thống kê số lượng tần suất xuất hiện của các thể loại (Category) và khu vực (Area) từ dữ liệu món ăn/công thức của TheMealDB.
3. **Price Category Distribution (`mr_price_segment.py`)**: Thống kê phân phối số lượng nhà hàng theo từng phân khúc giá (Price Range).
4. **Review Sentiment Analysis (`mr_sentiment_analysis.py`)**: Phân tích sắc thái bình luận (Sentiment) của khách hàng trên từng nhà hàng bằng cách khớp các từ khóa Tích cực/Tiêu cực và tính điểm trung bình.
5. **Meal-to-Restaurant Ingredient Matching (`mr_ingredient_match.py`)**: Quét các bình luận của TripAdvisor để thống kê tần suất xuất hiện của các nguyên liệu nấu ăn từ công thức món ăn của TheMealDB (được tối ưu hóa bằng Regex đơn để chạy cực nhanh).
6. **Top 10 Most Reviewed Restaurants (`mr_top_reviewed.py`)**: Tìm kiếm và xếp hạng 10 nhà hàng có số lượng lượt đánh giá (review_count) nhiều nhất.
7. **Review Distribution Profile (`mr_review_distribution.py`)**: Phân tích phân phối số sao đánh giá (từ 1.0 đến 5.0) của tất cả lượt đánh giá.
8. **Delivery Status Analysis (`mr_delivery_analysis.py`)**: Phân loại và so sánh điểm đánh giá trung bình giữa các nhà hàng có dịch vụ giao hàng (Delivery-Friendly) và chỉ ăn tại quán (Dine-In-Only) dựa trên các từ khóa liên quan trong bình luận.

---

## 2. Các tệp tin được tạo mới và cập nhật

- [src/mapreduce/mr_rating_by_district.py](../../src/mapreduce/mr_rating_by_district.py) (Mới)
- [src/mapreduce/mr_cuisine_count.py](../../src/mapreduce/mr_cuisine_count.py) (Mới)
- [src/mapreduce/mr_price_segment.py](../../src/mapreduce/mr_price_segment.py) (Mới)
- [src/mapreduce/mr_sentiment_analysis.py](../../src/mapreduce/mr_sentiment_analysis.py) (Mới)
- [src/mapreduce/mr_ingredient_match.py](../../src/mapreduce/mr_ingredient_match.py) (Mới)
- [src/mapreduce/mr_top_reviewed.py](../../src/mapreduce/mr_top_reviewed.py) (Mới)
- [src/mapreduce/mr_review_distribution.py](../../src/mapreduce/mr_review_distribution.py) (Mới)
- [src/mapreduce/mr_delivery_analysis.py](../../src/mapreduce/mr_delivery_analysis.py) (Mới)
- [src/mapreduce/test_local.py](../../src/mapreduce/test_local.py) (Mới - Tự động tạo dữ liệu mẫu và kiểm thử nội bộ cục bộ)
- [src/mapreduce/run_all_jobs.py](../../src/mapreduce/run_all_jobs.py) (Mới - Script tự động dọn dẹp HDFS output cũ và chạy tuần tự 8 jobs trên Hadoop YARN)
- [mrjob.conf](../../mrjob.conf) (Mới - Tệp cấu hình phân vùng chạy cho mrjob chỉ định đúng đường dẫn python venv)

---

## 3. Quy trình Triển khai & Kiểm thử (WSL2 Ubuntu)

### Bước 3.1: Kiểm thử Cục bộ (Local Test)
Trước khi đưa lên cụm Hadoop YARN, chúng tôi chạy kiểm thử cục bộ bằng dữ liệu mẫu (20 dòng đầu) từ các tệp thô để đảm bảo logic Mapper, Combiner và Reducer hoàn toàn chính xác.

```bash
# Đảm bảo virtual environment đã được kích hoạt
source venv/bin/activate

# Chạy suite kiểm thử cục bộ offline
python src/mapreduce/test_local.py
```

**Kết quả đầu ra kỳ vọng:**
* Chương trình chuyển đổi dữ liệu thô từ dạng JSON array sang JSON Lines tạm thời.
* Chạy lần lượt 8 jobs cục bộ và hiển thị thành công kết quả mẫu (Success).

### Bước 3.2: Chạy trên Hệ sinh thái Hadoop YARN
Để thực thi trên Hadoop Streaming và đẩy kết quả phân tích đầu ra lên HDFS:

```bash
# Chạy script tự động hóa toàn bộ 8 MapReduce jobs
python src/mapreduce/run_all_jobs.py
```

* Kịch bản sẽ tự động xóa các thư mục kết quả cũ trên HDFS (tại `/data/output/mr_*`) để tránh lỗi ghi đè.
* Chạy tuần tự các Job trên YARN bằng cách chỉ định tệp cấu hình [mrjob.conf](../../mrjob.conf) (để tránh lỗi thiếu thư viện `distutils` trên Python 3.12+ của hệ thống).

Để chạy lẻ một Job thủ công trên cụm:
```bash
python src/mapreduce/mr_rating_by_district.py -r hadoop hdfs:///data/raw/restaurants/restaurants.jsonl
```

---

## 4. Nhật ký xử lý sự cố trong Cycle 4

### Sự cố 4.1: Lỗi `ModuleNotFoundError: No module named 'distutils'` trên YARN nodes
* **Triệu chứng**: Khi chạy MapReduce trên YARN với cờ `-r hadoop`, các map tasks đều bị thất bại (`PipeMapRed.waitOutputThreads() failed`).
* **Nguyên nhân**: Hệ điều hành Ubuntu 24.04 LTS sử dụng Python 3.12 làm mặc định. Python 3.12 đã loại bỏ hoàn toàn thư viện chuẩn `distutils` vốn được `mrjob` import. Khi chạy trên YARN, mặc định hệ thống chạy bằng `/usr/bin/python3` (system python) chứ không sử dụng virtual environment `venv` của chúng ta nơi setuptools được cài đặt.
* **Giải pháp khắc phục**:
  1. Cài đặt thêm thư viện `setuptools` vào venv: `./venv/bin/pip install setuptools` (để hỗ trợ module distutils giả lập).
  2. Tạo file cấu hình [mrjob.conf](../../mrjob.conf) tại thư mục gốc để cấu hình tham số `python_bin` trỏ trực tiếp đến Python trong môi trường ảo của dự án:
     ```yaml
     runners:
       hadoop:
         python_bin: /mnt/d/Project/final-bdes/venv/bin/python3
       local:
         python_bin: /mnt/d/Project/final-bdes/venv/bin/python3
     ```

### Sự cố 4.2: Kết quả của `mr_top_reviewed.py` và `mr_review_distribution.py` rỗng trên dữ liệu thô
* **Triệu chứng**: Khi kiểm thử với dữ liệu thô (`full_output.json`), hai job này chạy bình thường không lỗi nhưng không xuất ra dữ liệu.
* **Nguyên nhân**: Trong dữ liệu TripAdvisor thô, trường `review_count` có dạng chuỗi kèm ngoặc đơn như `"(128)"` và các review ratings có dạng `"5 of 5 bubbles"`. Việc ép kiểu trực tiếp `int(review_count)` và `float(rating)` ném ra ngoại lệ `ValueError` khiến các bản ghi bị khối `try-except` bỏ qua âm thầm.
* **Giải pháp khắc phục**: Cập nhật hàm mapper của cả hai Job sử dụng Regular Expressions (`re`) để bóc tách phần số chính xác trước khi ép kiểu dữ liệu:
  * Trích xuất `review_count`: `re.sub(r'\D', '', review_count)`
  * Trích xuất `rating`: `re.search(r'(\d+(\.\d+)?)', rating)`
