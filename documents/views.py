"""HTTP layer for the Unified Document Viewer.

Thin controller: validate the VIN, delegate to the aggregator, map the result to an
HTTP status, and record an audit log entry. No business logic lives here.
"""
import logging

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from documents.aggregator import aggregate_documents
from documents.models import SearchAuditLog

logger = logging.getLogger("documents")

VIN_LENGTH = 17


@api_view(["GET"])
def vehicle_documents(request, vin):
    """GET /vehicles/<vin>/documents — unified list of a vehicle's documents."""
    if not vin or len(vin) != VIN_LENGTH:
        return Response(
            {"error": f"VIN must be exactly {VIN_LENGTH} characters."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    logger.info("documents.search vin=%s", vin)

    result = aggregate_documents(vin)

    # 200 if at least one source responded; 502 only when every upstream failed.
    http_status = (
        status.HTTP_200_OK if result.any_source_ok
        else status.HTTP_502_BAD_GATEWAY
    )

    # Audit log is best-effort: a logging failure must never break the response.
    try:
        by_source = {s.source: s.status for s in result.sources}
        SearchAuditLog.objects.create(
            vin=vin,
            sales_status=by_source.get("SALES", SearchAuditLog.UNAVAILABLE),
            service_status=by_source.get("SERVICE", SearchAuditLog.UNAVAILABLE),
            document_count=len(result.documents),
        )
    except Exception as exc:
        logger.error("audit log write failed vin=%s err=%s", vin, exc)

    return Response(result.to_dict(), status=http_status)
