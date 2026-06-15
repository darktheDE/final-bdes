# Ghi chú cuối dự án — Quy tắc làm việc nhóm
#
# 1. Lưu toàn bộ log làm việc, file config xml, debug vào docs/process/
# 2. Khi đặt tên không chứa định danh cá nhân (tên, username cá nhân).
#    Dùng generic names để pipeline chạy được trên nhiều máy độc lập.
# 3. Viết script .sh chuẩn:
#    - ./bin/install_infra.sh  (chạy 1 lần trên máy mới)
#    - ./bin/run.sh            (chạy pipeline)
#    - ./bin/stop.sh           (dừng dịch vụ)
# 4. Đảm bảo toàn bộ task có thể triển khai đơn lẻ trên WSL2 Ubuntu 24.04 mới.
# 5. Đọc đầy đủ tài liệu (docs/) trước khi triển khai task.
# 6. Sau mỗi task, cập nhật docs/process/ với log thực thi và kết quả.
