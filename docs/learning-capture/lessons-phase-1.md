# 📓 Lessons — Phase 1 (Ideation & Requirements)

> Bài học rút ra. Quyết định thực tế (problem, user, MoSCoW…) nằm ở
> `build-journal/phase-1-decisions.md`.

---

## 💡 L1 — Problem statement là NỖI ĐAU, không phải GIẢI PHÁP

Bẫy: nhảy ngay vào *"tôi build app gọi 2 API gộp tài liệu."* Đó là giải pháp.
Bài: mô tả **sự bực bội của con người** trước, **zero từ kỹ thuật**. Test: kể trong 1 đoạn,
không một chữ API/VIN/backend/parallel. Vượt được test = đã hiểu *vì sao* app tồn tại.

## 💡 L2 — User định hình kiến trúc (không phải ngược lại)

Từ một câu tả user, suy ra được cả hệ thống:
- "sales đang chốt deal" → **performance** → gọi song song.
- "một đội cùng xài" → đăng nhập.
- "nhiều đại lý" → **multi-tenancy**.
→ Kiến trúc sư đọc user ra requirements, không bịa từ trên trời.

## 💡 L3 — "DESIGN FOR IT" ≠ "BUILD IT NOW"

Giấc mơ to (login, multi-tenant) là thật → **ghi vào design doc**, kiến trúc chừa chỗ.
Nhưng **không build** trong V1. Phân biệt được hai động từ này = làm chủ scope. Đây là
câu trả lời mạnh khi phỏng vấn: *"em design-for nó, nhưng V1 em không build, để làm trọn trái tim."*

## 💡 L4 — MoSCoW là cái KHIÊN; danh sách WON'T quan trọng ngang MUST

Must giữ ở 3–5 mục. Cái "Won't Have" viết rõ ra để **chặn scope creep**. Không có Won't list,
mọi ý tưởng hay đều luồn vào và bài làm phình ra tới chết.

## 💡 L5 — MUST là HÀNH VI, không phải BỘ ĐỒ NGHỀ

"1 nguồn chết → vẫn hiện phần còn lại" là **MUST** (hành vi: graceful degradation).
Nhưng retry / circuit breaker / cache là **COULD** (đồ nghề nâng cao). Tách hai tầng này =
khoe "hiểu degradation" mà **không over-engineer**. Để degradation ở Should là rủi ro bị
cắt lúc hết giờ — và trái tim Scenario D ngừng đập.

## 💡 L6 — Một user story = MỘT nhu cầu; scope creep luồn vào qua câu nghe rất hợp lý

Lỗi đã vấp: viết 1 story nhét 3 nhu cầu (gộp + link + degradation). Khi test không biết
"done" là done cái nào. Và chính chữ "kèm link đọc thêm" đã **lén kéo một Won't-Have(V1) trở lại**.
Bài: tách mỗi story một nhu cầu; cảnh giác scope creep núp trong câu chữ tử tế.

## 💡 L7 — Giới hạn giờ → vertical slice, không phải nhiều mảnh rời

2 ngày là constraint. Constraint sinh ra sự rõ ràng. Quy tắc: **một lát dọc chạy được
end-to-end** (`VIN → 2 nguồn song song → gộp → trả về + degradation`) — *demo được, test được,
kể được* — **thắng** năm feature nửa vời không ráp thành câu chuyện. Ship cái xương sống trước,
phình ra sau nếu dư giờ.

---

## 📌 User Stories (lưu kèm ở đây theo yêu cầu — bản chốt ở build-journal)

1. **As a salesperson,** tôi muốn **tra một chiếc xe bằng số định danh của nó**, *để* tôi tìm ra nó ngay mà không cần nhớ giấy tờ nằm ở đâu.
2. **As a salesperson,** tôi muốn **mọi giấy tờ của chiếc xe gom về một danh sách duy nhất**, *để* tôi không phải tra hai nơi.
3. **As a salesperson,** tôi muốn **mỗi tờ giấy ghi rõ nó đến từ đâu**, *để* tôi tin và truy ngược được thông tin trước mặt khách.
4. **As a salesperson,** tôi muốn **vẫn xem được phần giấy tờ còn lại khi một nguồn trục trặc**, *để* một sự cố hệ thống không làm hỏng cuộc chốt deal.
