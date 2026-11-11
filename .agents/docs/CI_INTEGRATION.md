# Triển khai guardrails trong CI

1. Bật branch protection/required checks và reviewer/owner protection **tại Git host**; không chỉ nhờ agent “tuân thủ”.
2. Điền `.agents/project/project.policy.json` và map `ci_check_bindings`: `check_id` trừu tượng → tên status check thực trong CI. CLI chỉ xác nhận mapping, không xác minh status trên Git host.
3. Khi dự án bật task/scope validator, lưu Task Contract **cùng PR** ở đường dẫn ổn định (ví dụ `tasks/ID.contract.json`) và workflow gọi:

```bash
python3 .agents/scripts/ai_policy.py config
python3 .agents/scripts/ai_policy.py task --file "$TASK_CONTRACT"
python3 .agents/scripts/ai_policy.py scope --file "$TASK_CONTRACT" --base "$PR_BASE_SHA" --head "$PR_HEAD_SHA"
```

4. CI provider phải tự chạy các job build/lint/test/security tương ứng và xác minh status trên **merge result hoặc cuối cùng**. Dùng quyền tối thiểu; không đưa production secrets vào PR từ fork.
5. Khi fail, script trả exit code != 0; không được tự cho phép bypass bằng `--allow-example` trên CI.
6. `scope` so tên files trong `git diff` và các glob khai báo. Nó không chặn mọi hình thức path traversal tại runtime, cũng không bắt import/dependency/data exfiltration. Cần sandbox, code review và secret scanning.
7. Nếu policy file bị chỉnh trong PR, scope gate chặn mặc định; muốn đổi baseline phải có PR governance riêng, human review và kiểm tra bằng chính sách được lấy từ trusted base branch (không chỉ dùng policy do PR tự cung cấp).

**Lưu ý CI trust:** với PR không đáng tin, script/policy lấy từ branch PR cũng có thể bị người gửi PR sửa. CI cần dùng script/policy từ nhánh bảo vệ hoặc artifact tin cậy, và không cấp token có quyền ghi. Ví dụ đi kèm chỉ minh họa, không thay thiết kế trust boundary của Git provider.

## Cross-service quality guardrail

Task Contract phải khai báo `impacted_services`. Khi danh sách có từ hai service/module trở lên, validator yêu cầu thêm `cross_service_integration` trong `required_checks`; job thực tế phải do project CI cung cấp. Trường này vẫn dựa vào khai báo của con người/agent: cần reviewer xác minh service impact với diff, call graph và event/API contract.

## Role capabilities

`.agents/policies/role-capabilities.example.json` cung cấp ma trận tham khảo để triển khai tool broker, không được tự động coi là runtime grants. Mọi deployment production hoặc quyền đọc secrets phải do policy engine/host thực sự kiểm soát và ghi log.
