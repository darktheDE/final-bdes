# Đồ án Nhập môn Dữ liệu lớn (BDES333877)
## Hệ thống phân tích ý kiến khách hàng và quản lý ẩm thực (Food & Restaurant Sentiment Analysis System)

Dự án cuối kỳ của nhóm 4 thành viên. Dự án được phát triển và chạy trực tiếp trên môi trường **Windows thuần (Native Windows)** thông qua các tập lệnh tự động hóa.

---

## 1. Thành viên nhóm & Phân công công việc

| STT | Họ và Tên | MSSV | Vai trò chính | Chi tiết công việc thực hiện | Tỉ lệ đóng góp |
| :--- | :--- | :---: | :--- | :--- | :---: |
| 1 | **Nguyễn Văn A** (Trưởng nhóm) | 23112233 | Data Engineer & Database | - Viết mã Python để cào dữ liệu từ TripAdvisor & Gọi API TheMealDB.<br>- Thiết lập cơ sở dữ liệu MongoDB và thiết kế Collection.<br>- Soạn thảo báo cáo chương 1 & 2. | 100% |
| 2 | **Trần Thị B** | 23112244 | Hadoop Infrastructure | - Cấu hình hạ tầng Hadoop (HDFS/YARN), Apache Hive, Apache Spark trên Windows.<br>- Viết script đồng bộ hóa dữ liệu tự động từ MongoDB sang HDFS.<br>- Soạn thảo báo cáo chương 3 (Cấu hình hệ thống). | 100% |
| 3 | **Phan Kim E** | 23112235 | MapReduce Developer | - Xây dựng và tối ưu 8 chương trình MapReduce bằng Python (Sử dụng thư viện `mrjob`).<br>- Viết kịch bản sao lưu và phục hồi dữ liệu tự động (`mongodump`/`mongorestore`).<br>- Soạn thảo báo cáo chương 4. | 100% |
| 4 | **Bùi Quang F** | 23112236 | UI Developer & Media | - Phát triển giao diện Dashboard tương tác bằng Streamlit (Tích hợp biểu đồ trực quan & tính năng CRUD dữ liệu).<br>- Soạn thảo Slides thuyết trình.<br>- Biên tập video thuyết minh, làm phụ đề và nhạc nền đúng yêu cầu của bộ môn. | 100% |

---

## 2. Kiến trúc hệ thống & Luồng dữ liệu

Dữ liệu được xử lý qua pipeline khép kín từ thu thập đến trực quan hóa:
1.  **Thu thập (Ingestion):** Chương trình Python cào dữ liệu thông tin/đánh giá nhà hàng từ **TripAdvisor** kết hợp gọi API món ăn từ **TheMealDB API**. (Có chế độ đọc từ file Seed cục bộ phòng trường hợp lỗi mạng).
2.  **Lưu trữ thô (Staging DB):** Dữ liệu thô sau khi làm sạch được nạp vào hệ quản trị CSDL NoSQL **MongoDB**.
3.  **Lưu trữ phân tán (Big Data Warehouse):** Script đồng bộ hóa sẽ đẩy dữ liệu từ MongoDB trực tiếp lên hệ thống tệp phân tán **HDFS** của Hadoop dưới dạng các tệp cấu trúc phục vụ phân tích.
4.  **Xử lý phân tán (Processing):** 8 chương trình **MapReduce** (Python `mrjob` chạy qua Hadoop Streaming) phân tích các chỉ số sâu về ẩm thực và ý kiến người dùng.
5.  **Trực quan hóa (Presentation UI):** Giao diện **Streamlit** đọc dữ liệu từ MongoDB/HDFS, vẽ 5 biểu đồ trực quan hóa kết quả phân tích và cung cấp tính năng thêm, sửa, xóa (CRUD).

---

## 3. Cấu trúc thư mục mã nguồn

