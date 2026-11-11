# TEST MATRIX — [TASK ID]

> **Chỉ dùng khi bảng test trong PLAN không đủ** (CRITICAL, nhiều module/contract hoặc nhiều nhóm kiểm thử). Nếu đã có Test Case Management, issue hoặc PR để lưu bảng này, sử dụng nơi đó; **không tạo thêm file**. Không phải một bộ test runner.

- **Yêu cầu nguồn:** [PRD/issue/AC]
- **Rủi ro / change type:** [FAST | STANDARD | CRITICAL]; [API/DB/UI/authorization/...]
- **Revision đang kiểm:** [SHA, hoặc snapshot chưa commit]
- **Môi trường / dữ liệu giả / tài nguyên:** [DB, broker, user/roles, isolation; không dùng dữ liệu thật]

| ID | AC / rủi ro | Kịch bản và kỳ vọng | Tầng thấp nhất phù hợp | Suite/file đã có hoặc cần bổ sung | Lệnh + cwd / selector | Trạng thái | Evidence |
|---|---|---|---|---|---|---|---|
| TC-01 | AC-01 | [đầu vào hợp lệ → kết quả] | [unit / component / integration / e2e] | [path đã kiểm chứng] | [command đã kiểm chứng] | NOT_RUN | — |
| TC-02 | AC-02 | [truy cập bị từ chối / input lỗi] | [tầng phù hợp] | [path hoặc 'chưa kiểm tra'] | [command hoặc 'chưa cấu hình'] | NOT_RUN | — |

## Thứ tự và điều kiện chạy

1. Chạy targeted test khi sửa → module hoặc boundary thực bị tác động → required CI theo project policy.
2. Không thêm một tầng test nếu nó không chứng minh rủi ro khác; **không thay integration thật bằng mock** cho lỗi tại DB/API/event.
3. `PASS` khi test có discovery khác 0 và có exit code/evidence; `FAIL` khi có lỗi; `BLOCKED` khi môi trường thiếu; `NOT_RUN` khi chưa chạy; `N/A` cần lý do + thẩm quyền theo policy.
4. Khi code, data schema, runtime hoặc merge result đổi: chỉ chạy lại các checks có evidence không còn hợp lệ; không loop full suite vô ích.

## Tổng kết cho PR

- **AC đã kiểm chứng:** [ID → evidence]
- **Required CI còn thiếu:** [check → reason/owner]
- **Lỗi hoặc rủi ro còn lại:** [finding + người xử lý]
- **Kết luận:** [PASS | FAIL | BLOCKED] — không ghi PASS nếu gate bắt buộc chưa đạt.
