"""Aggregator Service — THE BRAIN (build-journal phase-2 §2.1 + data flow §2.4).

Trách nhiệm (Separation of Concerns — không lo HTTP, chỉ lo business logic):
  • fan-out đồng thời 2 adapter (ThreadPoolExecutor) — "đồng thời", không tuần tự
  • fan-in: gộp document thành công thành 1 list (mỗi tờ đã tag `source`)
  • graceful degradation: 1 nguồn chết → vẫn trả phần còn lại + ghi `sources`

Đây là TRÁI TIM Scenario D. Lessons: L1 (fan-out/in), L7 (degradation).
"""
from __future__ import annotations

from dataclasses import dataclass

from documents.adapters.base import Document, SourceResult, SourceStatus


@dataclass
class AggregationResult:
    """Kết quả gộp — DATA (`documents`) tách khỏi META (`sources`) theo ADR-004."""
    vin: str
    documents: list[Document]
    sources: list[SourceResult]

    @property
    def any_source_ok(self) -> bool:
        """≥1 nguồn sống → controller trả 200; không có nguồn nào sống → 502 (ADR-004)."""
        return any(s.status == SourceStatus.OK for s in self.sources)

    def to_dict(self) -> dict:
        return {
            "vin": self.vin,
            "documents": [d.to_dict() for d in self.documents],
            "sources": [s.to_dict() for s in self.sources],
        }


def aggregate_documents(vin: str) -> AggregationResult:
    """Fan-out 2 nguồn đồng thời, fan-in, degradation. → trả về AggregationResult.

    ⚠️ TODO(Wiganz): đây là phần LÕI em sẽ gõ ở turn sau. Các bước (theo data flow §2.4):
      1. Tạo 2 adapter: SalesAdapter(), ServiceAdapter()
      2. Dùng concurrent.futures.ThreadPoolExecutor → submit cả 2 .fetch(vin) ĐỒNG THỜI
      3. Thu kết quả từng future (mỗi cái trả (documents, SourceResult))
      4. fan-in: gộp tất cả documents lại; gom các SourceResult vào list `sources`
      5. return AggregationResult(vin, documents, sources)
    """
    raise NotImplementedError(
        "TODO(Wiganz): viết fan-out/fan-in/degradation ở đây — xem data flow §2.4"
    )
