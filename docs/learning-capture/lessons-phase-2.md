# 📓 Lessons — Phase 2 (System Design)

> Bài học/khái niệm. Quyết định thực tế nằm ở `build-journal/phase-2-system-design.md`.

---

## 💡 L1 — Fan-Out / Fan-In (trái tim Scenario D)

- **Fan-OUT:** từ 1 request, *bung ra* gọi nhiều nguồn **CÙNG LÚC** (không tuần tự).
- **Fan-IN:** *gom* các kết quả về một mối, gộp thành một output.

**Vì sao nó quan trọng — con số biết nói:**
| Cách | Tổng thời gian |
|------|----------------|
| Tuần tự (Sales xong → Service) | 200ms + 200ms = **400ms** |
| Fan-out (đồng thời) | max(200, 200) = **~200ms** |

→ Ông sales đang ngồi với khách. Fan-out **cắt đôi** thời gian chờ. Đây là *performance*
suy ra trực tiếp từ user. Trong code: `Promise.all` (Node) / `asyncio.gather` (Python) /
`ThreadPoolExecutor`.

**Câu nói khi phỏng vấn:** *"Em fan-out 2 lời gọi đồng thời để latency = nguồn chậm nhất,
không phải tổng hai nguồn."*

---

## 💡 L2 — Adapter Pattern / Anti-Corruption Layer (ACL)

Mỗi nguồn ngoài nói "tiếng" riêng (`docName`, `price`… vs `title`, `serviceDate`…). Mình
**không** để cái lộn xộn của tụi nó tràn vào lõi hệ thống. Mỗi nguồn có một **adapter** —
"người phiên dịch" — dịch response của nó về **một domain model chung** (unified Document).

**Lợi ích:**
- Mai Sales API đổi format → chỉ sửa **MỘT adapter**, lõi không đụng.
- Lõi (Aggregator) chỉ làm việc với một khuôn duy nhất → đơn giản, dễ test.

**Câu nói khi phỏng vấn:** *"Em đặt Anti-Corruption Layer ở biên: mỗi external API có một
adapter dịch về domain model chung. Format ngoài đổi thì chỉ một adapter đổi."* → cân câu
hỏi về **maintainability**.

---

## 💡 L3 — Separation of Concerns (SoC): Controller vs Aggregator

**SoC = mỗi phần lo ĐÚNG MỘT việc, không lấn sân.** Trong Django của mình nó đã có sẵn:

| Tên "sang" | = trong Django | Lo việc gì |
|---|---|---|
| **Controller** | `views.py` (cái "view") | Nhận HTTP request, lấy VIN, trả JSON + status code. **Chỉ HTTP.** |
| **Aggregator** | một class/hàm trong `/services/` | fan-out, gộp, tag nguồn, xử lý lỗi. **Chỉ business logic.** |

**Vì sao quý:**
- View đổi (REST → GraphQL) → business logic không đụng.
- Test business → gọi thẳng service, **khỏi dựng HTTP** → test nhanh, gọn.
- Đọc code biết ngay: lỗi HTTP tìm ở view, lỗi logic tìm ở service.

Ngược lại nhét hết vào view = một cục 200 dòng, sửa một chỗ vỡ ba chỗ. SoC = *"mỗi nhạc
cụ chơi đúng bè của nó."* 🎹

## 💡 L4 — I/O-bound vs CPU-bound → chọn concurrency cho đúng

Vấn đề fan-out của mình là **I/O-bound** (ngồi *chờ* mạng), không phải CPU-bound. Với
I/O-bound, **threads (`ThreadPoolExecutor`) là đủ**: thread này chờ mạng thì Python thả
thread kia chạy. **Async** chỉ thắng đậm khi có *hàng nghìn* lời gọi đồng thời — mình chỉ
có **2**. → Chọn công cụ theo *bản chất bài toán*, không theo độ "hot" của công nghệ.

---

## 💡 L5 — Graceful degradation: thiết kế response cho lỗi từng phần

**Hai nguyên tắc xương sống khi 1 nguồn trong fan-out chết:**

**(a) Tách DATA khỏi META.**
- `documents` = chỉ chứa dữ liệu THẬT, sạch tuyệt đối.
- `sources` (META) = báo sức khoẻ từng nguồn riêng một khu.
- ❌ Anti-pattern: nhét "nguồn lỗi" thành một document giả toàn `null` → rác trộn vào data,
  client lặp qua list sẽ vẽ ra dòng rỗng hỏng.

