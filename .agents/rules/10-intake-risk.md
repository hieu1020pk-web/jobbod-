# 10 — Intake và planning theo rủi ro

## Cách dùng cho developer (5 bước, không bắt thêm công cụ)

`Nhận yêu cầu → Plan vừa đủ → Code + test → Verify → PR/merge theo policy`. Một developer với một AI coding agent có thể làm trọn luồng. FAST ghi 3 dòng ngay trong issue/chat; STANDARD/CRITICAL có thể dùng `.agents/templates/PLAN_TEMPLATE.md` **tại một nơi** nếu cần. Ba ví dụ ở `.agents/examples/PLAN_{FAST,STANDARD,CRITICAL}.example.md`; không tạo 3 workflow riêng, không bắt buộc file `.md` cho mọi task.

## Chọn tuyến trước khi viết plan

- Xác định outcome, AC quan sát được, phạm vi, owner và tác động contract/data/security. Một Critical signal → CRITICAL theo company policy. Thiếu dữ liệu trọng yếu → STANDARD tạm và `NEEDS_CLARIFICATION`; vẫn được khám phá read-only hoặc làm phần độc lập an toàn.
- FAST: sửa đổi cục bộ đã rõ; ghi mục tiêu, điểm sửa và check trong vài dòng ngay tại issue/chat/PR. Không tạo file plan hoặc gọi Planner riêng.
- STANDARD: một plan ngắn trong issue/chat/PR; thường 3–5 bước theo hành vi, không liệt kê mọi thao tác đọc/sửa file.
- CRITICAL hoặc thay nhiều boundary: thêm compatibility, thứ tự migration/rollout, phục hồi, owners và approvals. Độ dài phụ thuộc rủi ro thực; không bỏ thông tin an toàn để đạt quota.
- JSON chỉ cần khi dự án dùng validator/automation hoặc cần handoff có cấu trúc. Không chép cùng plan sang JSON, Markdown và chat; giữ một nơi chuẩn và liên kết từ nơi khác.

## Khám phá có điểm dừng

1. Đọc yêu cầu và convention của module. Dùng graph nếu có: target symbol → callers → dependencies → tests; dùng search khi graph thiếu và cho config/docs/literals. Không đọc cả repo mặc định.
2. Xác định component đang sở hữu hành vi và test hiện hữu. Ghi nguồn `path:symbol` và revision khi có; không đoán tên hàm, đường dẫn hoặc command chưa tồn tại thành fact.
3. Tách fact, assumption, unknown. Unknown ảnh hưởng AC, quyền, dữ liệu, compatibility hoặc phạm vi là blocker cho phần phụ thuộc. Unknown về chi tiết nội bộ có thể xác minh ở bước triển khai tương ứng.
4. Dừng khám phá khi biết owner, callers/boundaries bị ảnh hưởng, cách sửa và cách chứng minh AC; truy vấn thêm phải trả lời một câu hỏi cụ thể còn thiếu. Khi chưa biết impact, không tự thu hẹp test chỉ dựa vào tên file.

## Nội dung plan tối thiểu

- **Outcome và AC:** kết quả mong đợi; trường hợp sai/biên quan trọng; nguồn yêu cầu.
- **Scope và evidence:** module/path sở hữu, callers/dependencies bị ảnh hưởng, phần ngoài phạm vi; fact/assumption/blocker có nguồn.
- **Cách sửa:** thay đổi implementation hiện hữu; callers cần migrate, code/test/config cũ cần bỏ. Chỉ thêm abstraction khi có nhu cầu thật; không tạo pipeline song song.
- **Các bước:** thứ tự phụ thuộc, mỗi bước có kết quả kiểm tra được; không lập chi tiết cho bước xa còn phụ thuộc quyết định chưa chốt.
- **Verification:** AC → test hiện có cần sửa/bổ sung → lệnh/selector và cwd đã xác minh; check boundary/security phù hợp; điều kiện mở rộng regression theo `50-quality.md`.
- **Risk và điểm dừng:** unknown cần giải quyết, rollback/restore và phê duyệt khi áp dụng; budget có thật từ task/runtime/project.

Đây là cấu trúc nội dung, không bắt buộc tạo sáu biểu mẫu. FAST có thể gộp trong vài dòng. Không đặt phần trăm token planning cố định cho mọi task; dùng độ bất định và rủi ro để quyết định mức khám phá.

## Kiểm plan và cập nhật

- Self-review một lần: AC có chứng minh được không; nguồn code có thật không; đang sửa đúng owner không; có bỏ sót caller, failure case, quyền hoặc dữ liệu không; checks có đủ không?
- Review độc lập khi policy/owner yêu cầu, hoặc có quyết định kiến trúc/boundary cần chuyên môn khác; không mặc định tạo nhiều agents. Review độc lập không thay human approval.
- DoR: đủ AC, scope, owner, cách kiểm chứng và không còn blocker trọng yếu cho bước sắp làm. Sau đó triển khai, không tiếp tục viết plan chỉ để plan dài hơn.
- Khi fact/contract/AC/base thay đổi làm plan sai: cập nhật đúng bước và test scope bị ảnh hưởng, invalidate evidence liên quan; không viết lại toàn bộ plan.
- Không lặp đọc cùng nguồn hay review cùng plan nếu không có evidence mới. Hết budget hoặc không có giả thuyết mới → checkpoint ngắn gồm facts, diff, blockers và bước tiếp theo; không reset lịch sử điều tra.
