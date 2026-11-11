# Migration từ Jobbod_AI_Universal_Rules_v1.0

1. Giữ v1.0 trong nhánh lưu trữ hoặc version tag. Chuyển sang v2 trong PR riêng về governance, không gộp với feature code.
2. Đối chiếu company rules v1 với `.agents/rules/` mới; chuyển conventions **đặc thù project** vào `PROJECT_RULES.md`, không thêm vào company core.
3. Migrate `R0–R4` cũ theo **tác động thật của task**, không map 1:1 theo tên mã: docs/nonbusiness/local→FAST; business/compatible→STANDARD; auth/payment/PII/breaking/irreversible/production infra→CRITICAL.
4. Nếu dự án bật task/scope validator, chuyển Task Contract sang JSON tương ứng; task thường có thể dùng issue/chat/PR theo `10-intake-risk.md`. Nếu chưa có `base_sha`, owner, signals, checks hoặc AC, dừng tại `NEEDS_CLARIFICATION` thay vì tự điền đoán.
5. Điền `project.policy.json`, map check IDs sang status CI thực và giữ nguyên branch protections hiện có khi chưa kiểm thử chuyển đổi.
6. Mỗi project phải xem xét các việc như bổ sung CI job, CODEOWNERS, release approvals, worktree isolation: chỉ khai báo rules không đủ.
7. Test negative: hạ payment xuống FAST phải FAIL; thiếu integration phải FAIL; chỉnh `.agents/rules/*` từ feature task phải FAIL; chưa cấu hình phải FAIL.
8. Chạy pilot 2 sprint, tổng hợp DORA+AI metrics, đánh giá tần suất manual review/escalation và sửa policy trước khi nhân rộng.

**Chuyển đổi role:** v1 có core + rules chung; v2 thêm `roles/{planner,plan-reviewer,orchestrator,developer,qa-reviewer,integrator}.md`. Agent chỉ đọc role hiện tại + core + chính sách cần thiết, không nạp toàn bộ.

**Thay đổi trạng thái:** phân biệt `task status`, `agent lifecycle` và `delivery state`; không dùng DONE thay cho merged.
