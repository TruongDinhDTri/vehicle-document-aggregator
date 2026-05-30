from django.db import models


class SearchAuditLog(models.Model):
    """Cuốn sổ "ai tra xe nào, lúc nào, nguồn nào sống/chết" (ADR-005, Phase 4 §4.3).

    DB của app chỉ phục vụ observability của RIÊNG mình — documents thuộc 2 nguồn ngoài,
    KHÔNG lưu ở đây. Schema sạch 1NF: mỗi nguồn một cột atomic (ADR-007).
    """

    STATUS_CHOICES = [
        ("ok", "ok"),
        ("unavailable", "unavailable"),
    ]

    vin = models.CharField(max_length=17, db_index=True)       # VIN chuẩn = 17 ký tự
    created_at = models.DateTimeField(auto_now_add=True)        # "giờ giấc tra"
    sales_status = models.CharField(max_length=12, choices=STATUS_CHOICES)
    service_status = models.CharField(max_length=12, choices=STATUS_CHOICES)
    document_count = models.IntegerField(default=0)            # lần đó trả về mấy tờ

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.vin} @ {self.created_at:%Y-%m-%d %H:%M} ({self.document_count} docs)"
