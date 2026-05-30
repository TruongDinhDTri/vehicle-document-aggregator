# 🧭 Decision Log (ADR — Architecture Decision Records)

> Keyloop sẽ hỏi: *"Vì sao mỗi quyết định lại chọn vậy? Đã cân nhắc gì khác? Đánh đổi gì?"*
> Cuốn sổ này có sẵn đạn. Mỗi quyết định: **Context → Decision → Alternatives → Trade-offs
> → câu trả lời phỏng vấn**.

---

## ADR-001 — Build **Backend** (mock Frontend)
- **Status:** ✅ Accepted
- **Context:** Đề cho build trọn 1 layer, mock layer kia. Linh hồn Scenario D nằm ở
  server-side aggregation.
- **Decision:** Build Backend (RESTful API + DB thật). Mock client bằng test harness / cURL.
- **Alternatives:** Frontend (build UI, mock backend bằng static JSON) — khoe UX nhưng phần
  hệ-phân-tán nhẹ đô.
- **Trade-offs:** Mất phần demo UX bóng bẩy; ĐỔI LẠI nắm đúng phần được chấm sâu nhất.
- **Câu trả lời phỏng vấn:** *"Phần khó của D là gộp dữ liệu phía server + lỗi từng phần —
  đó là backend. Em build backend để làm chủ đúng chỗ đang bị đánh giá."*

---

## ADR-002 — Scope: **DESIGN-FOR, không BUILD-NOW** (auth + multi-tenancy OUT khỏi V1)
- **Status:** ✅ Accepted
- **Context:** User là một đội ở nhiều đại lý → ngụ ý cần login + multi-tenancy. Nhưng 3
  yêu cầu cốt lõi không đòi; chỉ có ~2 ngày.
- **Decision:** V1 KHÔNG build login/multi-tenancy. Ghi vào Design Doc mục scalability,
  kiến trúc chừa chỗ.
- **Alternatives:** Build auth + tenancy ngay → cạn giờ, trái tim làm dở.
- **Trade-offs:** V1 chưa production-secure; ĐỔI LẠI làm TRỌN phần lõi.
- **Câu trả lời phỏng vấn:** *"Em design-for multi-tenancy/auth nhưng không build trong V1
  để dồn sức ship trọn fan-out + aggregation. Làm trọn một thứ hơn làm dở giấc mơ to."*

---

## ADR-003 — **DRF + ThreadPoolExecutor** cho fan-out đồng thời
- **Status:** ✅ Accepted
- **Context:** Cần gọi 2 external API **đồng thời** (I/O-bound); 2 ngày; mạnh Django REST.
- **Decision:** Django REST Framework (sync) + `concurrent.futures.ThreadPoolExecutor` để
  gọi song song; HTTP client `requests`.
- **Alternatives:**
  - **B.** Django async view + `httpx` + `asyncio.gather` → DRF chưa async đầy đủ, dễ vướng
    ổ gà trong 2 ngày.
  - **C.** FastAPI async-native → hợp fan-out nhất nhưng là framework mới phải học.
- **Trade-offs:** Threads "cũ" hơn async; GIL không sao vì I/O-bound; không scale tới hàng
  nghìn lời gọi đồng thời (mình chỉ có 2).
- **Câu trả lời phỏng vấn:** *"I/O-bound, chỉ 2 nguồn → threads đủ đồng thời. Giữ DRF để
  ship kịp, tránh phức tạp async tới khi quy mô đòi. Hàng trăm nguồn thì em chuyển async."*

---

## ADR-004 — Hợp đồng response cho **Partial Failure** (`sources` + 200/502)
- **Status:** ✅ Accepted
- **Context:** Fan-out tới 2 nguồn → 1 hoặc cả 2 có thể chết (timeout/500). Phải báo cho
  client mà KHÔNG phá graceful degradation, và phải phân biệt được "xe không có giấy" với
  "hệ thống sập".
- **Decision:**
  - Tách **DATA / META**: `documents` chỉ chứa giấy THẬT (sạch); `sources` là khu riêng báo
    status từng nguồn (`ok` / `unavailable` + `error`).
  - **≥ 1 nguồn OK → HTTP 200** (kể cả nguồn đó trả 0 giấy).
  - **Cả 2 nguồn chết → HTTP 502 Bad Gateway** (total upstream failure).
  - VIN sai định dạng → 400 (validate ở controller).
- **Alternatives:**
  - Nhét nguồn-lỗi thành **document giả toàn `null`** trong list → rác trộn vào data, client
    vẽ ra dòng rỗng hỏng. ❌
  - **Luôn 200** kể cả chết hết → client không phân biệt "xe trống" với "hệ thống sập". ❌
  - **207 Multi-Status** → đúng học thuật nhưng ít client hiểu, thêm phức tạp vô ích.
  - **500 khi 1 nguồn chết** → mất trắng phần dữ liệu nguồn còn sống → giết degradation. ❌
- **Trade-offs:** Client phải đọc thêm `sources` để biết degradation; phải xử lý 2 nhánh
  (200 vs 502). ĐỔI LẠI: ngữ nghĩa rõ ràng, an toàn, đúng tinh thần hệ phân tán.
- **Câu trả lời phỏng vấn:** *"Partial → 200 vì vẫn có data hữu ích; degradation là trạng
  thái bình thường của hệ phân tán nên em báo trong body (`sources`), không phải bằng HTTP
  error. Total upstream failure → 502 để client phân biệt 'xe không có giấy' với 'mọi nguồn
  sập' — hai thứ đó không được trông giống nhau."*

