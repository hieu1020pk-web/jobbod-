# Role Planning

- Đây là trách nhiệm phân tích, không bắt buộc là agent riêng. Khi đang planning, chỉ đọc implementation và nguồn yêu cầu.
- Áp dụng `.agents/rules/10-intake-risk.md`; xác minh owner/callers/dependencies/tests và phân biệt fact/assumption/blocker.
- Giữ một plan chuẩn tại issue/chat/PR; JSON nếu automation cần. Không lặp spec hoặc viết pseudocode chi tiết cho phần chưa rõ.
- Output `READY` khi đủ DoR cho bước tiếp theo; `NEEDS_CLARIFICATION/NEEDS_DECISION` khi có blocker trọng yếu. Chuyển review độc lập chỉ khi policy/owner yêu cầu.
- Không cấp quyền, tự giảm Critical hoặc vượt budget. Cùng agent có thể tiếp tục implement trong phạm vi được giao.
