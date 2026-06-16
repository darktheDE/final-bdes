# Hướng Dẫn Cài Đặt và Khởi Chạy Hệ Thống (WSL2 Ubuntu 24.04 LTS)

Tài liệu này cung cấp hướng dẫn từng bước để cài đặt toàn bộ hạ tầng dữ liệu lớn (Hadoop, Hive, MySQL, MongoDB, Java, Python venv) và chạy pipeline thu thập/đồng bộ dữ liệu của dự án. Quy trình này được thiết kế hoàn toàn tổng quát (generic), không phụ thuộc vào bất kỳ tên người dùng hay đường dẫn cứng nào.

---

## 1. Yêu Cầu Hệ Thống & Chuẩn Bị

* **Hệ điều hành**: Ubuntu 24.04 LTS chạy trên WSL2 (Windows Subsystem for Linux).
* **Quyền hạn**: Tài khoản của bạn phải có quyền `sudo` để thực hiện cài đặt các gói hệ thống.
* **Mạng**: Đảm bảo kết nối internet ổn định để tải các gói phần mềm và các file cài đặt Hadoop/Hive (~1.3 GB tổng cộng).

---

## 2. Quy Trình Cài Đặt Từng Bước (Step-by-Step)

Sau khi pull repository này về máy, hãy mở terminal WSL2 Ubuntu và thực hiện tuần tự các bước sau:

### Bước 2.1: Phân quyền thực thi cho các script shell
Chạy lệnh sau tại thư mục gốc của dự án:
```bash
chmod +x bin/*.sh src/backup/*.sh
```

### Bước 2.2: Sửa lỗi ký tự xuống dòng (CRLF to LF)
Nếu bạn clone repo này trên Windows trước khi chạy trên WSL2, các file script có thể đã bị tự động chuyển đổi định dạng xuống dòng sang Windows (CRLF). Hãy chuyển đổi chúng về định dạng Linux (LF) bằng cách chạy lệnh:
```bash
sed -i 's/\r$//' bin/*.sh src/backup/*.sh
```

### Bước 2.3: Cài đặt và cấu hình Hạ tầng Dữ liệu lớn
Chạy script cài đặt toàn bộ hạ tầng (chỉ chạy 1 lần duy nhất trên máy mới):
```bash
./bin/install_infra.sh
```
**Script này sẽ tự động thực hiện:**
1. Cấu hình SSH Server và SSH passwordless localhost access (cần thiết cho Hadoop).
2. Cài đặt **OpenJDK 8 LTS** (bắt buộc cho Hadoop và Apache Hive 3.x).
3. Thêm các biến môi trường cần thiết (`JAVA_HOME`, `HADOOP_HOME`, `HIVE_HOME`, `PATH`) vào phần đầu của file `~/.bashrc`.
4. Cài đặt và cấu hình MySQL Server 8.0, tạo CSDL `food_sentiment_db` và `hive_metastore` kèm theo phân quyền.
5. Cài đặt MongoDB Community Server 8.0.
6. Cài đặt Python 3.10/3.11, tạo môi trường ảo `venv` và cài đặt các package trong `requirements.txt`.
7. Tải và giải nén Apache Hadoop 3.3.6, copy cấu hình từ `conf/hadoop/*.xml`, định dạng NameNode.
8. Tải và cấu hình Apache Hive 3.1.3, tải MySQL JDBC Connector, khắc phục lỗi thư viện Guava.

### Bước 2.4: Reload biến môi trường
Sau khi `install_infra.sh` hoàn thành, bạn **cần nạp lại (reload) biến môi trường** của terminal hiện tại để áp dụng các thay đổi:
```bash
source ~/.bashrc
```

### Bước 2.5: Nạp dữ liệu gốc vào hệ thống (Ingest Data)
Sau khi môi trường ảo `venv` và các dịch vụ nền đã sẵn sàng, hãy thực hiện phân quyền và chạy script nạp dữ liệu offline vào database:
```bash
chmod +x bin/ingest.sh
./bin/ingest.sh
```
Script này sẽ tự động kích hoạt `venv` và nạp dữ liệu sạch từ local vào MongoDB + khởi tạo MySQL Schema & di cư dữ liệu.

