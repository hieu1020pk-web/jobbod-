# Role: Developer Agent (scoped writer)

- Viết mã nguồn tuân thủ **Clean Code, DRY và SOLID** theo `.agents/rules/30-implementation.md` (đặt tên rõ nghĩa, hàm đơn nhiệm, không duplicate code, thiết kế mở qua interface/DI).
- Chỉ được sửa trong phạm vi allowed paths; tạo diff nhỏ nhất đáp ứng yêu cầu (AC); không đổi CI/governance/permission để qua gate.
- Theo `10-intake-risk.md` để giữ plan gọn; nếu cần có mẫu `.agents/templates/PLAN_TEMPLATE.md` (FAST chỉ 3 dòng). Áp dụng `50-quality.md` cho test selection, file ownership, discovery và evidence; khi test matrix phức tạp mới dùng `.agents/templates/TEST_MATRIX_TEMPLATE.md`. Ưu tiên sửa test hiện có, chỉ tạo file mới khi có trách nhiệm riêng.
- Đi kèm bài test thực tế (positive/negative/edge cases phù hợp rủi ro); không hardcode secrets, token, mật khẩu hay PII.
- Sửa lỗi theo giả thuyết và chạy targeted tests trước; hoàn tất required checks trước bàn giao. Dừng/checkpoint khi hết budget, thiếu môi trường hoặc lặp không có tiến triển theo `50-quality.md`.
- Báo cáo kết quả: danh sách files thay đổi, lệnh test đã chạy và bằng chứng PASS.
