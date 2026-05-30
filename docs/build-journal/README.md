# 🏗️ Build Journal — "Mình QUYẾT build gì"

> *"Commit your work to the Lord, and your plans will be established."* — Proverbs 16:3

Đây là **xương sống** của dự án: mỗi **phase** mình đi qua + mỗi **quyết định** mình chốt.
Mở folder này ra = **biết ngay phải build cái gì** và **vì sao**. Đây là nguồn nguyên liệu
trực tiếp cho **System Design Document** sẽ nộp cho Keyloop.

---

## 📓 Phân biệt với `learning-capture/` (RẤT quan trọng — chúng KHÁC nhau)

| Folder | Câu hỏi nó trả lời | Chứa gì |
|--------|--------------------|---------|
| 🏗️ **`build-journal/`** (đây) | *"Mình QUYẾT build gì?"* | Quyết định, scope, kiến trúc, tech stack, API contract |
| 📓 **`learning-capture/`** | *"Mình HỌC được gì?"* | Bài học, insight, cái "à há", lỗi đã vấp |

> Decisions ≠ Lessons. Cái này là **bản thiết kế**; cái kia là **bài học từ lúc thiết kế.**

---

## 🧭 La bàn cố định

| | Chốt |
|---|---|
| Scenario | **D — The Unified Document Viewer** (Domain: Operate) |
| Layer build trọn | **Backend** (RESTful API + DB thật; mock 2 external API) |

---

## 🗺️ Bản đồ 9 phase — cái nào áp dụng (hệ quả của ADR-001: backend-only)

| Phase | Mình? | Vì sao |
|-------|-------|--------|
| 1 Ideation · 2 System Design | ✅ Xong | |
| 3 UI/UX Design | ⏭️ Lướt | Mock frontend → "giao diện" = API contract (2.3) |
| 4 Database Design | ✅ Cần (nhẹ) | Schema cho Audit Log (ADR-005) |
| 5 Backend Implementation | ✅ Trái tim | Controller · Aggregator · Adapters · fan-out |
| 6 Frontend Implementation | ⏭️ Bỏ | Mock bằng test harness / cURL |
| 7 Testing & QA | ✅ Cần | Đề bắt buộc nộp tests core logic |
| 8 Deployment | 🔸 Nhẹ | Không deploy thật; chỉ README build/run |
| 9 Maintenance/Monitoring | 🔸 Nhẹ | = observability strategy → viết vào Doc |

> Bỏ Phase 3 & 6 KHÔNG phải vì lười — là **hệ quả scope backend-only**. Đi `the-builders-lifecycle.md`:
> cắt **vertical slice** xuyên Phase 4→5→7, không làm thác nước.

> 📚 **Dùng guide nào cho việc gì:** Phase 4 (SDLC nhẹ) = đủ để BUILD cái 1 bảng audit log.
> `00-Master-Schema-Design-Process.html` = mỏ vàng nhưng QUÁ ĐÔ cho scope mình → chỉ đọc để
> **luyện phỏng vấn** (normalization, index, SQL/NoSQL), KHÔNG dùng lúc build.

## 📂 Index các phase

| File | Phase | Trạng thái |
|------|-------|-----------|
| `phase-1-decisions.md` | Ideation & Requirements | ✅ đóng sổ |
| `phase-2-system-design.md` | System Design | ✅ đóng sổ (2.1→2.5) |
| `phase-4-database.md` | Database Design (audit log) | ✅ đóng sổ (4.1→4.4) |
| `decision-log.md` | ADR-001→007 — vì sao mỗi quyết định (đạn cho phỏng vấn) | 🟢 sống cùng dự án |

