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
  - *Ràng buộc:* Không tính thời gian làm báo cáo, làm slide, định dạng video hoặc các công việc không liên quan đến nội dung môn học vào bảng phân chia khối lượng công việc chính thức.

---

## 2. Yêu cầu kỹ thuật & Môi trường cấu hình

### 2.1. Yêu cầu về môi trường phát triển (Mục 2.1 của HD)
- **Hệ điều hành**: Ubuntu Server (phiên bản mới nhất) hoặc cài đặt trực tiếp trên các môi trường khác nhau (Windows, macOS) để chứng minh tính tương thích đa nền tảng.
- **Công cụ cốt lõi**:
  - Apache Hadoop (phiên bản tương thích).
  - Các công cụ trong Hadoop EcoSystem kèm phiên bản tương thích được sử dụng.
- **Minh chứng cấu hình (Bắt buộc ghi vào báo cáo)**: Sinh viên phải cung cấp chi tiết cấu hình máy tính cá nhân/máy ảo sử dụng bao gồm:
  - Loại máy tính.
  - Dung lượng RAM.
  - Thông số CPU (Số nhân, số luồng).
  - Thông số GPU (nếu có).
  - Phiên bản hệ điều hành & Phiên bản ứng dụng cụ thể.

---

## 3. Nội dung thực hiện đồ án (Pipeline & Chức năng)

Để đạt điểm số tối đa (tối ưu hóa thang điểm), hệ thống phải đáp ứng đầy đủ các tiêu chuẩn chức năng sau:

### 3.1. Pipeline Dữ liệu (Dữ liệu & Lưu trữ - Max 1.75đ)
- [ ] **Nguồn dữ liệu**: Thu thập dữ liệu theo chủ đề tự chọn từ **tối thiểu 2 nguồn khác nhau** (Đa dạng hóa nguồn). Phương pháp thu thập có thể là thủ công (Manual), tự động (Crawl/API) hoặc cả hai.
- [ ] **Kích thước dữ liệu**: Tập dữ liệu thu thập phải đủ lớn, **tối thiểu trên 1000 records** (bản ghi).
- [ ] **Làm sạch dữ liệu**: Tiến hành sửa chữa, loại bỏ dữ liệu không chính xác, định dạng sai, xử lý dữ liệu trùng lặp (duplicates), hoặc gán nhãn sai.
- [ ] **Staging DBMS**: Lưu trữ dữ liệu thu thập được vào một hệ quản trị cơ sở dữ liệu (DBMS) tự chọn (ví dụ: MongoDB, MySQL, Cassandra...).
- [ ] **Cấu trúc dữ liệu**: Tổ chức dữ liệu theo mô hình quan hệ (SQL) hoặc phi cấu trúc (NoSQL).
- [ ] **Hadoop Integration**: Dữ liệu từ DBMS phải có khả năng kết nối và đồng bộ trực tiếp với hệ thống tệp phân tán Hadoop (HDFS).

### 3.2. Chức năng hệ thống (Max 4.00đ)
- [ ] **Thao tác dữ liệu (CRUD)**: Hỗ trợ giao diện thực thi truy vấn (Query), thao tác dữ liệu cơ bản (Thêm, Đọc, Sửa, Xóa).
- [ ] **Sao lưu & Phục hồi**: Triển khai tính năng sao lưu (Backup) và phục hồi (Restore) dữ liệu của hệ thống.
- [ ] **Trực quan hóa**: Vẽ biểu đồ hiển thị thông tin dữ liệu thu thập được (Yêu cầu: **Tối thiểu 5 biểu đồ** thuộc **ít nhất 3 loại biểu đồ khác nhau**).
- [ ] **Công cụ Hadoop Ecosystem (Trong chương trình - Max 1.00đ)**: Cài đặt và sử dụng 4 công cụ thuộc hệ sinh thái Hadoop có trong chương trình học (HDFS, YARN, MapReduce, Hive, Spark...).
- [ ] **Công cụ Hadoop Ecosystem (Ngoài chương trình - Max 1.00đ)**: Cài đặt và sử dụng 4 công cụ bổ trợ ngoài chương trình học (MongoDB, ZooKeeper, Kafka, Zeppelin...).
- [ ] **Chương trình MapReduce (Max 2.00đ)**: Xây dựng và thực thi thành công **tối thiểu 8 chương trình MapReduce** trên Hadoop để phân tích dữ liệu (Tính điểm: 0.25đ / 1 chương trình MapReduce).

