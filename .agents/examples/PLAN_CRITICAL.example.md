# Ví dụ CRITICAL — Thu hồi quyền tự chốt lịch khi A2A đang xử lý

> Ví dụ giả định theo sản phẩm Jobbod. Không phải bằng chứng triển khai. Các trường policy/version/command phải kiểm chứng trong code trước khi thực thi.

- **Nguồn yêu cầu:** Ví dụ US-AUTH-01; quyền người dùng phải có hiệu lực trước khi tự động chốt lịch.
- **Owner:** [người phụ trách]; **Rủi ro:** CRITICAL — `authorization`, có thể `pii` và concurrency.
- **Trạng thái:** NEEDS_DECISION cho mọi quy tắc hủy/chốt chưa được PO phê duyệt; không hạ CRITICAL để tiết kiệm test.

## AC

- **AC-01:** Hai người cùng ủy quyền tự chốt và mọi điều kiện hợp lệ → có thể tạo một lịch duy nhất.
- **AC-02:** Một người thu hồi quyền trước điểm chốt → không thể tự chốt lịch; không dùng snapshot quyền đã hết hiệu lực.
- **AC-03:** Một người ở chế độ yêu cầu xác nhận → lịch chỉ CONFIRMED sau khi cả hai hoàn tất xác nhận cần thiết.
- **AC-04:** Hai luồng xử lý đồng thời cùng slot không tạo hai lịch bị trùng; retry không tạo bản ghi trùng.
- **AC-05:** Thông tin riêng không bị gửi vượt phạm vi chia sẻ khi hai Agent trao đổi.

## Scope và quyết định

- Cần truy tìm: API quyền Agent, nơi xác thực policy, transaction tạo lịch, storage và integration boundary.
- Không làm: thay cơ chế đăng nhập, UI unrelated hoặc nâng quyền Agent ngoài phạm vi được cấp.
- Chốt điểm kiểm quyền ngay trước commit, version/concurrency strategy, transaction boundary, behavior khi cancel, audit và khả năng phục hồi với backend owner.

## Các bước và rollback

1. Xác minh tất cả đường vào auto-confirm; thiết kế policy gate phía BE (không tin kết luận của LLM).
2. Implement kiểm quyền phiên bản mới nhất trước commit, xử lý cạnh tranh và idempotency bằng primitives có thật của stack.
3. Migrate callers/tests cũ, thêm negative/security/integration tests và giám sát audit; không xóa đường cũ nếu còn caller.
4. Có cách tắt auto-confirm (feature flag nếu thực tế có) và kế hoạch phục hồi dữ liệu/lịch nếu rollout lỗi; **cần owner xác nhận**, không gọi đó là rollback sẵn sàng khi chưa kiểm chứng.

## Verification

| AC | Case | Tầng ưu tiên | Command + cwd | Kết quả |
|---|---|---|---|---|
| 01 | Hai quyền hợp lệ | Integration | Xác minh trong profile dự án | NOT_RUN |
| 02 | Thu hồi giữa thương lượng và commit | Integration, security-negative | Xác minh | NOT_RUN |
| 03 | Mixed-mode không auto-confirm | Unit + Integration | Xác minh | NOT_RUN |
| 04 | Concurrent same slot / replay request | Integration thật với DB | Xác minh | NOT_RUN |
| 05 | Chia sẻ dữ liệu ngoài scope bị từ chối | Security / contract | Xác minh | NOT_RUN |

Trước merge: thêm các required checks CRITICAL + change type từ company/project policy (build/lint/unit/SAST/SCA/secrets scan/authorization-negative/security review và checks boundary thực). Cần approvals theo policy nếu production; reviewer không thể tự thay sự phê duyệt của chủ trách nhiệm.

**Điểm dừng:** FAIL/BLOCKED nếu chưa chạy integration thật, policy gate fail, thiếu approval hoặc thiếu rollback/restore plan bắt buộc. Không dùng PASS chỉ vì agent báo “đã xử lý”.
