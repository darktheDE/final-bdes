# Nhật ký thực thi (Execution Log) - Cycle 5: DevOps, Backup & Resilience

**Ngày thực hiện:** 14/06/2026

## 1. Các hạng mục đã triển khai

Chúng tôi đã thiết lập thành công và kiểm thử hệ thống sao lưu/phục hồi tự động cho cơ sở dữ liệu cùng với bộ kiểm tra trạng thái dịch vụ (Port & Service Checks) tích hợp trong kịch bản khởi chạy hệ thống trên môi trường Ubuntu 24.04 LTS (WSL2).

### Các hạng mục chính trong Cycle 5:
1. **Automate Backup (`db_backup.sh`)**:
   - Sử dụng `mysqldump` để sao lưu toàn bộ cấu trúc và dữ liệu của cơ sở dữ liệu quan hệ MySQL `food_sentiment_db`.
   - Sử dụng `mongodump` để sao lưu các collections của cơ sở dữ liệu NoSQL MongoDB `sentiment_db`.
   - Lưu trữ các bản sao lưu vào thư mục có gán nhãn thời gian (`data/backups/backup_YYYYMMDD_HHMMSS/`) tại thư mục gốc dự án.
2. **Automate Restore (`db_restore.sh`)**:
   - Tự động kiểm tra và nhập tệp tin backup đã chỉ định.
   - Sử dụng `mysql` client để phục hồi dữ liệu MySQL.
   - Sử dụng `mongorestore` với cờ `--drop` để xóa sạch dữ liệu hiện tại trước khi khôi phục dữ liệu MongoDB để tránh trùng lặp.
3. **Port & Service Checks (`bin/run.sh`)**:
   - Tích hợp hàm kiểm tra socket trạng thái cổng mạng (`ss -tln` hoặc `netstat`) để phát hiện các cổng dịch vụ có đang chạy hay không.
   - Tự động chạy daemon cho MySQL (`sudo service mysql start`), MongoDB (`sudo service mongod start`), Hadoop DFS (`start-dfs.sh`) và Hadoop YARN (`start-yarn.sh`) nếu phát hiện cổng tương ứng chưa hoạt động.

---

## 2. Các tệp tin được tạo mới và cập nhật

- [src/backup/db_backup.sh](../../src/backup/db_backup.sh) (Đã kiểm tra)
- [src/backup/db_restore.sh](../../src/backup/db_restore.sh) (Đã kiểm tra)
- [bin/run.sh](../../bin/run.sh) (Đã tích hợp Port Checks và tự động kích hoạt dịch vụ)
- [.gitignore](../../.gitignore) (Cập nhật để bỏ qua thư mục `data/backups/`, `data/db/`, `data/hdfs/`, `data/raw/` và `tmp-pandas/`)

---

## 3. Quy trình Triển khai & Kiểm thử (WSL2 Ubuntu)

### Bước 3.1: Kiểm tra Port & Service Auto-Start
Khi chạy kịch bản khởi tạo hệ thống `./bin/run.sh`:
1. Kịch bản xuất ra các bước kiểm tra cổng:
   - Cổng `3306` cho MySQL
   - Cổng `27017` cho MongoDB
   - Cổng `9000` cho HDFS NameNode
   - Cổng `8088` cho YARN ResourceManager
2. Nếu dịch vụ chưa chạy, kịch bản tự động thực thi các lệnh kích hoạt (qua `sudo service` hoặc `start-dfs.sh` / `start-yarn.sh`).

### Bước 3.2: Thực hiện Sao lưu (Backup)
Chạy script sao lưu dữ liệu:
```bash
bash src/backup/db_backup.sh
```
**Kết quả đầu ra:**
- Tạo thành công thư mục backup ví dụ: `data/backups/backup_20260614_072428/`
- Chứa file `mysql_backup.sql` và thư mục `mongo_backup/` chứa cơ sở dữ liệu `sentiment_db`.

### Bước 3.3: Thực hiện Khôi phục (Restore)
Chạy script phục hồi dữ liệu từ thư mục sao lưu đã tạo:
```bash
bash src/backup/db_restore.sh backup_20260614_072428
```
**Kết quả đầu ra:**
- Kiểm tra sự tồn tại của tệp tin.
- Thực hiện khôi phục MySQL và MongoDB thành công mà không gây xung đột hoặc trùng lặp bản ghi nhờ cơ chế `--drop` trong `mongorestore`.

---

## 4. Nhật ký xử lý sự cố trong Cycle 5

### Sự cố 5.1: Quyền truy cập thư mục backup khi lưu trong phân vùng Windows share
- **Triệu chứng**: Gặp lỗi `Permission denied` hoặc `Operation not permitted` khi `mongodump` ghi trực tiếp file vào `data/backups/` nếu phân vùng NTFS được gắn kết không hỗ trợ đầy đủ quyền Linux POSIX.
- **Giải pháp**: Đảm bảo thư mục backups nằm hoàn toàn trong không gian thư mục dự án của người dùng hiện tại và phân quyền ghi phù hợp (`chmod -R 755 data/backups/`), đồng thời thêm thư mục này vào `.gitignore` để tránh đẩy hàng GB dữ liệu sao lưu lên GitHub.
