from django.db import models


class SearchAuditLog(models.Model):
    """Audit trail of VIN lookups (who/when is added once auth exists).

    The app does not own the documents themselves (they live in the external Sales
    and Service systems), so the database records only what is ours: each search and
    the per-source outcome. Useful for observability and usage analytics.
    """

    OK = "ok"
    UNAVAILABLE = "unavailable"
    STATUS_CHOICES = [(OK, OK), (UNAVAILABLE, UNAVAILABLE)]

    vin = models.CharField(max_length=17, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sales_status = models.CharField(max_length=12, choices=STATUS_CHOICES)
    service_status = models.CharField(max_length=12, choices=STATUS_CHOICES)
    document_count = models.IntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.vin} @ {self.created_at:%Y-%m-%d %H:%M} ({self.document_count} docs)"
