# PLAN — [MÃ TASK] — [TÊN NGẮN]

> Mẫu **tùy chọn** cho STANDARD/CRITICAL. Dùng ngay trong issue/PR/chat nếu đã có một nơi quản lý; **không bắt buộc tạo file**. Với FAST, ghi 3 dòng: *Mục tiêu — Phạm vi sửa — Cách kiểm tra*. Không copy kế hoạch sang nhiều nơi.

- **Nguồn yêu cầu:** [link issue / PRD / AC]
- **Chủ trách nhiệm:** [developer hoặc người phụ trách]; **Người thực thi:** [dev / AI agent]
- **Rủi ro:** [STANDARD | CRITICAL]; **Lý do:** [tín hiệu thực tế; không tự hạ CRITICAL]
- **Trạng thái:** [READY | NEEDS_DECISION | IN_PROGRESS | BLOCKED | DONE]

## 1. Mục tiêu và điều kiện nghiệm thu (AC)

- **Kết quả cần đạt:** [một câu có thể kiểm chứng]
- **AC-01:** [Given / Khi / Thì hoặc mô tả hành vi quan sát được]
- **AC-02 (nếu có):** [lỗi, tình huống biên hoặc quyền truy cập quan trọng]

## 2. Phạm vi và hiểu biết đã kiểm chứng

- **Trong phạm vi:** [module, đường dẫn hoặc symbol đã thực sự tìm thấy]
- **Không làm:** [thay đổi không thuộc task]
- **Nguồn đã kiểm tra:** [file:symbol hoặc link code, test hiện hữu; chưa xác minh thì ghi 'chưa xác minh']
- **Tác động liên quan:** [callers / API / DB / event / UI / dữ liệu / bảo mật; ghi 'không' nếu có cơ sở]
- **Điểm chưa rõ:** [nêu câu hỏi chặn thực hiện; nếu không có ghi 'không']

## 3. Các bước thực hiện (tối đa đủ để triển khai)

1. [Thay đổi chính trong code hiện hữu; kết quả kiểm được]
2. [Cập nhật nơi gọi / contract / dữ liệu / test bị tác động]
3. [Dọn đường cũ nếu đã chứng minh không còn sử dụng]

## 4. Kiểm thử theo tác động

| AC / Rủi ro | Test cần có (ưu tiên test hiện hữu) | Tầng | Lệnh/selector thực tế + cwd | Kết quả |
|---|---|---|---|---|
| AC-01 | [happy path] | [unit/component/integration/e2e] | [xác minh trong repo trước khi chạy] | NOT_RUN |
| AC-02 | [negative/edge case] | [...] | [...] | NOT_RUN |

- **Trong vòng sửa:** chạy test nhỏ liên quan → sửa có căn cứ → chạy lại phần bị ảnh hưởng.
- **Trước PR/merge:** chạy module/boundary phù hợp **và tất cả required CI gates** từ policy dự án trên revision thích hợp.
- **Bằng chứng khi hoàn thành:** lệnh + cwd + selector, SHA/snapshot, pass/fail/skipped, exit code, thời lượng, log/CI link. Không khai PASS nếu chưa chạy hoặc không phát hiện test.

## 5. Rủi ro và bàn giao

- **Điểm dừng:** [đủ AC + checks; hoặc blocker cần quyết định]
- **Nếu CRITICAL:** [kiểm quyền, dữ liệu, tương thích, rollback/restore, người phê duyệt theo policy]
- **Khi thay đổi phạm vi/contract:** cập nhật *phần kế hoạch và test liên quan*, không viết lại tất cả.
- **Bàn giao ngắn:** [files thay đổi, test thực chạy, kết quả, rủi ro còn lại, link PR]

> **Không có thông tin thực tế?** Ghi `NEEDS_DECISION`/`BLOCKED`, không tự điền tên file, lệnh test, dữ liệu hoặc PASS tưởng tượng.
