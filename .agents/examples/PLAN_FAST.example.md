# Ví dụ FAST — Đổi nhãn giao diện trong trang hồ sơ

> **Tình huống giả định, không phải task đã chạy**. Thực tế hãy xác minh path và lệnh trong repository; ví dụ này không chứng minh quyền hay CI đang hoạt động.

- **Mục tiêu:** Đổi nhãn “Skill” thành “Kỹ năng” trên thẻ hồ sơ, không đổi hành vi.
- **Phạm vi:** Component đang render nhãn; xác định sau khi tìm trong source. Không đổi API, DB hoặc bản dịch ngoài phạm vi.
- **Kiểm chứng:** Xem giao diện/kiểm tra component nếu có; chạy lint hoặc docs/component gate đúng project policy. Chưa chạy → `NOT_RUN`.

**Không bắt buộc tạo file plan, QA report hay gọi Agent chuyên planning cho loại task này.** Chỉ tăng lên STANDARD/CRITICAL nếu khám phá phát hiện logic, data hoặc quyền nhạy cảm.
