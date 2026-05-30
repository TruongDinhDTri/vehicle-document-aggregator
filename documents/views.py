"""Controller (thin view) — Separation of Concerns: CHỈ lo HTTP.

Validate VIN → gọi Aggregator (business logic ở services/) → map HTTP status (ADR-004).
KHÔNG fan-out, KHÔNG gộp ở đây — đó là việc của Aggregator.
"""
import logging

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from documents.services.aggregator import aggregate_documents

logger = logging.getLogger("documents")

VIN_LENGTH = 17


@api_view(["GET"])
def vehicle_documents(request, vin):
    """GET /vehicles/<vin>/documents — danh sách document đã gộp của 1 xe."""
    # 1. Validate VIN — sai định dạng → 400 (controller lo, không fan-out)
    if not vin or len(vin) != VIN_LENGTH:
        return Response(
            {"error": f"VIN phải đúng {VIN_LENGTH} ký tự."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    logger.info("documents.search vin=%s", vin)

    # 2. Gọi Aggregator (the brain) — fan-out/fan-in/degradation
    result = aggregate_documents(vin)

    # 3. Map HTTP status (ADR-004): ≥1 nguồn sống → 200; cả 2 chết → 502
    http_status = (
        status.HTTP_200_OK if result.any_source_ok
        else status.HTTP_502_BAD_GATEWAY
    )

    # TODO(slice sau): ghi SearchAuditLog (non-blocking) trước khi return
    return Response(result.to_dict(), status=http_status)
