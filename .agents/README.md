# Jobbod AI Agents Ruleset v2.2

Bộ quy tắc cho phát triển phần mềm với AI agents, ưu tiên một agent, planning có evidence và kiểm thử theo tác động. Đây là mẫu triển khai; chưa phải chính sách đã được công ty phê duyệt hoặc hệ thống quyền đã cấu hình.

## Nguồn quy tắc chuẩn

- `.agents/rules/10-intake-risk.md`: intake, phân loại rủi ro, cấu trúc plan, điều kiện kết thúc khám phá và cập nhật plan.
- `.agents/rules/50-quality.md`: chọn tầng test, tổ chức file, thứ tự chạy, tài nguyên và evidence.
- `.agents/policies/company.policy.json`: required checks và guardrails khai báo hiện hữu; bản cập nhật này không đổi schema hay hành vi CLI.
- `.agents/docs/REVIEW_PLANNING_TESTING.md`: findings của lần rà soát ngày 10/11/2026, bao gồm SOP DOCX; không phải nguồn rules thứ hai.

Sửa trực tiếp rules/roles/skills hiện hữu; không thêm pipeline planning hoặc test runner song song. Các chi tiết quy trình chỉ nằm ở hai rules chuẩn trên, các entrypoint/roles liên kết tới đó để tránh nạp trùng.

## Dùng hằng ngày (mọi developer / mọi AI coding agent)

1. **Nhận task:** đọc AC, code/test sở hữu hành vi; phân loại FAST / STANDARD / CRITICAL.
2. **Plan vừa đủ:** FAST ba dòng trong ticket; STANDARD/CRITICAL dùng một plan gọn tại ticket/PR/chat, có thể tham khảo `.agents/templates/PLAN_TEMPLATE.md`.
3. **Code + test:** sửa module đúng owner, cập nhật test hiện hữu; AI hỗ trợ nhưng dev chịu trách nhiệm.
4. **Verify:** targeted → module/boundary theo tác động → required CI. Kết quả không chạy phải ghi `NOT_RUN`, không nói PASS.
5. **Commit/PR:** một diff trong scope; reviewer/approvals theo policy. Không bắt có Planner, QA Agent, Orchestrator hay MCP riêng.

**Tài liệu mẫu:**

| Nhu cầu | File |
|---|---|
| Plan điền nhanh STANDARD/CRITICAL | `.agents/templates/PLAN_TEMPLATE.md` |
| Ba ví dụ plan theo mức | `.agents/examples/PLAN_FAST.example.md`, `PLAN_STANDARD.example.md`, `PLAN_CRITICAL.example.md` |
| Bảng liên kết AC → tình huống kiểm thử (chỉ khi phức tạp) | `.agents/templates/TEST_MATRIX_TEMPLATE.md` |
| Ví dụ kiểm thử quyền tự chốt lịch Jobbod | `.agents/examples/TEST_MATRIX.example.md` |
| Báo cáo QA độc lập (chỉ khi cần) | `.agents/templates/QA_REPORT.md` |

**Không bắt buộc:** tạo `PLAN.md` cho FAST; nhân bản plan trong JSON + MD + issue; cài framework, MCP, worktree, CLI validator hoặc phân nhiều sub-agent. Nếu dự án **đã bật** CI validator/branch protection thì bắt buộc tuân quy trình đó; tùy chọn ở đây chỉ là *cách soạn plan/test*, không phải tùy chọn bỏ quality gate.

## Áp dụng vào dự án

1. Chép `AGENTS.md`, `CLAUDE.md` và `.agents/` vào repo và quản lý version.
2. Điền `PROJECT_PROFILE.md`, `PROJECT_RULES.md`, `project.policy.json`: ownership, commands/runner thực, test routing, timeout/workers, isolation, execution budget và retry/backoff.
3. Chạy `python3 .agents/scripts/ai_policy.py config`. Cấu hình mẫu chứa `__REQUIRED__` phải FAIL cho đến khi được điền thật.
4. Nhận task qua prompt/issue. Dùng JSON template khi dự án chọn automation/validator; không bắt mọi task tạo file contract/plan/QA riêng.
5. Cấu hình branch protection, required CI, sandbox, CODEOWNERS, secrets và approvals thật. Markdown/JSON/CLI không thay thế các cơ chế này.

Nếu bật task/scope validator, JSON là input cần thiết cho cơ chế đó. Xem `.agents/docs/CI_INTEGRATION.md`; không diễn giải “JSON tùy chọn” thành bỏ input của CI đã được dự án chọn.

## Nạp context theo nhu cầu

Mọi agent đọc `AGENTS.md` → `00-core.md` → Project Profile/Rules. Sau đó chỉ nạp rules/role/skill liên quan, không đọc tất cả templates và playbooks mặc định.

