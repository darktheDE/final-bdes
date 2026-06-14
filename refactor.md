Hãy đọc dự án này, nắm chắc những tài liệu quan trọng. Những tài liệu dự án có thể bị sai và ta sẽ cập nhật lại, kể cả GEMINI.md hay README.md.
Bây giờ ta đến giai đoạn test, refactor toàn bộ pipeline dự án.
Một số vấn đề khi tôi manual check được như sau. Bạn cần đánh order list thứ tự triển khai.:
Vấn đề dẫn đến lỗi dưới đây là do cố định các trường dữ liệu, quyết định lựa chọn các mapreduce, quyết định plot để vẽ trước cả khi được cào. Do đó dữ liệu được cào thực tế so với schema dự đoán bị sai lệnh. Schema json của dữ liệu được cào là cố định, kèm với data cào được của themealapi. Do đó ta sẽ cập nhật, loại bỏ, chỉnh sửa job map re và plot sao cho phù hợp với data cào được. Điều này có thể dẫn đến cập nhật schema của hive, mysql. Kèm với đó, tôi chưa thấy được sự liên quan giữa data cào được của tripadvisor và themealapi. Hãy làm rõ.
Đây là data mẫu cào được của tripadvior:
{"_id": "https://www.tripadvisor.com/Restaurant_Review-g293925-d33215720-Reviews-Bun_Ch_Ha_Thanh_by_Hanoi_Corner-Ho_Chi_Minh_City.html", "name": "Bún Chả Hà Thành by Hanoi Corner", "rating": 5.0, "review_count": "(112)", "address": "18B/17 Đ. Nguyễn Thị Minh Khai Quận 1, Ho Chi Minh City 70000 Vietnam", "district": "18B/17 Đ. Nguyễn Thị Minh Khai Quận 1", "city": "Ho Chi Minh City 70000 Vietnam", "reviews": [{"user": "Chloe C", "rating": "5 of 5 bubbles", "comment": "Excellent food with friendly service by Ly. I highly recommend the Bun Cha and the flan 👏"}, {"user": "Fearless40327046190", "rating": "5 of 5 bubbles", "comment": "Good and good food will come back."}, ....
- Bổ sung incremental load cho data ở streamlit
- Bổ sung field query cho CRUD.
+ View hiện tại: Search by Name or District. Bổ sung cho tìm bằng ID.
+ Update chỉ cho update new rating, cho phép bổ sung thêm các field khác.
+ Bổ sung phân trang khi query
- Chỉnh sửa lại logic backup xem việc backup có diễn ra thành công hay không đường dẫn file có vẻ không override được, nếu backup lần 2 thì ứng dụng hiện tại tạo folder có tên là ký tự bị lỗi.
- Thêm summary hay plot cho mỗi job map re. Chỉ output ra log và kết quả map re thì không có ý nghĩa.
- Field data bị dư, không có field nào là price_range.
- kiểm tra lại mapre có ý nghĩa so với data thực tế.
- 1 số file tạo mới như file conf hay 1 số file .md, .py ở root project. Cần có cấu trúc folder hoàn chỉnh.
- Lên kế hoạch dọn dẹp những file không cần thiết. Tôi sẽ là người tự xóa.
- Phần Big Data Report của streamlit vẫn còn đang dùng mockup data. Xóa toàn bộ các hàm mockup data.
Mục tiêu cuối cùng mà tôi mong muốn bao gồm:
- Người dùng sẽ tự trang bị WSL2 Windows với Ubuntu, tự pull repo này về và mở trong môi trường Ubuntu WSL2. Chạy lần lượt 3 script trong folder bin/
1. install_infra.sh Ta không biết là người dùng đã có sẵn các infra tech như Java, Python, Hadoop, Mongo, MySQL, .... nói chung toàn bộ tech stack phục vụ cho dự án này. Script cần kiểm tra xem tech đó có trong máy hay chưa, lưu ý cần đúng chính xác tuyệt đối phiên bản mà dự án yêu cầu. Nếu khác phiên bản, nếu chưa có thì thực hiện việc download, config, test xem tech đó hoạt động được chưa. Tôi yêu cầu bạn cập nhật lại file infra, đầy đủ và chính xác quy trình cũng như các tech stack của dự án. Các file config như các file .xml thì nên viết ra từng file riêng và để vào 1 folder chung. Không viết trực tiếp trong file .sh đó. Trong quá trình thực hiện dự án, tôi gặp kha khá lỗi phải chỉnh sửa, bổ sung nội dung các file cấu hình đó (trong folder process có lưu lại quá trình debug). Vì vậy bạn cần truy cập vào WSL2 của tôi để lấy chi tiết nội dung các file config hiện tại.
2. setup.sh tôi không rõ vai trò của file này có khác gì với file install_infra.sh hay không, nếu được thì nên gộp chung, dù gì thì khi cấu hình môi trường ta cũng chỉ mong muốn chạy 1 lần duy nhất. Nên nếu cần chạy lại nhiều lần như run.sh thì giữ, không thì gộp chung với infra. Trong file này đang dùng jdk-11. Tôi muốn dự án chỉ dùng jdk-8
3. run.sh là file chạy full pipeline, môi trường, dịch vụ trong trường hợp đã có đầy đủ tech stack, môi trường phù hợp. Bạn có thể kiểm tra version thêm lần nữa ở đây trong trường hợp không phù hợp với tech stack dự án yêu cầu thì yêu cầu chạy install_infra.sh. Sau khi chạy thì người dùng được truy cập trực tiếp localhost:8501 để sử dụng web. Nên bổ sung tham số -data để có thể thực hiện cào data để nạp vào các storage. Nếu không thì mặc định các storage đã có data và chỉ cần chạy dịch vụ phục vụ cho nghiệp vụ oltp olap ở streamlit.
4. stop.sh là file tắt hết toàn bộ dịch vụ. nên có thêm tham số: -backup nếu muốn thực hiện backup toàn bộ data trước khi tắt, -cleandata để clean toàn bộ data của toàn bộ storage, cho mục đích demo full pipeline.
Tôi mong muốn bạn lên kế hoạch refactor chi tiết, phân ra theo module refactor rõ ràng. Sau mỗi module tôi sẽ được manual test. Nếu pass tôi sẽ clear context (tạo 1 chat mới) để refactor module tiếp theo.
Việc lên kế hoạch refactor nên được diễn ra như pipeline của dự án.
Folder /process/ chứa toàn bộ quá trình thực hiện task trong masterplan.md, bao gồm cả những hoạt động debug. Cần theo dõi những process liên quan khi thực hiện refactor. Kể cả việc refactor cũng cần lưu docs process lại.
Các docs của dự án có thể đang không đúng với triển khai thực tế. Bạn chỉ nên tham khảo, không nên tin đó là source of truth, kể cả GEMINI.md. Vì vậy, thứ đầu tiên refactor chính là những docs liên quan mà bị sai.