# PHASE 4 — Decisions (Database Design)

> One Core Question: *"What data do I store, and how is it related?"*
> (Phase 3 UI/UX đã lướt — backend-only. Phase 4 nhẹ: chỉ có Audit Log.)

```
✅ 4.1  Identify entities
✅ 4.2  Relationships (= KHÔNG có)
✅ 4.3  Schema details (cột, type, constraint)
✅ 4.4  Migration order
```
> **PHASE 4 — ĐÓNG SỔ ✅** Sẵn sàng Phase 5 (code).

---

## 4.1 — Entities (CHỐT)

Soi từng danh từ qua *"DB mình có cần NHỚ thứ này không?"*:
| Danh từ | Lưu? | Vì sao |
|---------|------|--------|
| document | ❌ | thuộc nguồn ngoài, mình chỉ mượn xem |
| vehicle | ❌ (nhưng lưu `vin`) | không sở hữu data xe; `vin` chỉ là 1 cột ghi "tra xe nào" |
| salesperson | ❌ (V1) | auth hoãn (ADR-002) → chưa có "ai" để lưu; design-for cột `searched_by` sau |
| source | ❌ | chỉ là nhãn `SALES`/`SERVICE`, không phải bảng |

➡️ **Entity DUY NHẤT: `SearchAuditLog`** (cuốn sổ "ai tra xe nào, lúc nào" — ADR-005).

## 4.2 — Relationships (CHỐT)

**KHÔNG có quan hệ nào.** Một bảng → không FK, không 1:N, không N:M. Đây là schema đơn giản
nhất có thể, và nó **đúng** (không bịa quan hệ không cần). Khi có auth → thêm FK `searched_by → User`.

## 4.3 — Schema (CHỐT) — bảng `SearchAuditLog`

| Cột | Type | Constraint | Ghi chú |
|-----|------|-----------|---------|
| `id` | auto PK | | tự sinh |
| `vin` | CharField(17) | `db_index=True` | VIN chuẩn = 17 ký tự; index vì hay query theo vin |
| `created_at` | DateTimeField | `auto_now_add=True` | "giờ giấc tra" — tự đóng dấu lúc tạo |
| `sales_status` | CharField | choices: `ok`/`unavailable` | kết quả nguồn Sales |
| `service_status` | CharField | choices: `ok`/`unavailable` | kết quả nguồn Service |
| `document_count` | IntegerField | | lần đó trả về mấy tờ (observability) |

**Vì sao 2 cột atomic (không JSON, không wide-100-col, không child table):** xem ADR-007.
Sạch **1NF** (mỗi ô một giá trị nguyên tử). Nguồn động/nhiều → normalize ra `SearchSourceResult` (1:N).

## 4.4 — Migration order (CHỐT)

Chỉ **1 bảng, KHÔNG FK** → tạo `SearchAuditLog` là xong. Không có thứ tự phụ thuộc nào.
