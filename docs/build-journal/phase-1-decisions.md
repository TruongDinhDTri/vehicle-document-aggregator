# PHASE 1 — Decisions (Ideation & Requirements)

> Đây là **những gì mình QUYẾT build**. Bài học rút ra nằm ở `learning-capture/`.

```
✅ 1.1  Problem statement
✅ 1.2  Target user
✅ 1.3  MoSCoW
✅ 1.4  User stories
✅ 1.5  MVP scope
```
> **PHASE 1 — ĐÓNG SỔ ✅** Sẵn sàng sang Phase 2 (System Design).

---

## 1.1 — Problem Statement (CHỐT)

> Mỗi ngày, một nhân viên ở đại lý ô tô phải **lục qua hai cuốn sổ tách biệt** để ghép cho
> đủ hồ sơ của **một** chiếc xe: một cuốn ghi chuyện mua bán (giá, ngày sản xuất…), một
> cuốn ghi chuyện chăm sóc xe (bảo dưỡng hồi nào, thay nhớt, thay phụ tùng chưa…). Việc
> **đi qua đi lại giữa hai nơi** vừa chậm, vừa mệt, vừa dễ sót. Anh ta cần **một chỗ duy
> nhất**: gõ con số định danh của chiếc xe là **lập tức** thấy toàn bộ giấy tờ từ **cả hai
> cuốn sổ** hiện ra cùng lúc — **biết rõ mỗi tờ đến từ đâu** — để không bao giờ phải lục
> lọi thủ công nữa.

---

## 1.2 — Target User (CHỐT)

- **Ai:** Nhân viên **sales đang chốt deal** (khách ngồi ngay đó).
- **Quy mô:** **Một đội** cùng xài (nhiều người).
- **Phạm vi:** **Nhiều đại lý** (multi-tenant).

**Hệ quả → định hình kiến trúc:**
| Đặc điểm user | Kéo theo |
|---|---|
| Sales chốt deal, khách chờ | **Performance** → gọi 2 nguồn **song song** |
| Một đội cùng xài | Đăng nhập / danh tính |
| Nhiều đại lý | Tách dữ liệu theo đại lý (**multi-tenancy**) |

**Quyết định scope — "DESIGN FOR IT, không BUILD IT NOW" (chọn B):**
> Login + multi-tenancy → **ghi vào System Design Doc** mục scalability, kiến trúc chừa chỗ.
> **V1 KHÔNG build.** Dồn sức cho trái tim: fan-out 2 API song song + gộp + xử lý lỗi từng phần.

---

## 1.3 — MoSCoW (CHỐT)

| Nhóm | Feature | Ghi chú |
|------|---------|---------|
| 🔴 **MUST** | Tìm xe bằng **VIN** (1 ô search) | yêu cầu cốt lõi #1 |
| 🔴 **MUST** | Gọi **SONG SONG** 2 API (Sales + Service) | yêu cầu cốt lõi #2 — trái tim |
| 🔴 **MUST** | Gộp **1 danh sách**, **ghi rõ nguồn** mỗi doc | yêu cầu cốt lõi #3 |
| 🔴 **MUST** | **1 nguồn chết → vẫn trả phần còn lại + báo lỗi 1 phần** | graceful degradation (HÀNH VI) |
| 🟡 **SHOULD** | Lưu **DB thật** (đề bắt backend có persistent DB) | persist cái gì → quyết ở Phase 2 |
| 🟡 **SHOULD** | Structured logging (observability) | |
| 🟢 **COULD** | Trả kèm field **`documentUrl`** mỗi doc (passthrough) | gần như free — GIỮ |
| 🟢 **COULD** | Lọc / sắp xếp / phân trang | nếu dư giờ |
| 🟢 **COULD** | Resilience xịn: retry / circuit breaker / cache | "đồ chơi" nâng cao của degradation |
| ⚫ **WON'T (V1)** | Đăng nhập / phân quyền | design-for |
| ⚫ **WON'T (V1)** | Multi-tenancy | design-for |
| ⚫ **WON'T (V1)** | Xây trình **xem/tải file thật** | chỉ trả metadata + `documentUrl` |

---

## 1.4 — User Stories (CHỐT)

> Format: *As a [user], I want [action], so that [benefit].* — zero từ kỹ thuật.

1. **As a salesperson,** tôi muốn **tra một chiếc xe bằng số định danh của nó**, *để* tôi tìm ra nó ngay mà không cần nhớ giấy tờ nằm ở đâu.
2. **As a salesperson,** tôi muốn **mọi giấy tờ của chiếc xe gom về một danh sách duy nhất**, *để* tôi không phải tra hai nơi.
3. **As a salesperson,** tôi muốn **mỗi tờ giấy ghi rõ nó đến từ đâu**, *để* tôi tin và truy ngược được thông tin trước mặt khách.
4. **As a salesperson,** tôi muốn **vẫn xem được phần giấy tờ còn lại khi một nguồn trục trặc**, *để* một sự cố hệ thống không làm hỏng cuộc chốt deal.

---

## 1.5 — MVP Scope (CHỐT)

**⏱️ Ngân sách: ~2 ngày** (design doc + code + tests + video). Triết lý: **vertical slice chạy
được end-to-end > nhiều feature nửa vời.**

| | Làm gì |
|---|---|
| **Ngày 1** | System Design Doc + skeleton backend + vertical slice trái tim (`VIN → fan-out 2 mock API → gộp + tag nguồn`) + graceful degradation |
| **Ngày 2** | Persistence (gọn) + structured logging + tests core logic + README (AI Collaboration Narrative) + quay video |

**✅ IN (V1 phải ship):**
- Search bằng VIN
- Gọi **song song** 2 mock API
- Gộp 1 list + tag nguồn + field `documentUrl`
- 1 nguồn chết → vẫn trả phần còn lại
- DB thật (gọn — persist cái gì chốt ở Phase 2)
- Structured logging (gọn)
- Tests core business logic

**⛔ OUT (dứt khoát):**
- Đăng nhập / multi-tenancy (design-for, không build)
- Trình xem/tải file thật
- Retry / circuit breaker / cache
- Lọc / sắp xếp / phân trang
