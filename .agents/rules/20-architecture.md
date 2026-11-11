# 20 — Kiến trúc và ranh giới tích hợp

- Tuân thủ System Design/ADR và service/module ownership. Thực trạng code không tự thay thế quyết định đã duyệt.
- Thay public API/event/shared library/migration phải liệt kê consumers, compatibility, version, rollout order; chốt contract trước khi triển khai dependents.
- API: validation, authorization, errors, idempotency/retry khi liên quan. Event: schema, duplicate/out-of-order, retry/DLQ, idempotency; không mặc định exactly-once.
- Database: ownership, expand/contract, data preservation, locking, restore/roll-forward; không giả định down migration khôi phục được dữ liệu.
- Contract update đi kèm code, tests và docs + consumer/provider evidence. Không tự tạo service/schema/abstraction dự phòng.
- Contract conflict hoặc cross-service impact → block dependents, tạo decision/ADR, chạy Cross-Service Integration Gate khi cần.
