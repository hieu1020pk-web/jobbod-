# 70 — Merge, release, rollback và DoD

1. Validate task/AC/paths/tier/approvals, kiểm chứng test và checks thực tế trên commit/merge result, không còn blocking issues.
2. Merge vào protected branch theo dependencies; rebase/merge/conflict → chạy lại checks có thể bị ảnh hưởng.
3. Cross-service: consumer/provider contract, integration, event/schema/DB migration compatibility; không bỏ qua vì tests service riêng lẻ PASS.
4. Delivery state phân biệt `CODE_COMPLETE`, `MERGED`, `DEPLOYED`, `DONE`, `ROLLED_BACK`; không coi merge là Done.
5. Critical production yêu cầu human authorization, rollback/restore (hoặc giải trình phương án phục hồi), smoke/health, observability và rollout pause signals.
6. Sau triển khai, quan sát error/latency/business/security signals theo SLO; nếu không đạt, pause/rollback/incident kèm owner.
7. DONE chỉ khi AC, evidence, review, merge/release obligations theo tier đạt. Nếu task không cần deploy, ghi N/A hợp lệ.
