# Checklist triển khai bộ rules cho mỗi dự án

- [ ] Điền Project Profile, Project Rules và `project.policy.json` (Tech Lead phê duyệt).
- [ ] Chốt service owners, API/event/schema authority và dependency graph ban đầu.
- [ ] Map abstract `check_id` → CI job/status name đang chạy; không đặt tên check giả.
- [ ] Cấu hình required status checks trên protected branch, reviewers/CODEOWNERS và không cho agent bypass.
- [ ] Cấu hình sandbox, scoped credentials, MCP allowlist, isolation cho DB/ports/topics/secrets.
- [ ] Xác minh rủi ro FAST/STANDARD/CRITICAL bằng các task mẫu và human escalation thực.
- [ ] Kiểm tra automation không thể thay policies, CI hoặc production deployment rights.
- [ ] Kiểm tra approval cho Critical, rollback plan và smoke/monitoring trước production.
- [ ] Chọn rõ có bật task/scope validator hay không; nếu bật, cấp JSON input và chạy trong CI theo hướng dẫn; thử negative cases trước khi coi gate đạt.
- [ ] Điền test routing, discovery/selector, timeout/workers, isolation và bounded infra retry trong Project Profile.
- [ ] Pilot plan một nguồn + AC/test mapping: kiểm tra ví dụ `.agents/examples/PLAN_*.example.md` và `.agents/examples/TEST_MATRIX.example.md`; xác minh targeted runs không bỏ required merge checks. Không bắt FAST tạo plan/test report file.
- [ ] Đo duration/setup/flaky/duplicate coverage và planning rework; không áp trần file test hay tuyên bố tiết kiệm token chưa đo.
- [ ] Pilot 2 sprint (baseline theo service/tier), audit tasks/escaped defects/cost/rework và điều chỉnh concurrency.
- [ ] Ghi version rules trong repo và lịch đổi; có migration strategy cho task contract cũ `R0–R4`.

**Release criteria cho pilot:** 1 FAST (docs), 1 STANDARD (business logic) và 1 CRITICAL (mô phỏng, không production) đều có evidence, đúng approval và negative tests. Không cho phép giảm quality chỉ để tăng tốc.
- [ ] Ánh xạ `.agents/policies/role-capabilities.example.json` vào runtime authorization (nếu có); mọi capability mặc định DENY.
- [ ] Xác minh `impacted_services` khi review diff; cross-service tasks phải có integration gate.
