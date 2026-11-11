# Review quy trình planning và kiểm thử

Ngày rà soát 10/11/2026. Kết luận: quy trình có bước planning nhưng thiếu cấu trúc và điều kiện dừng đủ cụ thể; testing thiếu cách chọn phạm vi, tổ chức file và kiểm soát chạy lặp. Những chỗ này có thể làm tăng token, rework và thời gian chạy. Chưa có telemetry dự án để định lượng mức lãng phí hoặc mức tiết kiệm sau sửa.

## Phạm vi và phương pháp

Đã đọc toàn bộ 42 file văn bản trong ruleset gồm entrypoints, rules, roles, skills, policies, project templates, templates, examples, hướng dẫn và hai Python scripts. Đọc nội dung DOCX nguồn bằng OOXML theo thứ tự paragraph/table, gồm history, mục lục và §1–4. DOCX có hai media assets; đây là review nội dung quy trình, không đánh giá hình ảnh hoặc layout bằng render. Không sửa DOCX gốc và không coi bản nguồn là SOP v2.1 đã được duyệt. Bytecode cache không phải source.

## Findings và xử lý

| Mức | Nguồn trong bản trước sửa | Vấn đề và tác động | Xử lý trong ruleset |
|---|---|---|---|
| Cao | SOP §3.2, §3.5, §3.6; README §4; planning skill/role | SOP giữ plan/check plan nhưng README nói bỏ hoàn toàn thủ tục; skill bắt STANDARD/CRITICAL và role bắt handoff reviewer. Không rõ task nào cần plan tới đâu | `10-intake-risk` quyết định depth theo risk/unknown, một nguồn plan, role riêng tùy nhu cầu |
| Cao | planning skill, `10-intake-risk` | Plan chỉ là danh sách trường; thiếu source, kiểm owner/callers/tests, AC→test mapping và điều kiện dừng discovery | Bổ sung cấu trúc plan, fact/assumption/blocker, DoR và stop/replan rules |
| Cao | SOP §3.8; `30-implementation`; developer role | “Đến khi toàn bộ test PASS” dễ dẫn đến rerun hoặc sửa không có giả thuyết; không nối rõ budget với tiến triển | Targeted repair, checkpoint khi không có evidence mới hoặc hết budget; không giới hạn cứng số fix đang tiến triển |
| Cao | SOP §3.7; `50-quality` | Không tách local feedback và required merge gates; có thể full suite mỗi edit hoặc chọn quá ít checks | Ladder targeted → module/boundary → required CI, triggers mở rộng và invalidation |
| Cao | SOP §3.7; implementation rules | Không có ownership/lifecycle cho file test, fixtures hoặc duplicate coverage | Sửa suite/file hiện hữu trước; tạo file theo trách nhiệm; parameterization, cleanup, loại bỏ test obsolete có căn cứ |
| Cao | company execution; validator `validate_task` | Hai trần maximum bằng 0 nghĩa validator không áp hạn, không có bounded infra retry/runtime enforcement; warning dựa vào số khai báo | Không đổi semantics CLI. Rules yêu cầu task/runtime/project đặt retry/backoff thực; không tự retry khi chưa có hạn. README nói rõ giới hạn |
| Vừa | SOP §3.7/§3.10; `50-quality` | PASS chưa yêu cầu discovery/counts; exit 0 với selector sai dễ bị coi có coverage | Evidence gồm counts/skips, command/cwd/selector, revision/config, zero tests không PASS |
| Vừa | QA template, roles, README | Template buộc independent reviewer trong khi policy không bắt mọi tier; README cài đặt ép JSON nhưng task intake nói tùy chọn | QA ghi review mode; role kích hoạt có điều kiện; JSON cần khi chọn automation, task thông thường dùng issue/chat/PR |
| Vừa | `MAPPING_SOP.md`; DOCX history/mục lục | Mapping trỏ §5–7 không có; tên DOCX v1.1 nhưng history có v1.2; hàng FAST có hai đoạn lặp | Sửa mapping và ghi nhận version mismatch. DOCX cần editorial update riêng trước phát hành lại |
| Vừa | Project Profile; metrics | Chưa có fast/module/full commands, worker cap, setup/slow/flaky baseline; số file không chứng minh hệ thống chậm | Mở rộng profile và metrics; đo duration/I/O/setup/RAM trước tối ưu, không đặt quota số file |

## Thiết kế được chọn

Giữ nguyên kiến trúc ruleset: `10-intake-risk.md` sở hữu planning, `50-quality.md` sở hữu test strategy và execution. Skill/role/entrypoint chỉ dẫn tới nguồn chuẩn. Một agent có thể planning, implement và self-review; không sinh thêm role hoặc pipeline bắt buộc. Không tạo PLAN template riêng vì skill và intake đã sở hữu cấu trúc đó; không thêm test runner hoặc scheduler mới.