| Công việc | Nạp thêm |
|---|---|
| Nhận task và planning | `10-intake-risk.md`; `20-architecture.md` khi ảnh hưởng boundary |
| Implementation | `30-implementation.md`, `50-quality.md`; role developer nếu cần |
| Plan cần phân tích riêng | skill planning và role planner; không bắt buộc agent riêng |
| Review | `50-quality.md`, role/skill review theo policy; `60-security.md` khi liên quan |
| Song song được giao | `40-orchestration.md`, role orchestrator và isolation thực |
| Merge/release | `70-integration-release.md`, quyền/security liên quan |
| Tool-heavy | `90-tools-context.md` |

## Tuyến thực thi

- **FAST:** thay đổi cục bộ rõ ràng, không chạm tín hiệu Critical/contract/nghiệp vụ nhạy cảm. Plan vài dòng trong task → sửa → checks phù hợp → review/merge theo policy.
- **STANDARD:** business logic hoặc contract tương thích; plan ngắn có source và test mapping → sửa từng phần → targeted/module/boundary checks → required CI.
- **CRITICAL:** auth/payment/PII/authorization, breaking contract, migration khó phục hồi, production infrastructure/SLO hoặc phá hủy. Bổ sung safety/compatibility/restore, security checks và human approval theo policy.

Một Critical signal đủ nâng CRITICAL; thiếu thông tin trọng yếu không được tự coi FAST. Con người có thẩm quyền mới được duyệt downgrade bằng decision record và không tự bỏ required controls của tín hiệu gốc.

Pipeline chung: `Yêu cầu → Khám phá và plan vừa đủ → Sửa code và tests → Kiểm chứng theo tác động → Merge/release nếu thuộc scope`. Không ép đủ sáu vai trò. Dừng planning khi đủ DoR; không lặp plan/review/chạy test nếu không có input hoặc evidence mới.

## Planning và testing trong vận hành

Plan phải xác định owner hiện hữu, callers, cách thay thế code cũ và AC có thể chứng minh. Giữ một bản chuẩn ở issue/chat/PR; chỉ cập nhật bước bị invalidated khi scope/contract/fact đổi. Không dùng độ dài plan hay tỷ lệ token cố định làm chỉ tiêu chất lượng.

Test ưu tiên suite/file sở hữu hành vi, parameterized cases khi cùng luật; chỉ thêm file cho trách nhiệm rõ ràng. Chạy nhỏ trước trong vòng sửa rồi đủ module/boundary/required checks trước bàn giao. Không giới hạn số test/file tùy ý, không bỏ integration thật để tiết kiệm và không rerun full suite sau mỗi edit. Project Profile phải đăng ký lệnh và tài nguyên thật.

## Evidence và giới hạn thực thi

Ghi outcome/AC, files sửa/xóa, command + cwd + selector, revision/snapshot, test counts/skips, exit code, duration và link log. Phân biệt `PASS`, `FAIL`, `NOT_RUN`, `BLOCKED`, `N/A`; zero discovered tests không phải PASS. Dùng PR/CI report hiện có, không sinh nhiều file report cho từng lần chạy.

CLI hiện tại chỉ kiểm manifest/config/scope khai báo. Nó không chọn test theo graph, đo token runtime, chạy test, xác minh approval hoặc trạng thái CI. `maximum_* = 0` nghĩa không áp trần trong validator; runtime/task/project vẫn phải có budget và bounded infra retry. Không có cấu hình retry thì không tự retry infra.

Company/project policies và runtime/SCM/CI thực thi quyền; project chỉ được siết baseline. Governance thay đổi phải có review phù hợp; không sửa policy/CI nhằm vượt gate của feature task. Release vẫn phân biệt `CODE_COMPLETE`, `MERGED`, `DEPLOYED`, `DONE`.

## Test và ví dụ thực tế

- `.agents/scripts/test_ai_policy.py` kiểm tra validator/policy framework hiện hữu; **không chứng minh** chất lượng Jobbod FE/BE/AI.
- Ví dụ test trong `.agents/examples/TEST_MATRIX.example.md` là **test scenarios cần hiện thực**, không phải code test đã chạy.
- Project phải điền test commands thật vào `PROJECT_PROFILE.md` và map required CI. Mẫu không được dùng làm lệnh sản phẩm nếu chưa xác minh.

## Lệnh kiểm tra bộ rules

Chạy từ thư mục chứa `.agents/`:

```bash
python3 -B -m unittest discover -s .agents/scripts -p 'test_*.py' -v
python3 -B .agents/scripts/ai_policy.py --project .agents/examples/project.policy.demo.json config
python3 -B .agents/scripts/ai_policy.py --project .agents/examples/project.policy.demo.json task --file .agents/examples/task.standard.example.json
```

Config và task demo chỉ minh họa consistency, không chứng minh approvals/checks sản phẩm thật. Scope cần Git history thật và JSON task:

```bash
python3 -B .agents/scripts/ai_policy.py scope --file /path/to/task.json --base "$BASE_SHA" --head "$HEAD_SHA"
```

Không dùng `--allow-example` trong CI. Xem adoption checklist và changelog trước rollout. Benchmark tasks FAST/STANDARD/CRITICAL trong môi trường thử; đo planning rework, duration/chi phí và escaped defects qua baseline thực trước khi kết luận tiết kiệm.
