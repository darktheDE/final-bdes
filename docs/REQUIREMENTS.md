# Toàn bộ yêu cầu đồ án môn học (Instructor Requirements)
## Môn học: Nhập môn Dữ liệu lớn (BDES333877) - Khoa CNTT - HCMUTE

Tài liệu này tổng hợp toàn bộ các yêu cầu bắt buộc và tiêu chí đánh giá từ giảng viên phụ trách dựa trên: Hướng dẫn thực hiện đồ án, Đề cương môn học và Bảng tự chấm điểm.

---

## 1. Hình thức thực hiện & Phân chia công việc

- **Quy mô nhóm**: Từ 03 – 05 sinh viên (Ưu tiên số lẻ). 
  - *Lưu ý nhóm hiện tại:* Nhóm đăng ký 4 người cần đảm bảo được GV đồng ý nếu có quy định khắt khe về số lẻ.
- **Quản lý mã nguồn**:
  - Lưu trữ toàn bộ source-code, tài liệu tham khảo lên **GitHub/GitLab**.
  - Giảng viên sẽ **đánh giá mức độ đóng góp cá nhân trực tiếp dựa trên lịch sử commit/submit code trên Git**.
- **Phân chia công việc**:
  - Phải phân công công việc rõ ràng giữa các thành viên.
  - *Ràng buộc:* Không tính thời gian làm báo cáo, làm slide, định dạng video hoặc các công việc không liên quan đến nội dung môn học vào bảng phân công khối lượng công việc chính thức.

---

## 2. Yêu cầu kỹ thuật & Môi trường cấu hình

### 2.1. Yêu cầu về môi trường phát triển (Mục 2.1 của HD)
- **Hệ điều hành**: **Ubuntu 24.04 LTS chạy trên WSL2** là môi trường đích chính thức. Việc chạy trên Linux/WSL2 giúp hệ thống tối ưu hóa hiệu năng I/O cho NameNode/DataNode và loại bỏ các lỗi phân quyền file trên Windows.
- **Tech Stack Phiên Bản LTS Khuyến Nghị**:
  - **Hadoop**: Apache Hadoop 3.3.6 LTS.
  - **Java**: OpenJDK 8 LTS (Bắt buộc dùng Java 8 vì Hive 3.1.3 không tương thích Java 11+ do lỗi Kryo serialization).
  - **MongoDB**: MongoDB Community Server 8.0 LTS (đáp ứng gói phân phối chính thức cho Ubuntu 24.04 LTS).
  - **MySQL**: MySQL Server 8.0 (CSDL quan hệ phục vụ SQL & CRUD).
  - **Python**: Python 3.10 / 3.11 (được cài đặt trong môi trường ảo `venv` để tránh xung đột loại bỏ `distutils` của Python 3.12 mặc định trên Ubuntu 24.04).
- **Minh chứng cấu hình (Bắt buộc ghi vào báo cáo)**: Sinh viên phải cung cấp chi tiết cấu hình máy tính cá nhân/máy ảo sử dụng bao gồm:
  - Loại máy tính.
  - Dung lượng RAM.
  - Thông số CPU (Số nhân, số luồng).
  - Phiên bản hệ điều hành WSL2 & Phiên bản ứng dụng cụ thể.

---

## 3. Nội dung thực hiện đồ án (Pipeline & Chức năng)

Để đạt điểm số tối đa (tối ưu hóa thang điểm), hệ thống phải đáp ứng đầy đủ các tiêu chuẩn chức năng sau:

