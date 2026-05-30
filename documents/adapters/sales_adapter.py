"""Sales System adapter (ACL). Gọi Sales API → dịch response về Document chung.

⚠️ TODO(Wiganz): phần fetch() em sẽ gõ. Hợp đồng (xem base.SourceAdapter):
  • gọi Sales API (requests.get, timeout = settings.EXTERNAL_API_TIMEOUT)
  • thành công → dịch mỗi item về Document(source="SALES"); trả (docs, SourceResult(OK))
  • lỗi/timeout → TỰ NUỐT (try/except), trả ([], SourceResult(UNAVAILABLE, error=...))
    → KHÔNG để exception nổ ra ngoài (graceful degradation — lesson L7).
"""
from __future__ import annotations

from documents.adapters.base import Document, SourceAdapter, SourceResult, SourceStatus


class SalesAdapter(SourceAdapter):
    source_name = "SALES"

    def fetch(self, vin: str) -> tuple[list[Document], SourceResult]:
        raise NotImplementedError(
            "TODO(Wiganz): gọi Sales API + try/except + dịch về Document"
        )
