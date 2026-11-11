# Mapping SOP và ruleset

DOCX `QuyTrinh_AI_Agents_SOP_v1.1 (1).docx` có history đến v1.2 trong nội dung. Tên file không phản ánh đúng version nội dung; bản gốc được giữ làm nguồn review, chưa được sửa hoặc phê duyệt lại. Ruleset v2.1 cập nhật quy trình planning/testing; findings và phần SOP cần đồng bộ nằm trong `REVIEW_PLANNING_TESTING.md`.

| SOP section thực sự có trong bản nguồn | Nguồn rules tương ứng |
|---|---|
| §3.1–3.2 Chuẩn bị và các bước | `10-intake-risk`, roles khi cần; README pipeline |
| §3.3 Rules và skills | entrypoints, `.agents/skills/`, project rules |
| §3.4 Tools | `90-tools-context`; tool list trong SOP là tham khảo, không cấp quyền |
| §3.5–3.6 Risk và DoR | `10-intake-risk`, company risk policy; JSON khi validator được dùng |
| §3.7 Quality và testing | `50-quality`, company quality matrix, Project Profile, QA template |
| §3.8 Failure recovery | `30-implementation`, `40-orchestration`, `50-quality`, runtime budgets |
| §3.9 Parallel | `20-architecture`, `40-orchestration`, runtime isolation |
| §3.10 Release | `70-integration-release`, release/approval fields khi áp dụng |
| §3.11 Governance | `60-security`, `80-governance-metrics`, protected paths |
| §3.12 Metrics | `80-governance-metrics`, baseline theo service/tier |
| §3.13 Exceptions | `DECISION_RECORD.md` |
| §4 AC-01–10 | AC/test mapping, real checks, scope, release evidence |

Bỏ mapping cũ tới §5 RACI, §6 Pilot, §7 Templates vì các mục đó không có trong DOCX được cung cấp. Adoption checklist và templates là nội dung bổ sung của ruleset, không phải trích dẫn các mục SOP này.

CLI chỉ kiểm consistency của dữ liệu/diff; không xác minh sandbox, CI pass, approvals hoặc chất lượng plan/test selection.
