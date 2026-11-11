# Ví dụ STANDARD — Bộ lọc thời gian rảnh khi gợi ý kết nối

> Ví dụ minh họa để developer copy cách nghĩ; **chưa có code, command hoặc kết quả PASS thật**. Đường dẫn cần được xác minh trên repository đích.

- **Nguồn yêu cầu:** Ví dụ US-MATCH-01: Không gợi ý hai người thiếu khung giờ phù hợp.
- **Owner:** [developer được giao]; **Rủi ro:** STANDARD (logic nghiệp vụ, giả định chưa sửa API/DB/authorization).
- **Trạng thái:** NEEDS_DECISION nếu quy tắc timezone hoặc min overlap chưa thống nhất, ngược lại READY khi đã có AC.

## Mục tiêu & AC

- **AC-01:** Khi A và B có khung giờ giao nhau đủ điều kiện, B có thể được xếp vào tập ứng viên.
- **AC-02:** Khi không có khung giờ giao nhau, B không được đề xuất lịch gặp tại thời điểm đó.
- **AC-03:** Nếu thiếu timezone hợp lệ, hệ thống xử lý theo quy tắc sản phẩm đã được phê duyệt, không tự đoán.

## Scope & nguồn

- Cần xác định function/module đang tính availability và bộ test đang sở hữu hành vi bằng code search; không giả lập tên path.
- Không làm: thay đổi toàn bộ ranking, lịch bên thứ ba hay cơ chế chốt lịch tự động.
- **Decision cần chốt:** độ dài tối thiểu của slot; quy tắc timezone và daylight saving theo trường hợp; đây là blocker nếu ảnh hưởng AC.

## Cách triển khai

1. Khảo sát logic overlap hiện hữu và các callers; ghi đúng owner của hành vi.
2. Bổ sung so khớp khung giờ tại đúng module; tránh một bộ lọc thứ hai song song.
3. Sửa hoặc bổ sung test hiện có cho đủ/thiếu overlap và dữ liệu không hợp lệ.

## Test mapping

| AC | Test | Tầng | Command + cwd | Trạng thái |
|---|---|---|---|---|
| AC-01 | slot hợp lệ | unit | xác minh theo `PROJECT_PROFILE.md` | NOT_RUN |
| AC-02 | không có overlap | unit | xác minh theo `PROJECT_PROFILE.md` | NOT_RUN |
| AC-03 | timezone thiếu/sai | unit hoặc integration nếu boundary liên quan | xác minh | NOT_RUN |

**Trước bàn giao:** targeted → module → required CI thật (build/lint/unit/business_regression nếu policy áp dụng); báo evidence theo revision, không tự khẳng định PASS.
