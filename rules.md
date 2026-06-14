tôi cần bạn lưu lại toàn bộ log làm việc, lưu lại toàn bộ file config xml, debug, .....
nói chung là lưu lại toàn bộ quá trình. Vừa hỗ trợ viết báo cáo vừa giúp chạy cài đặt hạ tầng trên máy khác đơn giản hơn.
lưu toàn bộ quá trình vào 1 file .sh 
tôi muốn bạn lưu lại toàn bộ quá trình chạy lệnh, toàn bộ file cấu hình xml trong quá trình cài đặt, viết task log, .... vì đây là yêu cầu của đồ án.
Nhớ đọc đầy đủ những tài liệu cần trước khi triển khai task

Đảm bảo:
- Khi đặt tên không chứa các tên định danh cá nhân, ví dụ tên tôi kienhung, vì đây là project nhóm, cần triển khai riêng lẻ cho nhiều máy chạy được pipeline.
- Viết quy trình chạy script sh chuẩn. Sau khi pull repo này về thì cần chạy step by step là gì, file sh nào. Đảm bảo việc chạy file sh cài hạ tầng trên 1 môi trường wsl2 ubuntu mới là thành công.

Test đảm bảo toàn bộ task thành công và có thể triển khai đơn lẻ trên 1 máy mới