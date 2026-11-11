---
name: plan-task
description: Lập plan theo rủi ro khi impact hoặc dependencies cần phân tích, không dùng mặc định cho mọi task.
---
# Skill Planning

**Trigger:** task có bất định trọng yếu, thay boundary hoặc cần phối hợp nhiều bước; FAST đã rõ không cần gọi riêng.
**Inputs:** yêu cầu gốc, project profile, implementation/callers/tests hiện hữu và policy liên quan.
**Steps:** áp dụng `.agents/rules/10-intake-risk.md` làm nguồn chuẩn → khám phá có phạm vi → ghi plan tại một nơi → self-review → triển khai hoặc chuyển decision cần xử lý.
**Outputs:** plan đủ outcome/AC, scope/evidence, cách sửa, bước phụ thuộc, verification và risk/điểm dừng. Có mẫu tùy chọn `.agents/templates/PLAN_TEMPLATE.md` và ví dụ trong `.agents/examples/PLAN_*.example.md`; dùng issue/chat/PR hiện có, JSON chỉ khi automation cần.
**Stop:** đủ DoR cho bước tiếp theo thì kết thúc planning; không tạo thêm plan/review/handoff nếu không có người tiếp nhận hoặc yêu cầu thật.
**Boundary:** bước planning không sửa production code hay cấp quyền; cùng agent có thể chuyển sang implementation sau khi đủ DoR. Không tự phê duyệt Critical downgrade.
