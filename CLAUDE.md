# Claude Code — Jobbod v2.2

Tuân thủ `AGENTS.md` và `.agents/rules/00-core.md`.

Nhận task qua prompt/issue. Planning dùng `10-intake-risk.md`, kiểm thử dùng `50-quality.md`: một plan đủ evidence, sửa implementation/test hiện hữu, targeted → module/boundary → required gates. Không lặp plan/review/test nếu input không đổi; dừng khi hết budget hoặc không tiến triển. Một agent có thể thực hiện từ đầu đến cuối. JSON và vai trò riêng chỉ khi dự án cần. Không đổi governance/CI để vượt gate, không ghi secrets/PII; thay governance được giao rõ phải qua review phù hợp.
