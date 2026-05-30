# PHASE 2 — Decisions (System Design)

> Map gần 1:1 với **System Design Document** nộp cho Keyloop. Mỗi mục chốt ở đây = một
> section trong Doc. Bài học rút ra nằm ở `learning-capture/`.

> One Core Question: *"How do all the parts connect, communicate, and handle data?"*

```
✅ 2.1  Architecture diagram
✅ 2.2  Tech stack (kèm lý do)
✅ 2.3  API endpoints
✅ 2.4  Data flow (trace 1 request)
✅ 2.5  External integrations
```
> **PHASE 2 — ĐÓNG SỔ ✅** Sẵn sàng viết code (vertical slice).
> Quyết định kèm "vì sao / alternatives / trade-offs" → ghi ở `decision-log.md` (ADR).

---

## 2.1 — Architecture Diagram (CHỐT)

```
┌─────────────┐
│   Client    │   (test harness / cURL — MOCK, vì mình build BACKEND)
│   gõ VIN    │
└──────┬──────┘
       │  GET /vehicles/{vin}/documents
       ▼
┌──────────────────────────────────────────────────────────────────┐
│                          OUR BACKEND                               │
│                                                                    │
│  ┌────────────┐   vin     ┌─────────────────────┐                 │
│  │ Controller │ ────────▶ │  Aggregator Service │                 │
│  │ (thin view)│ ◀──────── │   (the brain)       │                 │
│  └────────────┘  unified  │  • fan-out đồng thời │                 │
│        ▲          list     │  • fan-in (merge+tag)│                │
│        │                   │  • degradation       │                │
│   ┌─────────┐              └─────┬───────────┬────┘                │
│   │   DB    │           fan-out  │           │  fan-out            │
│   │persist? │                    ▼           ▼                     │
│   └─────────┘            ┌───────────┐ ┌───────────┐               │
│                          │  Sales    │ │  Service  │  Adapters     │
│                          │  Adapter  │ │  Adapter  │  (ACL / dịch) │
│                          └─────┬─────┘ └─────┬─────┘               │
└────────────────────────────────┼─────────────┼────────────────────┘
                                 ▼             ▼
                          ┌───────────┐ ┌────────────┐
                          │ Sales API │ │ Service API│   (MOCKED)
                          └───────────┘ └────────────┘

cross-cutting: structured logging ở mỗi trạm
```

**Vai trò từng trạm:**
| Trạm | Trách nhiệm | Delete test |
|------|-------------|-------------|
| **Controller (thin view)** | Nhận `GET /vehicles/{vin}/documents`, validate VIN, định hình response | Xoá → không có cửa vào API |
| **Aggregator Service** (lõi) | fan-out đồng thời 2 adapter, fan-in (gộp + tag nguồn), xử lý degradation | Xoá → mất trái tim Scenario D |
| **Sales / Service Adapter** (ACL) | Gọi 1 external API + **dịch** response về unified Document model | Xoá → lộn xộn format tràn vào lõi |
| **External mock APIs** | Giả lập Sales System + Service System | Đề bắt — nguồn dữ liệu |
| **DB** | Persist (cái gì → quyết ở 2.2/2.4) | đề bắt backend có persistent DB |

> Tách **Controller (mỏng)** khỏi **Aggregator (lõi)**: controller chỉ lo HTTP, aggregator
> lo business logic → dễ test lõi mà không cần dựng HTTP.

---

## 📦 Unified Document Model (data contract — CHỐT)

```jsonc
{
  "id":          "doc-123",            // mã riêng của tờ giấy
  "vin":         "WDB463...",          // thuộc xe nào
  "title":       "Sales Invoice #44",  // tên/loại — dịch từ docName HOẶC title
  "documentType":"INVOICE",            // INVOICE / SERVICE_REPORT / WARRANTY...
  "issuedDate":  "2024-03-12",         // ngày — dịch từ nguồn tương ứng
  "source":      "SALES",              // 👈 NGUỒN: "SALES" | "SERVICE"  (giải MUST #3)
  "documentUrl": "https://..."         // link passthrough (COULD — giữ)
}
```
> Mỗi adapter chịu trách nhiệm dịch response riêng của nó về đúng khuôn này.

## 2.2 — Tech Stack (CHỐT)

| Tầng | Công nghệ | Vì sao (không phải cái kia) |
|------|-----------|------------------------------|
| Ngôn ngữ | **Python** | Thế mạnh của mình → ship kịp 2 ngày |
| Web framework | **Django REST Framework (DRF)** | Quen, có sẵn routing/serializer/test client; giữ tốc độ |
| **Concurrency (fan-out)** | **`concurrent.futures.ThreadPoolExecutor`** | Bài toán **I/O-bound** chỉ **2 lời gọi** → threads đủ "đồng thời"; không gánh async khi quy mô chưa cần. (xem ADR-003) |
| HTTP client (gọi mock) | `requests` (sync) | Đi cặp tự nhiên với threads |
| DB | _(chốt ở 2.4 — persist cái gì)_ | đề bắt backend có persistent DB |
| Tests | `pytest` / DRF test client | test thẳng Aggregator (lõi) không cần HTTP |

