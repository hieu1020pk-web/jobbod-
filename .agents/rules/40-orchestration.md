# 40 — Điều phối và Thực thi song song (khi cần)

- Mặc định ưu tiên 1 agent/developer giải quyết trọn vẹn từ đầu đến cuối; chỉ chia subtask song song khi các module hoàn toàn độc lập hoặc người dùng yêu cầu.
- Subtask phải có ID, AC, allowed paths, base SHA, owned interfaces, dependencies, locks, agent role, budget và checks.
- Cấm đồng thời ghi mutable shared contract/schema/migration nếu chưa có ownership/serialization. Contract phải được thống nhất trước consumer tasks.
- Worktree cô lập source nhưng không cô lập test DB/ports/topics/consumer groups/caches/secrets; cấp môi trường test riêng nếu có tranh chấp.
- Agent states: `QUEUED → RUNNING → VERIFYING → COMPLETED`, ngoài ra `BLOCKED/FAILED/NEEDS_DECISION/CANCELLED`; log task/run ID, timestamp, SHA, reason.
- Không giới hạn cứng số lượt sửa code; chỉ chạy lại checks bị ảnh hưởng theo `50-quality.md`. Dừng/checkpoint khi hết budget hoặc lặp cùng lỗi mà không có evidence/hướng sửa mới.
- Hết budget/timeout/loop không tiến triển/scope violation/contract drift → checkpoint, stop phần nguy hiểm, giao human triage.
- Thay contract invalidates dependent subtasks; merge result phải revalidate. Tối ưu concurrency bằng CI queue time, conflicts và rework, không bằng số agents.
