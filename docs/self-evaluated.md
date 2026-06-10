# BẢNG TỰ CHẤM & BẢNG PHÂN CÔNG ĐỒ ÁN
## ĐỒ ÁN NHẬP MÔN DỮ LIỆU LỚN (BDES333877) - KHOA CNTT - HCMUTE

---

## PHẦN 1: BẢNG TỰ CHẤM ĐIỂM CHI TIẾT

| STT | PHÂN LOẠI | NỘI DUNG TIÊU CHÍ | ĐIỂM MAX | NHÓM TỰ CHẤM | MINH CHỨNG THỰC TẾ & VAI TRÒ TRONG PIPELINE |
| :---: | :--- | :--- | :---: | :---: | :--- |
| **1** | **Dữ liệu** | Đa dạng về nguồn dữ liệu thu thập | 0.25 | **0.25** | Cào dữ liệu TripAdvisor (BeautifulSoup) và gọi API TheMealDB. |
| | | Cài đặt chương trình thu thập | 0.25 | **0.25** | Script `fetch_mealdb.py` và TripAdvisor spider tự động hóa. |
| | | Lớn (> 1000 records) | 0.25 | **0.25** | Dữ liệu đạt trên 1,300 nhà hàng và 40,000+ review. |
| | | Làm sạch, chuẩn hóa dữ liệu | 0.25 | **0.25** | Xử lý kiểu dữ liệu, loại bỏ trùng lặp, chuẩn hóa ratings bằng Pandas. |
| **2** | **Lưu trữ** | Lưu trữ dữ liệu thu thập vào các DBMS | 0.25 | **0.25** | Lưu trữ dữ liệu thô vào MongoDB và dữ liệu sạch vào MySQL. |
| | | Tổ chức CSDL quan hệ hoặc phi cấu trúc | 0.25 | **0.25** | **CSDL quan hệ:** MySQL (quản lý CRUD). **NoSQL:** MongoDB. |
| | | Có khả năng kết nối với Hadoop System | 0.25 | **0.25** | Sync dữ liệu từ MySQL/MongoDB lên HDFS dạng `.jsonl`. |
| **3** | **Môi trường** | Triển khai trên môi trường khác nhau | 0.25 | **0.25** | Chạy trên môi trường Ubuntu 24.04 LTS (WSL2) và macOS. |
| | **Hệ sinh thái** | Cài đặt công cụ Hadoop (trong CT) | 1.00 | **1.00** | Cài đặt và sử dụng: **HDFS, YARN, MapReduce, Apache Hive, Apache Sqoop**. |
| | | Cài đặt công cụ Hadoop (ngoài CT) | 1.00 | **0.00** | Không triển khai để đảm bảo pipeline tinh gọn, tối giản, tránh dư thừa. |
| **4** | **Chức năng** | Hỗ trợ thực thi truy vấn & CRUD | 0.50 | **0.50** | CRUD và thực thi truy vấn SQL trực tiếp trên MySQL từ Streamlit. |
| | | Sao lưu, phục hồi dữ liệu | 0.25 | **0.25** | Script bash `db_backup.sh` / `db_restore.sh` cho CSDL. |
| | | Trực quan hóa dữ liệu thu thập | 0.25 | **0.25** | Dashboard Streamlit chứa 6 biểu đồ trực quan (Plotly). |
| | | Xây dựng chương trình MapReduce | 2.00 | **2.00** | Viết và chạy thành công **8 chương trình MapReduce** bằng Python (`mrjob`). |
| **5** | **Giao diện** | Có hỗ trợ giao diện tương tác (GUI) | 1.00 | **1.00** | Giao diện Streamlit hiện đại, tương tác đầy đủ tính năng. |
| **6** | **Báo cáo** | Bảng phân công công việc chi tiết | -1.00 | **Đạt** | Đã đính kèm bảng phân công cụ thể từng thành viên ở trang đầu. |
| | | Báo cáo trình bày đúng định dạng | 0.75 | **0.75** | Quyển báo cáo step-by-step đầy đủ hình ảnh trên WSL2. |
| | | Có soạn slides thuyết trình | 0.25 | **0.25** | Slides tóm tắt súc tích, chuyên nghiệp. |
| **7** | **Video** | Theo đúng yêu cầu môn học | 1.00 | **1.00** | Video HD có thuyết minh, phụ đề, nhạc nền, logo và webcam nhóm. |
| **8** | **Vấn đáp** | Trả lời các yêu cầu từ GV | -4.00 | **Đạt** | Các thành viên nắm rõ phần việc của mình. |
| **9** | **Đánh giá** | Độ khó và độ hoàn thiện | 1.00 | **0.25** | Đề tài độ khó mức 1 (hệ số 0.25), hoàn thiện pipeline tối đa. |
| | | **TỔNG ĐIỂM DỰ KIẾN** | **10.00**| **8.50** | **Điểm số tối ưu, pipeline tinh gọn và thuyết phục.** |

---

## PHẦN 2: BẢNG PHÂN CÔNG CÔNG VIỆC NHÓM

| # | THÀNH VIÊN | VAI TRÒ CHÍNH | CÔNG VIỆC CHI TIẾT | % HOÀN THÀNH | KÝ TÊN |
| :---: | :--- | :--- | :--- | :---: | :---: |
| **1** | **Nguyễn Văn A** | Data Engineer & DB | - Viết crawler TripAdvisor & gọi API TheMealDB.<br>- Thiết lập MongoDB (Staging NoSQL) & MySQL (Relational DB). | 100% | |
| **2** | **Trần Thị B** | Hadoop Infrastructure | - Cấu hình Hadoop, YARN và Apache Hive trên WSL2.<br>- Thiết lập Apache Sqoop để đồng bộ hóa dữ liệu. | 100% | |
| **3** | **Phan Kim E** | MapReduce Developer | - Xây dựng và thực thi 8 chương trình MapReduce bằng Python (`mrjob`).<br>- Viết script backup/restore dữ liệu tự động. | 100% | |
| **4** | **Bùi Quang F** | UI & Media Creator | - Phát triển Dashboard Streamlit (CRUD, charts).<br>- Soạn Slide đề cương và làm video demo thuyết trình đúng chuẩn. | 100% | |

### CAM ĐOAN CỦA NHÓM
Chúng tôi xin cam đoan bảng phân công công việc trên đã được thống nhất thông qua giữa các thành viên và phân bổ khối lượng chính xác, đúng với tiến độ được đề cập trong tỷ lệ hoàn thành công việc.

*Tp. Hồ Chí Minh, ngày ....... tháng ....... năm .......*  
**(Trưởng nhóm ký, ghi rõ họ tên)**