---

## 3. Khởi Chạy Toàn Bộ Hệ Thống (Run Pipeline)

Hệ thống đã được thiết kế tự động hóa hoàn toàn thông qua script `bin/run.sh`. Tùy thuộc vào nhu cầu, bạn có thể chạy với các tùy chọn (flags) sau:

### Lựa chọn 1: Chạy hệ thống với dữ liệu đã có sẵn (Nhanh nhất)
```bash
./bin/run.sh
```
Lệnh này sẽ khởi động các dịch vụ nền (Hadoop, MySQL, MongoDB) và mở Dashboard Streamlit.

### Lựa chọn 2: Thu thập dữ liệu mới & Đồng bộ HDFS
```bash
./bin/run.sh --crawl
```
Bổ sung thêm quá trình crawl dữ liệu từ API TheMealDB & TripAdvisor, sau đó chuẩn hóa vào MySQL/MongoDB, và đồng bộ `.jsonl` lên HDFS.

### Lựa chọn 3: Chạy toàn bộ luồng Pipeline & MapReduce Jobs (GIÀNH CHO CHẠY LẦN ĐẦU)
```bash
./bin/run.sh --crawl --jobs
```
Sẽ chạy đầy đủ quy trình: Khởi động dịch vụ -> Crawl dữ liệu mới -> Đồng bộ HDFS -> Thực thi toàn bộ **8 MapReduce Jobs** trên YARN -> Cập nhật Hive Views -> Mở Streamlit.

---

## 4. Giao diện Web Application (Streamlit)

Khi quá trình khởi chạy (run.sh) hoàn tất thành công, hệ thống sẽ in ra URL. Mở trình duyệt trên Windows host và truy cập:
👉 **[http://localhost:8501](http://localhost:8501)**
Nếu web app chưa chạy gì có thể chạy lệnh để khởi động thủ công. Tại folder dự án:
```bash
source venv/bin/activate
streamlit run src/streamlit_app/app.py
```
---

## 5. Danh Sách Giao Diện Web UI Để Giám Sát Hệ Thống

Để kiểm tra trạng thái hoạt động của các dịch vụ Hadoop, YARN và Streamlit, bạn có thể truy cập các URL dưới đây từ trình duyệt trên Windows (môi trường WSL2 sẽ tự động chuyển tiếp cổng sang localhost):

* 📊 **Streamlit Web Dashboard:** [http://localhost:8501](http://localhost:8501)
  *(Giao diện báo cáo phân tích trực quan)*
* 📁 **Hadoop HDFS NameNode Web UI:** [http://localhost:9870](http://localhost:9870)
  *(Xem cấu trúc file trên HDFS, dung lượng bộ nhớ, trạng thái của các DataNode)*
* ⚙️ **Hadoop YARN ResourceManager Web UI:** [http://localhost:8088](http://localhost:8088)
  *(Theo dõi các ứng dụng đang chạy, tiến trình chạy các Job MapReduce)*

---

## 6. Dừng Hệ Thống (Stop/Cleanup)

Để dừng an toàn các tiến trình Hadoop, YARN và các database daemon nhằm tiết kiệm RAM của máy chủ, sử dụng kịch bản sau:

```bash
./bin/stop.sh
```

**Các tuỳ chọn nâng cao:**
* Dừng hệ thống và tạo tệp tin **Backup** dữ liệu MySQL/MongoDB:
  ```bash
  ./bin/stop.sh --backup
  ```
* **Xóa hoàn toàn dữ liệu** (Wipe All Data) để reset hệ thống cho lần demo kế tiếp:
  ```bash
  ./bin/stop.sh --cleandata
  ```

---

## 7. Vận Hành Thủ Công (Manual Operations)

Nếu bạn muốn tự chạy từng bước thủ công của pipeline, khởi động dịch vụ riêng lẻ, backup/restore thủ công hoặc truy vấn trực tiếp MySQL, MongoDB, HDFS, Hive bằng CLI để làm nội dung viết báo cáo đồ án, vui lòng tham khảo hướng dẫn chi tiết tại:
👉 **[MANUAL_GUIDE.md](file:///d:/Project/final-bdes/MANUAL_GUIDE.md)**
