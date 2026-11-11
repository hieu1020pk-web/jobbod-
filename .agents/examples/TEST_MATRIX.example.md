# Ví dụ TEST MATRIX — Tự chốt lịch Jobbod (CRITICAL)

> Ví dụ **chưa thực thi**; các kịch bản là gợi ý kiểm chứng, không phải test đã có hoặc kết quả thực. Xác minh file/runner/CI trong project thật. Dùng cùng task `PLAN_CRITICAL.example.md`, không buộc lưu matrix ở file khác nếu PR đã có.

| ID | AC | Kịch bản / expected | Tầng | Suite hiện hữu | Command + cwd | Status | Evidence |
|---|---|---|---|---|---|---|---|
| TC-01 | AC-01 | Hai bên M2, quyền hiệu lực, slot không xung đột → một lịch | integration | cần tìm | cần xác minh | NOT_RUN | — |
| TC-02 | AC-02 | Thu hồi quyền trước commit → không tạo lịch | integration, security | cần tìm | cần xác minh | NOT_RUN | — |
| TC-03 | AC-03 | M1–M2: chưa đủ xác nhận → không auto-confirm | unit + integration | cần tìm | cần xác minh | NOT_RUN | — |
| TC-04 | AC-04 | Hai request cạnh tranh cùng slot → không double-book | integration DB thật | cần tìm | cần xác minh | NOT_RUN | — |
| TC-05 | AC-04 | Retry cùng idempotency key → cùng kết quả, không thêm lịch | integration DB thật | cần tìm | cần xác minh | NOT_RUN | — |
| TC-06 | AC-05 | Dữ liệu ngoài consentScope → bị chặn và không phát ra event | contract/security | cần tìm | cần xác minh | NOT_RUN | — |

**Test selection:** target owner trước; thêm DB integration vì concurrency/transaction không thể xác minh đúng chỉ với mock. Không copy cùng case vào mọi tầng, không tạo 6 file test theo từng mã TC. Sau khi sửa code, chạy lại checks mà diff đã làm mất hiệu lực, không tự retry flaky vô hạn.

**Gate kiểm chứng:** dựa vào `.agents/policies/company.policy.json` và `.agents/project/project.policy.json`; `PASS` cần test discovery > 0, exit code, revision, log. Kết luận hiện tại: `NOT_RUN` — chưa được kiểm chứng trong sản phẩm.
