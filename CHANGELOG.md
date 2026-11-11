# Change log

## v2.2 — 2026-11-10 (Planning và Testing theo hướng developer-first)

- Giữ nguyên chính sách FAST/STANDARD/CRITICAL và CLI validator; không tăng phụ thuộc công cụ hoặc bắt buộc nhiều AI Agent.
- Thêm `PLAN_TEMPLATE.md` và 3 ví dụ FAST/STANDARD/CRITICAL; FAST vẫn chỉ cần 3 dòng trong task, không buộc lưu file.
- Thêm `TEST_MATRIX_TEMPLATE.md` và ví dụ test cho quyền auto-confirm Jobbod; sử dụng có điều kiện, không nhân đôi QA report/CI.
- Thêm luồng 5 bước và chỉ dẫn ngắn tại đầu rules planning/testing; đồng bộ entrypoint, README, vai trò developer và skill planning.
- Mọi expected test trong ví dụ đều là kịch bản **chưa chạy**; `PASS` chỉ có sau khi chạy trên dự án thật có evidence.



## v2.1 — 2026-11-10

- Thay nội dung planning trong `10-intake-risk` và skill/role hiện hữu: một plan chuẩn, discovery có điểm dừng, source/fact/unknown và AC/test mapping, cập nhật theo phần bị ảnh hưởng.
- Thay `50-quality` bằng quy tắc chọn tầng test, tái sử dụng file/suite, discovery/counts, targeted → module/boundary → required CI, evidence và tài nguyên.
- Bỏ câu tự sửa đến pass vô điều kiện; giữ sửa lỗi có tiến triển trong budget thực và checkpoint khi thiếu evidence mới.
- Đồng bộ entrypoints, roles, QA/handoff, Project Profile, README, adoption/CI/migration docs. Bỏ mapping SOP tới các mục không tồn tại.
- Thêm báo cáo review, bao gồm nội dung DOCX. DOCX gốc giữ nguyên, chưa review layout/render hoặc sửa version. Không đổi CLI, policy JSON, schema hoặc test runner; không tuyên bố guardrail mới đã được máy thực thi.
- Lịch sử v2.0 phía dưới mô tả thời điểm phát hành trước; retry/reviewer đã được nới trong trạng thái v2.0 được cung cấp. Nguồn hiện hành là policy JSON và rules, không dùng bullet lịch sử làm config.

## v2.0 — 2026-11-09

**Thay thế v1.0, không sửa tài liệu cũ.** Đồng bộ SOP AI Agents v1.1:

- Thêm FAST / STANDARD / CRITICAL và precedence rule + routing rule có thể kiểm thử.
- Quality gate matrix theo change type, yêu cầu evidence/N/A/reviewer độc lập.
- Retry/failure budget (`2` lượt sửa, `1` retry tool, cảnh báo `80%`) và state machine tách agent vs delivery.
- Orchestrator với ownership/locks cho shared contract, dependency invalidation và isolation thực tế.
- Rõ ràng approval người chịu trách nhiệm, các bước release và Definition of Done.
- Tách role contracts, skills chỉ nạp khi cần và entrypoint ngắn để tiết kiệm context.
- Bổ sung CLI kiểm cấu hình/rủi ro/scope bằng stdlib và unit tests. CLI là guardrail kiểm tra khai báo, **không phải policy engine hoàn chỉnh**.
- Bổ sung ví dụ, templates, checklist rollout và migration notes.

## So với v1.0

**Giữ:** no fabrication, least privilege, task contract, ADR/contract-first, independent review, worktree, protected branches.

**Nâng cấp:** xử lý task theo rủi ro thay vì áp pipeline cứng cho mọi task; phân biệt agent state và delivery state; tách company baseline khỏi cấu hình từng repo, chống nạp quá nhiều context.

**Không tương thích trực tiếp:** mã risk `R0–R4` cũ thay bằng `FAST/STANDARD/CRITICAL`; mọi task template hoặc automation cũ phải map lại trước khi chạy.