**(b) HTTP status phải phân biệt "không có dữ liệu" với "không liên lạc được".**
| Ca | Status | |
|----|--------|--|
| ≥1 nguồn OK (kể cả 0 giấy) | **200** | có data hữu ích → degradation báo trong body |
| Cả 2 nguồn chết | **502** | total upstream failure → lỗi thật, nói thẳng |

→ Nếu cả 2 ca đều trả `200 documents:[]`, client không biết "xe sạch giấy" hay "hệ thống
cháy". *Hai thứ đó không được trông giống nhau.*

**Bonus khoe hiểu biết:** nhắc `207 Multi-Status` tồn tại cho partial, rồi giải thích vì
sao bỏ (ít client hiểu) → cho thấy mình *biết* lựa chọn, không phải không biết.

---

## 💡 L6 — "Vì sao app này CẦN database?" + design-for lặp lại + non-blocking write

**(a) DB phục vụ nhu cầu của RIÊNG app, không lưu hộ data người khác.**
Documents thuộc 2 nguồn ngoài → mình không sở hữu. Vậy DB của mình lưu cái gì *của mình*:
**audit log** (ai tra xe nào, lúc nào, nguồn nào sống/chết) → observability/compliance.
→ Luôn hỏi *"vì sao cần DB?"* và trả lời bằng **lý do nghiệp vụ**, không phải "vì đề bắt".

**(b) Pattern "DESIGN-FOR, không BUILD-NOW" LẶP LẠI.**
Lần 1: auth + multi-tenancy (ADR-002). Lần 2: cache (ADR-005). Cùng một khuôn: thứ **thật
và đáng** nhưng **không thuộc lõi** → ghi future work kèm *use case + chỗ chen vào*, không
build V1. Biết hoãn cái gì = kỹ năng scope, không phải bỏ sót.

**(c) Cache đắt hơn vẻ ngoài.** *"Hai bài khó nhất ngành: đặt tên biến + cache invalidation."*
Bản cache cũ-sai đưa cho user trước mặt khách → tệ hơn không cache. TTL/staleness/invalidation
ngốn thời gian → cân nhắc kỹ trước khi build trong deadline ngắn.

**(d) Non-blocking persistence.** Ghi audit log **SAU KHI** đã trả response cho user → user
không phải chờ I/O ghi DB. Việc "kế toán nội bộ" không được làm chậm "trải nghiệm khách".

---

## 💡 L7 — Graceful Degradation (khái niệm xương sống)

**Định nghĩa:** khi MỘT phần hỏng, cả hệ thống vẫn chạy ở mức thấp hơn — **thay vì chết sạch.**
- *Degradation* = xuống cấp (thiếu một phần).
- *Graceful* = lịch sự (không sụp đổ, không la làng).

**Metaphor nhà hàng 🍽️:** máy kem hư.
- 😡 Nhà hàng tệ → *"đóng cửa, mời về"* = **catastrophic failure** (1 thứ hỏng → sập hết).
- 😌 Nhà hàng lịch sự → *"hết kem thôi, còn lại đủ hết"* = **graceful degradation** (vẫn ăn ngon).

**Trong app:** Service API chết → vẫn đưa giấy của Sales + ghi chú *"Service tạm thiếu"*.
Ông sales vẫn làm việc được, và biết vì sao thiếu.

**Trong CODE, nó là gì?** Một câu **`try/except` đặt ĐÚNG CHỖ** — trong từng adapter. Adapter
"nuốt" lỗi của riêng nó, biến exception thành một dòng status nhẹ nhàng (`unavailable`), để
request vẫn diễn ra. Mỗi adapter = một bồi bàn lịch sự riêng cho nguồn của nó; đứa chết tự
biến thành lời nhắn, không kéo sập đứa còn sống.

> Graceful degradation không phải phép màu — nó là **vị trí đặt `try/except`.**

---

## 💡 L8 — "Slow is the new down": timeout cho mọi external call

Nguồn **treo** (hanging — chậm mà không chết hẳn) **tệ hơn** nguồn chết: không có exception
để bắt, người dùng chờ vô hạn, lợi ích fan-out tan biến.

- Luôn đặt **timeout** cho lời gọi mạng. Hết giờ = coi như `unavailable` → degrade.
- Để timeout **configurable** (env), đừng hardcode → tune theo p99 latency thật, không đoán mò.
- Tư duy: *"một nguồn chậm cũng tệ ngang một nguồn chết — với người đang chờ."*
