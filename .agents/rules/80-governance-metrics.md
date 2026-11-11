# 80 — Governance và metrics

- Company > project > service > role > task. Thay rule/skill/gate/permission bằng PR, owner, independent review, semantic version, migration notes.
- Coding agent không tự sửa policy/CI/gate của task. Có thể đề xuất RFC hoặc Decision Record.
- Theo dõi DORA (Change Lead Time, Deployment Frequency, Failed Deployment Recovery Time, Change Fail Rate, Deployment Rework Rate) cùng task cycle, review/CI wait, escaped defects, rework, flaky checks, cost/accepted task, retry và human intervention.
- Theo dõi planning rework, token/time theo phase nếu telemetry có thật, repeated unchanged runs, test counts/duration/setup và escaped defects; không tối ưu số file/test riêng lẻ hoặc đoán token đã tiết kiệm.
- Thu thập baseline 2 sprint theo service/tier, không so sánh thô dự án khác nhau. Mỗi sprint cải tiến một bottleneck thực, không tối ưu token gây tăng lỗi.
- Audit sample task hàng tháng; exception phải có scope, human approver, reason, expiration, mitigation, remediation owner.
- Ưu tiên regression test/automated guardrail khi học từ incident; chỉ thêm company rule nếu vấn đề có tính phổ quát.
