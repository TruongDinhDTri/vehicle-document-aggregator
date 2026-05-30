"""Service System adapter (ACL). Gọi Service API → dịch response về Document chung.

⚠️ TODO(Wiganz): song song với SalesAdapter — chỉ khác nguồn + cách dịch field
(Service trả title/serviceDate... thay vì docName/price...). Vẫn tự nuốt lỗi (degradation).
"""
from __future__ import annotations

from documents.adapters.base import Document, SourceAdapter, SourceResult, SourceStatus


class ServiceAdapter(SourceAdapter):
    source_name = "SERVICE"

    def fetch(self, vin: str) -> tuple[list[Document], SourceResult]:
        raise NotImplementedError(
            "TODO(Wiganz): gọi Service API + try/except + dịch về Document"
        )
