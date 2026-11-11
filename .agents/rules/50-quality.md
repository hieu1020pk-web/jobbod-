# 50 — Kiểm thử theo tác động và bằng chứng

## Cách dùng nhanh cho developer

1. Đọc AC và tìm suite/test hiện có ở nơi sở hữu hành vi; chọn test theo tác động (không theo số file).
2. Sửa code + test, chạy **targeted** trước; khi ổn chạy module/affected boundary tương ứng.
3. Trước merge, xác minh **required CI gates trên revision phù hợp**; không bỏ gate chỉ vì chạy local đã xanh.
4. Báo đúng `PASS / FAIL / BLOCKED / NOT_RUN / N/A` cùng lệnh, revision, số test và log; **0 test discovered ≠ PASS**.

Ghi test ngay trong phần Verification của plan. Chỉ dùng `.agents/templates/TEST_MATRIX_TEMPLATE.md` khi cần bảng nhiều tình huống (ví dụ `.agents/examples/TEST_MATRIX.example.md`); bảng không thay bài test tự động, CI hay review hiện hữu. Trường hợp FAST có thể ghi kết quả trực tiếp tại PR/issue; không tạo QA report riêng theo mặc định.

## Chọn mức kiểm chứng

Required checks = baseline theo tier + change types + project additions trong company/project policy. Phân biệt **vòng phản hồi local** với **gate trước merge/release**: chạy local có chọn lọc không cho phép bỏ required CI. Evidence phải gắn revision/merge result tương ứng; workspace chưa commit ghi rõ snapshot chưa commit.

| Thay đổi | Kiểm chứng cần chọn theo tác động |
|---|---|
| Chỉ docs/comment | Parser/link/example/render khi liên quan; không tạo unit test chỉ kiểm tra câu chữ; chạy docs gate bắt buộc |
| Logic hoặc bug cục bộ | Regression tại owner, happy path, invalid/failure và boundary liên quan; module suite trước bàn giao |
| Shared logic/dependency/config/runtime | Affected callers/modules; mở rộng khi dependency graph thiếu hoặc blast radius chưa chắc chắn |
| API/event/DB | Contract + integration thật tại boundary thay đổi; compatibility, migration/dữ liệu, retry/idempotency khi áp dụng |
| UI | Component/accessibility liên quan; E2E cho journey thay đổi hoặc required gate, không E2E mọi biến thể nhỏ |
| Auth/payment/PII/concurrency | Denied access, misuse, duplicate/race/failure window tương ứng; security gates và approvals theo policy |

Không ép mọi test case xuất hiện ở unit, integration và E2E. Chọn tầng thấp nhất chứng minh được rủi ro; thêm tầng khác khi chứng minh một rủi ro khác. Không thay integration bằng mock nếu lỗi nằm ở SQL, broker, HTTP serialization, transaction hoặc tích hợp thật.

## Nguyên tắc viết và tổ chức file test

- Trước khi thêm: tìm test/suite/fixture đang sở hữu hành vi. Sửa hoặc bổ sung tại đó; chỉ tạo file khi có trách nhiệm/module/tầng test khác rõ ràng hoặc file hiện tại cần tách theo trách nhiệm.
- Không tạo file theo task ID, ngày, mỗi bug hoặc mỗi case; không tạo `new`, `v2`, `final` cho cùng hành vi. Giữ conventions/discovery hiện có; test đặt gần module hoặc trong test project tương ứng.
- Ưu tiên table-driven/parameterized cho cùng luật với nhiều dữ liệu; không gộp những hành vi khác nhau thành test khổng lồ. Tên case thể hiện điều kiện và kết quả; khi fail phải xác định được case.
- Kiểm observable behavior/invariant, không sao chép thuật toán production làm expected result, không assert private methods hoặc mock chính hành vi đang kiểm. Với bug, chứng minh test fail trên lỗi cũ khi khả thi; ghi lý do nếu không tái hiện an toàn được.
- Failure và invalid input bắt buộc khi liên quan; authorization, cancellation, timeout, concurrency/idempotency theo rủi ro. Không viết đủ nhánh vô nghĩa để tăng số test hoặc coverage.
- Fixture nhỏ, deterministic và dữ liệu giả; không secrets/PII thật. Cleanup DB/process/file/port/topic kể cả khi fail; không sleep tùy ý hay phụ thuộc thứ tự/chạy cùng máy.
- Chỉ chia sẻ setup khi cùng lifecycle và không gây state leakage. Không tạo test helper/framework/dependency mới chỉ cho một case đơn giản.
- Áp dụng hướng dẫn kích thước file của repo; tách theo trách nhiệm/discovery, không chia máy móc theo số dòng. Số file không phải thước đo hiệu năng; đo số case, setup, I/O, RAM và duration.
- Khi thay behavior: migrate callers/tests và xóa test/fixture/config của đường cũ nếu đã chứng minh obsolete. Không xóa regression hợp lệ chỉ vì chậm hoặc trùng tên.

