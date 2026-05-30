"""Tests for the core business logic.

Run:  python manage.py test
"""
from unittest.mock import patch

from django.test import SimpleTestCase

from documents.aggregator import (
    AggregationResult,
    Document,
    SourceResult,
    SourceStatus,
    aggregate_documents,
    fetch_sales,
)


def _fake_doc(source):
    return Document(
        id="X-1", vin="V", title="Doc", document_type="INVOICE",
        issued_date="2024-01-01", source=source, document_url=None,
    )


class _FakeResponse:
    """Minimal stand-in for a requests.Response."""

    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


class AnySourceOkTests(SimpleTestCase):
    """The 200-vs-502 decision."""

    def test_one_source_ok_means_alive(self):
        result = AggregationResult(
            vin="WDB4631234567890X",
            documents=[],
            sources=[
                SourceResult("SALES", SourceStatus.OK),
                SourceResult("SERVICE", SourceStatus.UNAVAILABLE),
            ],
        )
        self.assertTrue(result.any_source_ok)  # at least one source -> 200

    def test_all_sources_down_means_dead(self):
        result = AggregationResult(
            vin="WDB4631234567890X",
            documents=[],
            sources=[
                SourceResult("SALES", SourceStatus.UNAVAILABLE),
                SourceResult("SERVICE", SourceStatus.UNAVAILABLE),
            ],
        )
        self.assertFalse(result.any_source_ok)  # nothing responded -> 502


class AggregateDocumentsTests(SimpleTestCase):
    """Fan-out / fan-in / degradation, with the per-source fetchers mocked."""

    # @patch applies bottom-up: the first argument maps to the lowest decorator.
    @patch("documents.aggregator.fetch_service")
    @patch("documents.aggregator.fetch_sales")
    def test_merges_both_sources(self, mock_sales, mock_service):
        mock_sales.return_value = ([_fake_doc("SALES")], SourceResult("SALES", SourceStatus.OK))
        mock_service.return_value = ([_fake_doc("SERVICE")], SourceResult("SERVICE", SourceStatus.OK))

        result = aggregate_documents("V")

        self.assertEqual(len(result.documents), 2)
        self.assertTrue(result.any_source_ok)

    @patch("documents.aggregator.fetch_service")
    @patch("documents.aggregator.fetch_sales")
    def test_degradation_keeps_healthy_source(self, mock_sales, mock_service):
        mock_sales.return_value = ([_fake_doc("SALES")], SourceResult("SALES", SourceStatus.OK))
        mock_service.return_value = ([], SourceResult("SERVICE", SourceStatus.UNAVAILABLE, error="boom"))

        result = aggregate_documents("V")

        self.assertEqual(len(result.documents), 1)
        self.assertEqual(result.documents[0].source, "SALES")
        self.assertTrue(result.any_source_ok)  # still 200

    @patch("documents.aggregator.fetch_service")
    @patch("documents.aggregator.fetch_sales")
    def test_all_sources_down(self, mock_sales, mock_service):
        mock_sales.return_value = ([], SourceResult("SALES", SourceStatus.UNAVAILABLE, error="x"))
        mock_service.return_value = ([], SourceResult("SERVICE", SourceStatus.UNAVAILABLE, error="y"))

        result = aggregate_documents("V")

        self.assertEqual(result.documents, [])
        self.assertFalse(result.any_source_ok)  # 502


class FetchSalesTests(SimpleTestCase):
    """The Sales adapter: field translation and graceful failure."""

    @patch("documents.aggregator.requests.get")
    def test_translates_source_fields(self, mock_get):
        mock_get.return_value = _FakeResponse({"documents": [
            {"docId": "S-1", "docName": "Invoice", "category": "INVOICE",
             "createdDate": "2024-03-12", "fileUrl": "http://x/s-1.pdf"},
        ]})

        docs, result = fetch_sales("WDB4631234567890X")

        self.assertEqual(result.status, SourceStatus.OK)
        self.assertEqual(len(docs), 1)
        doc = docs[0]
        self.assertEqual(doc.id, "S-1")
        self.assertEqual(doc.title, "Invoice")
        self.assertEqual(doc.document_type, "INVOICE")
        self.assertEqual(doc.issued_date, "2024-03-12")
        self.assertEqual(doc.source, "SALES")
        self.assertEqual(doc.document_url, "http://x/s-1.pdf")

    @patch("documents.aggregator.requests.get", side_effect=Exception("boom"))
    def test_degrades_on_error(self, mock_get):
        docs, result = fetch_sales("WDB4631234567890X")

        self.assertEqual(docs, [])
        self.assertEqual(result.status, SourceStatus.UNAVAILABLE)
        self.assertEqual(result.source, "SALES")