### 3.1. Pipeline Dữ liệu (Dữ liệu & Lưu trữ - Max 1.75đ)
- [x] **Nguồn dữ liệu**: Thu thập dữ liệu theo chủ đề tự chọn từ **tối thiểu 2 nguồn khác nhau** (Đa dạng hóa nguồn). TripAdvisor (Scrape) + TheMealDB (REST API).
- [x] **Kích thước dữ liệu**: Tập dữ liệu thu thập phải đủ lớn, **tối thiểu trên 1000 records** (bản ghi).
- [x] **Làm sạch dữ liệu**: Tiến hành sửa chữa, loại bỏ dữ liệu không chính xác, định dạng sai, xử lý dữ liệu trùng lặp (duplicates), hoặc gán nhãn sai bằng Pandas.
- [x] **Staging DBMS**: Lưu trữ dữ liệu thu thập được vào MongoDB (`sentiment_db` NoSQL) và MySQL (`food_sentiment_db` Relational).
- [x] **Cấu trúc dữ liệu**: Tổ chức dữ liệu theo mô hình quan hệ (MySQL) và phi cấu trúc (MongoDB) song hành.
- [x] **Hadoop Integration**: Dữ liệu từ MySQL và MongoDB phải được đồng bộ trực tiếp lên hệ thống tệp phân tán Hadoop (HDFS) dưới dạng tệp JSON Lines (`.jsonl`).

### 3.2. Chức năng hệ thống (Max 4.00đ)
- [x] **Thao tác dữ liệu (CRUD)**: Hỗ trợ giao diện thực thi truy vấn (Query), thao tác dữ liệu cơ bản (Thêm, Đọc, Sửa, Xóa) trên giao diện tương tác trực tiếp với **MySQL** bằng SQL.
- [x] **Sao lưu & Phục hồi**: Triển khai tính năng sao lưu (Backup) và phục hồi (Restore) dữ liệu bằng script `db_backup.sh` / `db_restore.sh` cho cả MongoDB và MySQL.
- [x] **Trực quan hóa**: Vẽ biểu đồ hiển thị thông tin dữ liệu thu thập được (Yêu cầu: **Tối thiểu 5 biểu đồ** thuộc **ít nhất 3 loại biểu đồ khác nhau**).
- [x] **Công cụ Hadoop Ecosystem (Trong chương trình - Max 1.00đ)**: Cài đặt và sử dụng các công cụ thuộc hệ sinh thái Hadoop trong chương trình học (chọn tối đa 4 công cụ, 0.25đ/công cụ):
  1. **Apache HDFS** (Hệ thống file phân tán - 0.25đ)
  2. **Apache YARN** (Bộ quản lý tài nguyên - 0.25đ)
  3. **Apache MapReduce** (Bộ máy tính toán song song - 0.25đ)
  4. **Apache Hive** (Kho dữ liệu SQL phân tán - 0.25đ)
  5. **Apache Sqoop** (Đồng bộ dữ liệu RDBMS - HDFS - 0.25đ)
- [x] **Công cụ Hadoop Ecosystem / Apache (Ngoài chương trình - Max 1.00đ)**:
  * Không triển khai để đảm bảo pipeline tinh gọn, tránh dư thừa và phục vụ trực tiếp cho logic đồ án (0.00đ).
- [x] **Chương trình MapReduce (Max 2.00đ)**: Xây dựng và thực thi thành công **tối thiểu 8 chương trình MapReduce** trên Hadoop để phân tích dữ liệu (Tính điểm: 0.25đ / 1 chương trình MapReduce).

### 3.3. Giao diện người dùng (Max 1.00đ)
- [x] **Giao diện tương tác (GUI)**: Giao diện Web App Streamlit kết nối MySQL làm nghiệp vụ tác nghiệp (CRUD/SQL) và kết nối Hive/HDFS làm trực quan hóa báo cáo.

---

## 4. Yêu cầu về Báo cáo, Slides & Video

### 4.1. Quyển báo cáo đồ án (Max 0.75đ)
- Trình bày chi tiết từng bước quá trình cài đặt, cấu hình hệ thống trên môi trường Linux Ubuntu 24.04 WSL2 kèm hình ảnh minh chứng.
- **Bắt buộc:** Phải đính kèm **Bảng phân công công việc** cụ thể giữa các thành viên ở trang đầu của báo cáo.

### 4.2. Slides thuyết trình (Max 0.25đ)
- Slide tóm tắt từ **10 – 15 slides**.

### 4.3. Video demo đồ án (Max 1.00đ)
- Video HD có thuyết minh, phụ đề tiếng Việt, nhạc nền và webcam nhóm ở đầu video.