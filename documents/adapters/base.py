"""Unified domain model + Adapter contract (Anti-Corruption Layer).

Mỗi external system nói "tiếng" riêng (docName/price... vs title/serviceDate...).
Adapter dịch response của nó về `Document` chung này → lõi chỉ làm việc với MỘT khuôn.
Tham chiếu: build-journal/phase-2-system-design.md (Unified Document Model) + lessons L2 (ACL).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Optional


class SourceStatus:
    """Trạng thái một nguồn sau khi fan-out (khớp choices của SearchAuditLog)."""
    OK = "ok"
    UNAVAILABLE = "unavailable"


@dataclass
class Document:
    """Một tờ giấy tờ đã chuẩn hoá về khuôn chung của nhà mình (giải MUST #3 bằng `source`)."""
    id: str
    vin: str
    title: str
    document_type: str           # INVOICE / SERVICE_REPORT / WARRANTY...
    issued_date: str             # ISO date string, vd "2024-03-12"
    source: str                  # "SALES" | "SERVICE"
    document_url: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SourceResult:
    """Sức khoẻ của một nguồn — đi vào mảng `sources` của response (DATA vs META)."""
    source: str                  # "SALES" | "SERVICE"
    status: str                  # SourceStatus.OK | SourceStatus.UNAVAILABLE
    error: Optional[str] = None

    def to_dict(self) -> dict:
        data = {"source": self.source, "status": self.status}
        if self.error:
            data["error"] = self.error
        return data


class SourceAdapter:
    """Base ACL adapter. Mỗi nguồn kế thừa và tự dịch response → list[Document].

    Hợp đồng: `fetch(vin)` PHẢI tự nuốt lỗi của riêng nó (graceful degradation) — không để
    exception nổ ra ngoài làm sập fan-in. Trả về (documents, SourceResult).
    """
    source_name: str = ""        # "SALES" | "SERVICE"

    def fetch(self, vin: str) -> tuple[list[Document], SourceResult]:
        raise NotImplementedError