### 3.3. Giao diện người dùng (Max 1.00đ)
- [ ] **Giao diện tương tác (GUI)**: Hệ thống phải có giao diện đồ họa tương tác (như Web App Streamlit, Desktop App...) để người dùng dễ dàng thao tác, không chạy chay bằng dòng lệnh cmd.

---

## 4. Yêu cầu về Báo cáo, Slides & Video

### 4.1. Quyển báo cáo đồ án (Max 0.75đ)
- Phải trình bày chi tiết từng bước (step-by-step) quá trình cài đặt, cấu hình hệ thống kèm hình ảnh minh chứng rõ ràng.
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
- **Nộp báo cáo đồ án bản mềm**: Tuần 16 (Thời gian cụ thể bộ môn sẽ thông báo sau).

### 5.2. Cấu trúc thư mục nộp bài (Bắt buộc)
Thư mục nộp bài phải được nén dưới định dạng `.zip` và đặt tên theo cấu trúc:
` <Mã lớp>_<STT nhóm>_<Tên đề tài>`
*(Ví dụ: `06_01_NghienCuuXayDungHeThongABC.zip`)*

Cấu trúc tổ chức bên trong thư mục như sau:
-  `/source-code`: Chứa toàn bộ mã nguồn của chương trình mà nhóm đã phát triển.
-  `/reports`: Chứa quyển báo cáo (`.docx` và `.pdf`), slides thuyết trình, bảng tự chấm điểm, bảng phân công công việc và tệp video demo (nếu có dung lượng nhẹ).
-  `/dataset`: Chứa toàn bộ file dữ liệu thô và sạch được sử dụng trong chương trình.
-  `/refs`: Chứa danh sách các tài liệu tham khảo dưới dạng tệp hoặc liên kết.
-  `/libs`: Chứa danh sách các phần mềm, thư viện đặc thù có liên quan (nếu có).
-  **Tập tin `readme.txt`**: Nằm ở thư mục gốc, chứa thông tin có cấu trúc bắt buộc sau:
   ```text
   ----- Thông tin đề tài ---------------------
   STT: ...
   Tên đề tài: ...
   Lớp học phần: <mã_học_phần>_xx
   Năm học: HKx/20xx-20xx
   --------------------------------------------
   Thông tin nhóm
   1. Họ tên sinh viên trưởng nhóm (mã số sinh viên trưởng nhóm) – SĐT – Email cá nhân
   2. Họ tên sinh viên 2 (mã số sinh viên 2)
   3. Họ tên sinh viên 3 (mã số sinh viên 3)
   4. Họ tên sinh viên 4 (mã số sinh viên 4)
   ```

---

## 6. Đánh giá & Vấn đáp (Oral Defense)

- **Thuyết trình trước lớp**: Không bắt buộc, nhưng các nhóm đăng ký thuyết trình trước lớp sẽ được ưu tiên cộng điểm khuyến khích.
- **Vấn đáp cá nhân (Bắt buộc)**:
  - Từng thành viên trong nhóm phải tham gia vấn đáp trực tiếp với giảng viên vào cuối kỳ.
  - Nội dung vấn đáp dựa trên **bảng phân công công việc, lịch sử commit trên GitHub và kiến thức lý thuyết/thực hành liên quan**.
  - *Hình phạt tối đa:* Trừ tối đa **4.00đ** vào tổng điểm nếu không trả lời được các câu hỏi vấn đáp hoặc không chứng minh được phần việc mình làm.
```