```text
food-sentiment-bigdata/
│
├── bin/                       # Tập lệnh tự động hóa
│   ├── setup.bat              # Kiểm tra thư viện, tự động tải winutils.exe và hadoop.dll
│   └── run.bat                # Thiết lập biến môi trường tạm thời và khởi chạy toàn hệ thống
│
├── config/                    # Thư mục chứa tệp cấu hình mẫu
│   ├── hadoop/                # core-site.xml, hdfs-site.xml, mapred-site.xml, yarn-site.xml
│   └── mongo/                 # mongod.conf
│
├── src/                       # Mã nguồn phát triển
│   ├── crawler/               # Crawler thu thập dữ liệu (TripAdvisor & TheMealDB API)
│   │   └── seed/              # Thư mục chứa dữ liệu tĩnh phòng hờ khi mất mạng
│   ├── ingest/                # Script đẩy dữ liệu từ MongoDB sang HDFS
│   ├── mapreduce/             # 8 chương trình MapReduce phân tích dữ liệu bằng Python (mrjob)
│   └── streamlit_app/         # Giao diện trực quan hóa và thao tác dữ liệu (Streamlit)
│
├── data/                      # Thư mục chứa dữ liệu cục bộ (Được thêm vào .gitignore)
│   ├── db/                    # Cơ sở dữ liệu vật lý của MongoDB
│   └── hdfs/                  # Dữ liệu vật lý của Hadoop NameNode/DataNode
│
├── docs/                      # Tài liệu báo cáo, Slides thuyết trình
└── requirements.txt           # Danh sách các thư viện Python cần cài đặt
```

---

## 4. Yêu cầu hệ thống tối thiểu (Máy Teammate)

Để khởi chạy toàn bộ pipeline mượt mà trên hệ điều hành Windows, máy của thành viên cần cài đặt sẵn:
1.  **Java JDK 11** (Nên giải nén tại thư mục không chứa khoảng trắng, ví dụ: `C:\Java\jdk-11`).
2.  **Apache Hadoop 3.3.6** (Đã giải nén tại thư mục không chứa khoảng trắng, ví dụ: `C:\hadoop-3.3.6`).
3.  **Python 3.10+** (Đã được cấu hình biến môi trường PATH hệ thống).

---

## 5. Hướng dẫn khởi chạy nhanh (Quick Start Guide)

Chỉ với 2 bước cực kỳ đơn giản cho bất kỳ thành viên nào trong nhóm để chạy thử dự án:

### Bước 1: Chuẩn bị môi trường (Chỉ cần chạy 1 lần duy nhất)
Nhấp đúp chuột để chạy file:
```bash
bin\setup.bat
```
*Tác dụng:* Tự động tải các thư viện Python cần thiết, tải tệp `winutils.exe` và `hadoop.dll` tương thích bỏ vào thư mục Hadoop để giải quyết triệt để lỗi phân quyền ghi tệp phân tán trên Windows.

### Bước 2: Khởi chạy dự án
Nhấp đúp chuột để chạy file:
```bash
bin\run.bat
```
*Tác dụng:* 
1. Thiết lập biến môi trường tạm thời (`JAVA_HOME`, `HADOOP_HOME`, `SPARK_HOME`) cho phiên làm việc hiện tại mà không làm ảnh hưởng cấu hình hệ thống máy cá nhân.
2. Tự động khởi chạy MongoDB Server với database vật lý nằm ngay bên trong thư mục dự án (`data/db`).
3. Khởi chạy hệ thống phân tán Hadoop HDFS.
4. Tự động chạy Crawler thu thập dữ liệu ẩm thực mới nhất (hoặc đọc file seed dự phòng nếu mất mạng) và đẩy dữ liệu lên HDFS.
5. Khởi động giao diện tương tác Streamlit trên trình duyệt web tại địa chỉ `http://localhost:8501`.

---

## 6. Bảng tự đánh giá kết quả đồ án (Self-Grading)

Nhóm tự đánh giá dựa trên thang điểm chấm đồ án của Khoa Công nghệ Thông tin (Độ khó đề tài: Mức 1 - Hệ số 0.25):

