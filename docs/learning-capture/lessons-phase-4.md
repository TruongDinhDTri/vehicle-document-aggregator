# 📓 Lessons — Phase 4 (Database Design)

> Bài học. Quyết định thực tế ở `build-journal/phase-4-database.md` + ADR-007.

---

## 💡 L1 — Entity = thứ MÌNH cần nhớ (không phải mọi danh từ)

Tìm entity bằng cách gạch danh từ trong user stories — NHƯNG một danh từ chỉ thành bảng nếu
**mình cần lưu data về nó.** Document (nguồn ngoài lưu), vehicle (không sở hữu), user (auth
hoãn) → đều KHÔNG lưu. Chỉ còn **audit log**. → Đừng tạo bảng cho thứ mình không sở hữu/không cần.

## 💡 L2 — 1NF: mỗi ô một giá trị nguyên tử (atomic)

**1NF = no array, no comma-separated list trong một cột.** Một cột JSON `[{source,status},...]`
→ **vi phạm 1NF**. Cách sạch cho số nguồn cố định nhỏ: **mỗi nguồn một cột atomic**.

## 💡 L3 — Anti-pattern "wide table" + cách normalize 1:N

**Wide table** (mỗi nguồn 1 cột, scale tới 100 cột):
- Thêm nguồn → `ALTER TABLE` (đổi schema mỗi lần). Bảng **sparse** đầy NULL. Query khổ.

**Cách chuẩn — bảng con 1:N:**
```
SearchAuditLog (cha)         SearchSourceResult (con)
 id | vin | created_at        id | search_id(FK) | source | status
 1  | ... | ...               1  |      1        | SALES  | ok
                              2  |      1        | SERVICE| unavailable
```
- **FK nằm bên "many"** (SourceResult) trỏ về bên "one" (AuditLog).
- Thêm nguồn → chỉ **INSERT dòng**, không đổi schema.
- *"Nguồn nào hay chết nhất?"* → `WHERE source=.. AND status='unavailable'` → dễ.

## 💡 L4 — Biết khi nào DỪNG normalize (over-engineering ngược)

Bảng con 1:N đẹp hơn — nhưng đẻ ra bảng + FK. Với **2 nguồn cố định**, 2 cột atomic là đủ và
đơn giản nhất. → Làm chủ = biết **cả hai** (cái đơn giản xây bây giờ + cái sẽ-lớn-thành), và
biết **khi nào chưa cần** cái phức tạp. Đừng normalize cho thứ chưa động.