---

## ADR-005 — Persistence: V1 = **Audit Log**; **Cache = design-for** (future work)
- **Status:** ✅ Accepted
- **Context:** Đề bắt backend có persistent DB. Nhưng documents **thuộc 2 nguồn ngoài**, không
  phải data của mình → câu hỏi thật: *"lưu CÁI GÌ cho có lý do, thay vì lưu cho có?"*
- **Decision:**
  - V1 build **Search Audit Log**: mỗi lượt tra ghi `vin`, thời điểm, (user sau này), nguồn
    nào `ok`/`unavailable`. Ghi **non-blocking** (sau khi đã trả response) → KHÔNG làm ông
    sales phải chờ.
  - **Cache** (lưu list document đã gộp theo VIN, có TTL) → **DESIGN-FOR, không build V1**.
    Ghi vào Design Doc "future work" kèm use case + chỗ chen vào (lớp cache trước Aggregator).
- **Alternatives:**
  - Build cache ngay V1 → tốn thời gian (invalidation / TTL / staleness); rủi ro đưa bản
    cache **cũ sai** cho sales trước mặt khách → tệ hơn không cache. ❌
  - Không có DB / lưu vu vơ cho đủ đề → không có lý do nghiệp vụ, phí công. ❌
- **Trade-offs:** Audit log KHÔNG tăng tốc tra cứu (không phải mục tiêu của nó); cache bị
  hoãn nên lượt tra lặp lại vẫn gọi 2 nguồn mỗi lần. ĐỔI LẠI: V1 gọn, đúng trọng tâm.
- **Use case cache (ghi cho future work):** ông sales chèo kéo MỘT khách nhiều ngày → tra
  cùng VIN nhiều lần → cache (TTL ngắn) cắt lời gọi lặp + còn data tạm khi nguồn chết.
- **Câu trả lời phỏng vấn:** *"Documents thuộc nguồn ngoài, nên DB của em phục vụ nhu cầu
  của RIÊNG app: audit log — ai tra xe nào lúc nào, phục vụ observability/compliance. Em ghi
  non-blocking nên không chậm hot path. Cache em design-for cho repeat-lookup trong chu kỳ
  bán kéo dài nhiều ngày, nhưng hoãn build để tránh bẫy cache-invalidation trong 2 ngày."*

---

## ADR-006 — **Timeout 5s** mỗi external call (configurable)
- **Status:** ✅ Accepted
- **Context:** Nguồn **treo** (chậm, không chết hẳn) phá lợi ích fan-out — ông sales ngồi
  chờ trước mặt khách vì một nguồn rùa bò. "Slow ngang với dead" đối với người đang chờ.
- **Decision:** Mỗi lời gọi external có **timeout 5s**, đặt qua **config/env** (không
  hardcode). Hết giờ → coi như `unavailable` → degrade (ADR-004).
- **Alternatives:**
  - Không timeout → treo vô hạn, request không bao giờ xong. ❌
  - 2–3s → an toàn UX hơn nhưng dễ "bỏ cuộc" khi mạng chỉ hơi lề mề.
  - >5s → khách chờ lâu phát cáu.
- **Trade-offs:** 5s có thể hơi lâu với người sốt ruột; ĐỔI LẠI tha thứ cho mạng chậm. Vì
  **configurable** nên tune được theo p99 latency thật.
- **Câu trả lời phỏng vấn:** *"Slow ngang dead với người đang chờ. Em đặt timeout 5s làm
  điểm khởi đầu, configurable để tune theo latency thật; hết timeout thì coi như unavailable
  và degrade — không để một nguồn treo kéo sập cả request."*

---

## ADR-007 — Audit log: **2 cột atomic** cho kết quả nguồn (không JSON / wide / child table)
- **Status:** ✅ Accepted
- **Context:** Cần ghi kết quả mỗi nguồn (sales/service ok hay chết) cho observability. V1 có
  **2 nguồn cố định**.
- **Decision:** 2 cột atomic `sales_status` + `service_status` (+ `document_count`). Sạch **1NF**.
- **Alternatives:**
  - **JSON array** `[{source,status}]` → **vi phạm 1NF** (mảng trong 1 ô), khó query. ❌
  - **Wide table** (1 cột/nguồn, scale tới 100 cột) → sparse NULL, `ALTER TABLE` mỗi lần thêm
    nguồn, query khổ. ❌
  - **Child table `SearchSourceResult` (1:N)** → đúng chuẩn cho N nguồn động, nhưng đẻ thêm
    bảng + FK → **over-engineer** cho 2 nguồn cố định ở V1.
- **Trade-offs:** Thêm nguồn thứ 3 phải đổi schema; ĐỔI LẠI đơn giản nhất + dễ query cho V1.
- **Câu trả lời phỏng vấn:** *"V1 dùng 2 cột atomic — sạch 1NF cho 2 nguồn cố định. Nếu nguồn
  động/nhiều, em normalize ra child table `SearchSourceResult` 1:N (FK ở bên 'many'). Em biết
  chính xác đường đó nhưng không xây sớm khi chưa cần."*

---

## ADR-00X — _(template cho quyết định kế)_
- **Status:** Proposed
- **Context:**
- **Decision:**
- **Alternatives:**
- **Trade-offs:**
- **Câu trả lời phỏng vấn:**