**Lý do tổng (nói trước Keyloop):**
> *"Vấn đề là I/O-bound với chỉ 2 nguồn. Em chọn DRF + ThreadPoolExecutor: đủ để gọi đồng
> thời, giữ stack em thành thạo nên ship kịp 2 ngày, không gánh phức tạp async khi quy mô
> chưa cần. Fan-out lên hàng trăm nguồn thì em chuyển async — em design-for điều đó."*

## 2.3 — API Endpoints (CHỐT)

**Endpoint chính (gần như duy nhất):**
```
GET /vehicles/{vin}/documents
```
Đọc-to test: *"GET — vehicles — VIN này — documents"* → "Lấy danh sách document của xe theo VIN." ✅

**Response contract (hợp đồng với thế giới):**
```jsonc
{
  "vin": "WDB463...",
  "documents": [           // 👈 DATA: chỉ giấy THẬT, sạch tuyệt đối
    { "id": "doc-1", "vin": "...", "title": "Sales Invoice #44",
      "documentType": "INVOICE", "issuedDate": "2024-03-12",
      "source": "SALES", "documentUrl": "https://..." },
    { "id": "doc-2", "source": "SALES", ... }
  ],
  "sources": [             // 👈 META: sức khoẻ từng nguồn (tách khỏi data)
    { "source": "SALES",   "status": "ok" },
    { "source": "SERVICE", "status": "unavailable", "error": "timeout" }
  ]
}
```

**HTTP status codes:**
| Tình huống | Status | Vì sao |
|-----------|--------|--------|
| ≥ 1 nguồn OK (kể cả 0 giấy) | **200** | Phục vụ được; degradation báo trong `sources` |
| **Cả 2 nguồn chết** | **502 Bad Gateway** | Không có gì để trả vì mọi upstream sập → lỗi thật |
| VIN không hợp lệ | **400** | Controller validate trước khi fan-out |

> Nguyên tắc: HTTP status phải cho client phân biệt **"xe không có giấy" (200 rỗng)** với
> **"hệ thống sập" (502)** — hai thứ KHÔNG được trông giống nhau. Chi tiết → ADR-004.

## 2.4 — Data Flow (CHỐT — trace 1 request)

Hành động phức tạp nhất: **ông sales gõ VIN → nhận list document gộp.**

| # | Bước | Lỡ chết thì sao? |
|---|------|------------------|
| 1 | Client gọi `GET /vehicles/{vin}/documents` | — |
| 2 | **Controller** validate VIN (định dạng) | VIN sai → **400**, dừng, không fan-out |
| 3 | Controller gọi **Aggregator**(vin) | — |
| 4 | Aggregator **fan-out**: `ThreadPoolExecutor` submit 2 việc song song → Sales Adapter + Service Adapter | — |
| 5a | **Sales Adapter**: GET Sales API → dịch response về Unified Document | Lỗi/timeout → bắt exception, đánh dấu `SALES: unavailable` (KHÔNG ném ra ngoài) |
| 5b | **Service Adapter**: GET Service API → dịch về Unified Document | Lỗi/timeout → bắt, đánh dấu `SERVICE: unavailable` |
| 6 | Aggregator **fan-in**: gộp các document THÀNH CÔNG vào 1 list (mỗi tờ đã tag `source`); dựng mảng `sources` (ai ok/chết) | — |
| 7 | Quyết status: ≥1 nguồn ok → **200**; cả 2 chết → **502** | (chính là logic degradation) |
| 8 | Controller trả response (documents + sources) | — |
| 9 | **(non-blocking)** ghi Audit Log: vin, thời điểm, sources status | Lỗi ghi log → nuốt lỗi, KHÔNG ảnh hưởng response đã trả |

**Điểm sống còn:** bước 5 — adapter **tự nuốt lỗi của mình**, biến "API chết" thành "một
dòng status", chứ KHÔNG để exception nổ lên làm sập cả request. Đó là nơi graceful
degradation thật sự xảy ra trong code.

## 2.5 — External Integrations (CHỐT)

Hai nguồn: **Sales System API** + **Service System API** (MOCKED — nhưng thiết kế như thể thật).

| Vấn đề | Quyết định |
|--------|-----------|
| Config (base URL, key) | Để trong **env vars / config** — KHÔNG hardcode, KHÔNG lộ ra client |
| Nguồn down | Graceful degradation → `unavailable` trong `sources` (ADR-004) |
| Nguồn **treo/chậm** | **Timeout 5s/call, configurable** → hết giờ coi như `unavailable` (ADR-006) |
| Rate limit / cost | Mock nên N/A; nếu thật → cân nhắc cache (ADR-005 future) + backoff |

> Đinh quan trọng: **"slow ngang với dead"** đối với người đang chờ → timeout là bắt buộc.