## Thứ tự chạy tiết kiệm

1. Xác minh cwd, runtime, runner, lệnh/selector, discovery và môi trường theo Project Profile. Liệt kê test trước khi chạy nếu selector chưa chắc; exit 0 với zero tests không phải PASS.
2. Vòng sửa: chạy case/file/suite nhỏ nhất bắt lỗi vừa sửa và checks nhanh có liên quan. Gom một batch sửa có cùng nguyên nhân rồi chạy; không chạy full suite sau từng edit.
3. Khi targeted PASS: chạy suite của module và affected callers/boundaries theo plan. Shared behavior, thay build/test discovery/dependency/config, graph thiếu, lỗi chưa rõ phạm vi hoặc required CI → mở rộng regression tương ứng.
4. Trước bàn giao/merge: chạy các required checks đủ phạm vi trên revision cuối. Rebase/merge hoặc sửa source/test/config/dependency/environment liên quan → chạy lại checks bị ảnh hưởng. CI merge validation theo `70-integration-release.md` vẫn bắt buộc.
5. Dừng khi AC và required checks đủ evidence, không còn blocking finding. Không chạy lại cùng command trên cùng input chỉ để tạo thêm log hoặc “chắc hơn”. Flaky/concurrency investigation có thể lặp có chủ đích với số lần, seed và giả thuyết ghi rõ.

Không dùng `--no-build`/cache nếu artifact không tương ứng source/config/runtime/dependencies; cache build không thay kết quả test. Nếu tái sử dụng evidence, phải xác minh cùng input, command, runner/config và môi trường liên quan; nếu không chắc thì chạy lại. Không chạy trùng local và CI khi evidence hợp lệ đã đáp ứng cùng gate và project không yêu cầu cả hai.

## Tài nguyên và xử lý lỗi

- Profile dự án khai báo fast/module/integration/full commands, timeout, worker cap và isolation. Không tự dùng tất cả CPU hoặc chạy nhiều full suites cạnh tranh DB/RAM/ports.
- Đo duration, setup cost, slowest tests và flaky rate trước tối ưu. Ưu tiên giảm repeated setup, I/O, data volume, duplicate coverage; shard/parallel chỉ khi isolation bảo đảm. Không đặt trần số file/test chung cho mọi dự án.
- Fail → đọc lỗi đầu tiên có nguyên nhân, phân loại code/test/infra/discovery; sửa theo giả thuyết, chạy lại phạm vi liên quan. Không rerun nguyên suite khi input và giả thuyết không đổi.
- Không giới hạn cứng số lần sửa code đang có tiến triển; vẫn tuân budget/time/cost thực. Khi lặp cùng failure signature mà không có evidence hoặc hướng sửa mới: checkpoint và triage; không tiếp tục mù để “đến khi xanh”.
- Tool/infra retry phải có hạn/backoff do task/runtime/project quy định trước; thiếu hạn thì không retry tự động. `0` trong validator hiện tại là không áp trần khai báo, không có nghĩa runtime đã quản lý retry.
- Flaky không được đổi FAIL thành PASS bằng retry. Quarantine chỉ qua quy trình owner/issue/expiry được duyệt và có kiểm soát bù, không tự bỏ blocking gate.
- Không weaken assertions, hạ thresholds, skip valid tests hoặc che exit code để xanh. Thiếu dependency/môi trường → `BLOCKED/NOT_RUN`, ghi chính xác điều kiện thiếu.

## Evidence gọn

Dùng PR/CI report hiện có; QA template khi cần, không tạo báo cáo cho từng lần chạy. Ghi cwd + command/selector, revision/snapshot, runner/config/environment liên quan, exit status, counts passed/failed/skipped, duration và log/artifact link. Output vào context chỉ cần summary và lỗi liên quan; giữ full log ở artifact, không che warning/error ảnh hưởng kết luận. Ghi rõ targeted suite khác full suite.

`PASS` chỉ áp dụng cho checks thực sự chạy với discovery đúng. `N/A` cần lý do/owner/approval theo policy; không thay required check bằng câu “không cần”. Một consolidated review sau batch hoàn chỉnh; review lại khi có phát hiện/thay đổi mới ảnh hưởng kết luận.