Plan đủ tốt khi biết đang sửa ở đâu, vì sao, ảnh hưởng ai và chứng minh bằng gì. Sự ngắn gọn chỉ có ích khi không bỏ sót unknown quan trọng. Không khẳng định planning luôn là phase tốn token hoặc dễ sai nhất; cần telemetry theo phase và rework để kiểm chứng ở dự án cụ thể.

Test nhiều không đồng nghĩa chậm chỉ vì nhiều file. Setup DB/broker/browser, repeated I/O, state leakage, trùng coverage và chạy full suite lặp thường là những nơi cần đo. Không giảm test có giá trị, bỏ negative/integration hoặc đặt trần test count để tối ưu số liệu.

## Phần SOP DOCX cần đồng bộ khi tái phát hành

- History/tên version/mục lục: chốt một version nội dung, bỏ hàng FAST lặp; không gán review nội dung này thành chứng nhận layout.
- §3.2 và §3.6: dùng cấu trúc và DoR từ `10-intake-risk`; FAST vài dòng, STANDARD plan ngắn, CRITICAL thêm safety/compatibility/restore. Một plan chuẩn, không ba bản chép lại.
- §3.7: áp dụng `50-quality` cho tầng test, ownership file, fixtures, discovery, ladder và evidence; build/lint/unit theo matrix và loại thay đổi, không ép code tests cho chỉnh câu chữ.
- §3.8: nối tiến triển với budget thực, bounded infra retries và checkpoint; không coi rerun đến xanh là xử lý flaky.
- §3.10/§4: CODE_COMPLETE đòi AC và checks phù hợp đã chạy, không tuyên bố mọi suite của toàn hệ thống đã chạy nếu chỉ chạy targeted/module.
- §3.12: thêm planning rework, repeated unchanged runs, suite duration/setup/flaky; chỉ báo tiết kiệm khi có baseline thực.

Ruleset v2.1 là bản chỉnh có thể review trong workspace, không phải xác nhận thay đổi đã qua human governance approval hoặc triển khai sang các repo sản phẩm.

## Kiểm chứng và giới hạn

Kết quả lệnh thực tế của lần sửa được ghi ở phần Evidence bên dưới. Không thêm test file cho chỉnh tài liệu vì không có behavior executable mới; dùng regression suite hiện hữu cho guardrail và parse JSON/links/Markdown để phát hiện drift. Không đổi policy, schema, CLI hoặc test implementation.

Không có repository Git hợp lệ trong workspace (`git status` báo not a git repository), nên không thể gắn SHA hoặc chạy scope trên history của workspace. So diff nội dung với snapshot trước sửa trong thư mục tạm; integration test hiện hữu tự tạo Git repo tạm để kiểm scope. Project config thật còn placeholders nên phải FAIL; demo config không phải approval thực. Không có sản phẩm/runtime/CI thật để đo hiệu năng, chạy E2E hoặc chứng minh tiết kiệm token.

## Evidence lần rà soát

Working directory của các lệnh bên dưới là `Jobbod_AI_Rules_v2.0/`; workspace chưa có Git history hợp lệ, không gắn SHA giả.

| Lệnh hoặc kiểm tra thực tế | Kết quả |
|---|---|
| `python3 -B -m unittest discover -s .agents/scripts -p 'test_*.py' -v` | Exit 0; 18 tests, 0 failures/errors/skips; 0.041 giây do unittest báo; gồm integration tạo Git history tạm |
| `python3 -B .agents/scripts/ai_policy.py --project .agents/examples/project.policy.demo.json config` | Exit 0; config demo structurally valid |
| `python3 -B .agents/scripts/ai_policy.py --project .agents/examples/project.policy.demo.json task --file .agents/examples/task.standard.example.json` | Exit 0; manifest STANDARD consistent; build/business_regression/lint/unit là khai báo, không phải các CI job đã chạy |
| `python3 -B .agents/scripts/ai_policy.py config` | Exit 2 đúng kỳ vọng fail-closed: project/owners còn placeholders và chưa có CI bindings |
| Parse toàn bộ JSON bằng Python stdlib | PASS |
| So byte source validator, test script và policy với snapshot trước sửa | Không thay đổi |
| Kiểm whitespace, newline và local Markdown references | PASS sau lần chỉnh cuối |
| Review diff với snapshot trước sửa | Thay trực tiếp rules/roles/templates/docs; một file report mới; không tạo test file, runtime path hoặc dependency mới |

Shell login ban đầu báo không tạo được fnm multishell symlink và starship session log do filesystem read-only. Các Python commands vẫn chạy và có exit/status ở trên; các kiểm tra tài liệu sau đó dùng non-login shell. Không che warnings này hoặc quy chúng thành lỗi test.

Không chạy application build/lint/E2E/performance vì workspace chỉ chứa ruleset, không có ứng dụng hoặc lệnh stack tương ứng. Không chạy DOCX render: chỉ review nội dung, không chỉnh hoặc xuất DOCX. `git diff --check`/scope trên workspace không chạy được do thiếu Git repo hợp lệ; thay bằng whitespace/content diff và integration test repo tạm, không coi đó là evidence của một production merge.
