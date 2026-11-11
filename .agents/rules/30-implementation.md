# 30 — Implementation tinh gọn (Clean Code, DRY, SOLID)

1. **Phạm vi & Context:** Xác nhận mục tiêu, allowed paths, branch và conventions đúng stack của dự án. Diff nhỏ nhất đáp ứng AC; không sửa unrelated code hay generated files ngoài quy trình.
2. **Clean Code:**
   - **Đặt tên rõ nghĩa:** Biến, hàm, class thể hiện rõ mục đích (intention-revealing); tránh viết tắt tối nghĩa hoặc tên chung chung.
   - **Hàm đơn nhiệm & ngắn gọn:** Mỗi hàm chỉ làm một việc duy nhất; giảm thiểu side-effects; ưu tiên guard clauses / early returns để tránh lồng ghép nhiều tầng (`if/else` sâu).
   - **Code tự tường minh (Self-documenting):** Code diễn đạt logic rõ ràng; chỉ comment để giải thích "tại sao" (quyết định kiến trúc, workaround edge case), không comment mô tả lại code "đang làm gì". Xóa dead code, debug log và code bị comment bỏ.
3. **DRY (Don't Repeat Yourself):**
   - Đóng gói và tái sử dụng logic nghiệp vụ dùng chung; tránh copy-paste cùng cấu trúc xử lý, validation hay magic numbers/strings (dùng hằng số/enum).
   - Tránh trừu tượng hóa vội vàng (Premature Abstraction): chỉ trừu tượng khi có sự trùng lặp thực sự về mặt nghiệp vụ; không ép gộp hai đoạn code giống nhau tình cờ nhưng khác lý do thay đổi.
4. **SOLID Principles:**
   - **Single Responsibility (SRP):** Mỗi class, module hoặc function chỉ giữ một trách nhiệm duy nhất và một lý do duy nhất để thay đổi.
   - **Open/Closed (OCP):** Thiết kế mở để mở rộng tính năng mới (qua polymorphism, strategy, abstraction) nhưng đóng đối với việc sửa đổi mã nguồn lõi đang ổn định.
   - **Liskov Substitution (LSP):** Lớp con/implementation phải thay thế hoàn toàn được lớp cha/interface mà không làm sai lệch hành vi hay phá vỡ tính đúng đắn của chương trình.
   - **Interface Segregation (ISP):** Ưu tiên các interface nhỏ, tập trung và chuyên biệt thay vì một interface cồng kềnh; client không bị ép phụ thuộc vào phương thức nó không dùng.
   - **Dependency Inversion (DIP):** Module cấp cao không phụ thuộc trực tiếp vào module cấp thấp; cả hai phụ thuộc vào abstraction. Sử dụng Dependency Injection, tránh `new` trực tiếp các dependency phụ thuộc ngoại vi (database, API bên thứ ba, I/O).
5. **Kiểm thử hành vi:** Viết/cập nhật tests kiểm thử hành vi thực tế, bao phủ positive, negative và edge cases; không viết test hình thức phản chiếu implementation hiện tại.
6. **Bảo mật & Dữ liệu:** Tuyệt đối không hardcode secrets, token, mật khẩu, PII vào mã nguồn, log hoặc test fixtures.
7. **Tự sửa lỗi (Self-healing):** Khi test hoặc build fail: phân tích nguyên nhân → sửa theo giả thuyết → chạy targeted tests → module/required gates theo `50-quality.md`. Không giới hạn số lượt sửa đang tiến triển, nhưng phải dừng khi hết budget hoặc lặp lỗi không có evidence mới. Không coi pass rate là bằng chứng đủ cho AC.
8. **Báo cáo hoàn tất:** Tóm tắt ngắn gọn các files đã thay đổi, lệnh test đã chạy thực tế và kết quả PASS.
