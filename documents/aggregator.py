"""Aggregation logic for the Unified Document Viewer.

Fans out to the Sales and Service systems concurrently, normalizes each system's
response into a shared `Document` model (Anti-Corruption Layer), and merges the
results. A failing source degrades gracefully: its documents are dropped and its
status is reported in `sources` instead of failing the whole request.

The HTTP layer (views) stays thin; all business logic lives here.
"""
from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from typing import Optional

import requests
from django.conf import settings

logger = logging.getLogger("documents")


class SourceStatus:
    OK = "ok"
    UNAVAILABLE = "unavailable"


@dataclass
class Document:
    """A document normalized to a shared shape across all source systems.

    `source` identifies the originating system so the unified list stays traceable.
    """

    id: str
    vin: str
    title: str
    document_type: str
    issued_date: str
    source: str  # "SALES" | "SERVICE"
    document_url: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SourceResult:
    """Health of a single source, surfaced in the response separately from the data."""

    source: str
    status: str
    error: Optional[str] = None

    def to_dict(self) -> dict:
        data = {"source": self.source, "status": self.status}
        if self.error:
            data["error"] = self.error
        return data


@dataclass
class AggregationResult:
    """Merged output: `documents` (data) kept separate from `sources` (per-source status)."""

    vin: str
    documents: list[Document]
    sources: list[SourceResult]

    @property
    def any_source_ok(self) -> bool:
        """True if at least one source responded; drives the 200-vs-502 decision."""
        return any(s.status == SourceStatus.OK for s in self.sources)

    def to_dict(self) -> dict:
        return {
            "vin": self.vin,
            "documents": [d.to_dict() for d in self.documents],
            "sources": [s.to_dict() for s in self.sources],
        }


def fetch_sales(vin: str) -> tuple[list[Document], SourceResult]:
    """Call the Sales API and translate its payload into `Document`s.

    Any failure (timeout, connection error, bad payload) is swallowed and reported
    as an unavailable source so it cannot bring down the whole request.
    """
    base_url = settings.DOCUMENT_SOURCES["SALES"]["base_url"]
    try:
        resp = requests.get(
            f"{base_url}/documents",
            params={"vin": vin},
            timeout=settings.EXTERNAL_API_TIMEOUT,
        )
        resp.raise_for_status()
        raw = resp.json().get("documents", [])

        documents = [
            Document(
                id=item.get("docId"),
                vin=vin,
                title=item.get("docName"),
                document_type=item.get("category"),
                issued_date=item.get("createdDate"),
                source="SALES",
                document_url=item.get("fileUrl"),
            )
            for item in raw
        ]
        return documents, SourceResult(source="SALES", status=SourceStatus.OK)

    except Exception as exc:
        logger.error("sales fetch failed vin=%s err=%s", vin, exc)
        return [], SourceResult(source="SALES", status=SourceStatus.UNAVAILABLE, error=str(exc))


def fetch_service(vin: str) -> tuple[list[Document], SourceResult]:
    """Call the Service API and translate its payload into `Document`s.

    Mirrors `fetch_sales` but maps the Service system's distinct field names.
    Failures degrade gracefully (see `fetch_sales`).
    """
    base_url = settings.DOCUMENT_SOURCES["SERVICE"]["base_url"]
    try:
        resp = requests.get(
            f"{base_url}/documents",
            params={"vin": vin},
            timeout=settings.EXTERNAL_API_TIMEOUT,
        )
        resp.raise_for_status()
        raw = resp.json().get("documents", [])

        documents = [
            Document(
                id=item.get("recordId"),
                vin=vin,
                title=item.get("name"),
                document_type=item.get("type"),
                issued_date=item.get("serviceDate"),
                source="SERVICE",
                document_url=item.get("link"),
            )
            for item in raw
        ]
        return documents, SourceResult(source="SERVICE", status=SourceStatus.OK)

    except Exception as exc:
        logger.error("service fetch failed vin=%s err=%s", vin, exc)
        return [], SourceResult(source="SERVICE", status=SourceStatus.UNAVAILABLE, error=str(exc))


def aggregate_documents(vin: str) -> AggregationResult:
    """Fan out to both sources concurrently, then merge into a single result.

    Latency is bounded by the slowest source rather than the sum of both.
    """
    with ThreadPoolExecutor(max_workers=2) as executor:
        future_sales = executor.submit(fetch_sales, vin)
        future_service = executor.submit(fetch_service, vin)

        sales_docs, sales_status = future_sales.result()
        service_docs, service_status = future_service.result()

    return AggregationResult(
        vin=vin,
        documents=sales_docs + service_docs,
        sources=[sales_status, service_status],
    )
