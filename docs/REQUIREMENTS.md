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
  - **Java**: OpenJDK 11 LTS (để Hadoop runtime tương thích tốt nhất).
  - **MongoDB**: MongoDB Community Server 8.0 LTS (đáp ứng gói phân phối chính thức cho Ubuntu 24.04 LTS).
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
- [x] **Staging DBMS**: Lưu trữ dữ liệu thu thập được vào MongoDB (`sentiment_db`).
- [x] **Cấu trúc dữ liệu**: Tổ chức dữ liệu theo mô hình phi cấu trúc (NoSQL Document Store).
- [ ] **Hadoop Integration**: Dữ liệu từ MongoDB phải được đồng bộ trực tiếp lên hệ thống tệp phân tán Hadoop (HDFS) dưới dạng tệp JSON Lines (`.jsonl`).

### 3.2. Chức năng hệ thống (Max 4.00đ)
- [ ] **Thao tác dữ liệu (CRUD)**: Hỗ trợ giao diện thực thi truy vấn (Query), thao tác dữ liệu cơ bản (Thêm, Đọc, Sửa, Xóa) trên giao diện.
- [ ] **Sao lưu & Phục hồi**: Triển khai tính năng sao lưu (Backup) và phục hồi (Restore) dữ liệu bằng script `db_backup.sh` / `db_restore.sh`.
- [ ] **Trực quan hóa**: Vẽ biểu đồ hiển thị thông tin dữ liệu thu thập được (Yêu cầu: **Tối thiểu 5 biểu đồ** thuộc **ít nhất 3 loại biểu đồ khác nhau**).
- [ ] **Công cụ Hadoop Ecosystem (Trong chương trình - Max 1.00đ)**: Cài đặt và sử dụng các công cụ thuộc hệ sinh thái Hadoop (HDFS, YARN, MapReduce).
- [ ] **Công cụ Hadoop Ecosystem (Ngoài chương trình - Max 1.00đ)**: Cài đặt và sử dụng các công cụ bổ trợ ngoài chương trình học (MongoDB 8.0 LTS).
- [ ] **Chương trình MapReduce (Max 2.00đ)**: Xây dựng và thực thi thành công **tối thiểu 8 chương trình MapReduce** trên Hadoop để phân tích dữ liệu (Tính điểm: 0.25đ / 1 chương trình MapReduce).

### 3.3. Giao diện người dùng (Max 1.00đ)
- [ ] **Giao diện tương tác (GUI)**: Hệ thống phải có giao diện đồ họa tương tác (như Web App Streamlit) để người dùng dễ dàng thao tác.

---

## 4. Yêu cầu về Báo cáo, Slides & Video

### 4.1. Quyển báo cáo đồ án (Max 0.75đ)
- Phải trình bày chi tiết từng bước (step-by-step) quá trình cài đặt, cấu hình hệ thống trên môi trường Linux Ubuntu 24.04 WSL2 kèm hình ảnh minh chứng rõ ràng.
- Định dạng trình bày đúng theo mẫu quy định của Khoa Công nghệ Thông tin.
- **Bắt buộc:** Phải đính kèm **Bảng phân công công việc** cụ thể giữa các thành viên ở trang đầu của báo cáo (Nếu thiếu mục này sẽ bị **trừ trực tiếp 1.00đ** vào điểm báo cáo).

### 4.2. Slides thuyết trình (Max 0.25đ)
- Soạn slide tóm tắt súc tích nội dung tìm hiểu và kết quả đạt được.
- Dung lượng slide khuyến nghị từ **10 – 15 slides**.

### 4.3. Video demo đồ án (Max 1.00đ)
Để đạt điểm tối đa cho phần video, video nộp bài phải đáp ứng đầy đủ các tiêu chí kiểm tra sau:
- [ ] Giới thiệu đầy đủ: Tên đồ án, nhóm thực hiện, GV hướng dẫn, mục lục nội dung và lời cảm ơn.
- [ ] **Có logo trường, khoa trực thuộc và khoa CNTT đính kèm xuyên suốt toàn bộ thời lượng video.**
- [ ] Có thuyết minh (giọng nói) giải thích rõ ràng.
- [ ] Có phụ đề (subtitle) tiếng Việt.
- [ ] Có nhạc nền (background music) nhẹ nhàng xuyên suốt video.
- [ ] Video chất lượng cao (HD/Full HD), hình ảnh rõ nét, không bị nhòe.
- [ ] Kịch bản video chạy demo đầy đủ các chức năng đã triển khai của hệ thống.
- [ ] **Có hoạt cảnh xuất hiện (hình ảnh/webcam) của các thành viên trong nhóm trình bày về đồ án ở đầu video.**

---

## 5. Tiến độ thực hiện & Định dạng nộp bài

### 5.1. Tiến độ
- **Báo cáo tiến độ**: Tuần 14 – 15.
- **Nộp báo cáo đồ án bản mềm**: Tuần 16.

### 5.2. Cấu trúc thư mục nộp bài (Bắt buộc)
Thư mục nộp bài phải được nén dưới định dạng `.zip` và đặt tên theo cấu trúc:
` <Mã lớp>_<STT nhóm>_<Tên đề tài>`

Cấu trúc tổ chức bên trong thư mục như sau:
-  `/source-code`: Chứa toàn bộ mã nguồn của chương trình mà nhóm đã phát triển.
-  `/reports`: Chứa quyển báo cáo (`.docx` và `.pdf`), slides thuyết trình, bảng tự chấm điểm, bảng phân công công việc và tệp video demo (nếu có dung lượng nhẹ).
-  `/dataset`: Chứa toàn bộ file dữ liệu thô và sạch được sử dụng trong chương trình.
-  `/refs`: Chứa danh sách các tài liệu tham khảo dưới dạng tệp hoặc liên kết.
-  `/libs`: Chứa danh sách các phần mềm, thư viện đặc thù có liên quan (nếu có).
-  **Tập tin `readme.txt`**: Nằm ở thư mục gốc, chứa thông tin có cấu trúc bắt buộc.