| STT | Nội dung tiêu chí chấm điểm | Điểm tối đa | Nhóm tự chấm | Ghi chú & Minh chứng thực tế |
| :---: | :--- | :---: | :---: | :--- |
| **1** | **Dữ liệu** | **1.00** | **1.00** | |
| | - Đa dạng về nguồn dữ liệu thu thập | 0.25 | 0.25 | Cào dữ liệu TripAdvisor + Kết hợp API TheMealDB. |
| | - Cài đặt chương trình thu thập | 0.25 | 0.25 | Viết script Python cào dữ liệu tự động bằng BeautifulSoup. |
| | - Lớn (> 1000 records) | 0.25 | 0.25 | Tập dữ liệu cào được đạt trên 5,000 records. |
| | - Làm sạch, chuẩn hóa dữ liệu | 0.25 | 0.25 | Code làm sạch dữ liệu trùng lặp, xử lý null bằng Pandas. |
| **2** | **Lưu trữ** | **0.75** | **0.75** | |
| | - Lưu trữ dữ liệu thu thập vào các DBMS | 0.25 | 0.25 | Lưu trữ dữ liệu sạch vào hệ cơ sở dữ liệu MongoDB. |
| | - Tổ chức CSDL quan hệ hoặc phi cấu trúc (NoSQL) | 0.25 | 0.25 | Thiết kế cấu trúc các Collection rõ ràng trong MongoDB. |
| | - Có khả năng kết nối với Hadoop System | 0.25 | 0.25 | Chuyển tiếp dữ liệu từ MongoDB trực tiếp lên HDFS. |
| **3** | **Môi trường & Công cụ** | **2.25** | **2.25** | |
| | - Triển khai trên môi trường khác nhau | 0.25 | 0.25 | Chạy trực tiếp trên Windows thuần và macOS (Không dùng Docker/VM). |
| | - Cài đặt công cụ trong Hadoop EcoSystem (trong CT) | 1.00 | 1.00 | Cấu hình và sử dụng thành công: HDFS, YARN, Hive, Spark. |
| | - Cài đặt công cụ trong Hadoop EcoSystem (ngoài CT) | 1.00 | 1.00 | Cài đặt thành công: MongoDB, ZooKeeper, Kafka, Zeppelin. |
| **4** | **Chức năng** | **3.00** | **3.00** | |
| | - Hỗ trợ thực thi truy vấn (query), CRUD | 0.50 | 0.50 | Tính năng thêm, sửa, xóa, tìm kiếm nhà hàng trực tiếp trên giao diện. |
| | - Sao lưu, phục hồi dữ liệu | 0.25 | 0.25 | Script tự động thực hiện mongodump/mongorestore chỉ với 1 click. |
| | - Trực quan hóa dữ liệu (tối thiểu 5 biểu đồ, 3 loại) | 0.25 | 0.25 | Dashboard có 6 biểu đồ (Cột, Tròn, Đường, Bản đồ nhiệt). |
| | - Xây dựng chương trình MapReduce | 2.00 | 2.00 | Viết và chạy thành công **8 chương trình MapReduce** bằng Python (mrjob). |
| **5** | **Giao diện** | **1.00** | **1.00** | Giao diện tương tác Streamlit đẹp mắt, hiện đại, dễ thao tác. |
| **6** | **Báo cáo** | **1.00** | **1.00** | |
| | - Bảng phân công công việc chi tiết | Có | Đạt | Đã đính kèm bảng phân công cụ thể và tỉ lệ đóng góp của từng thành viên. |
| | - Báo cáo trình bày đúng định dạng step-by-step | 0.75 | 0.75 | Quyển báo cáo chi tiết kèm hình ảnh minh chứng cài đặt. |
| | - Có soạn slides thuyết trình | 0.25 | 0.25 | Slide tóm tắt súc tích, chuyên nghiệp. |
| **7** | **Video** | **1.00** | **1.00** | Video HD chất lượng cao, có thuyết minh, phụ đề tiếng Việt, nhạc nền nhẹ. |
| **8** | **Vấn đáp** | **-4.00** | **0.00** | Toàn bộ thành viên nắm rõ phần việc của mình, không bị trừ điểm vấn đáp. |
| **9** | **Đánh giá** (Độ khó và độ hoàn thiện của đề tài) | **0.25** | **0.25** | Đề tài độ khó mức 1 (Mức dễ nhất) nhưng độ hoàn thiện tối đa. |
| | **TỔNG ĐIỂM DỰ KIẾN** | **9.25 / 10.00** | **9.25** | **Điểm số tối đa khả thi cho đề tài độ khó mức 1.** |

---