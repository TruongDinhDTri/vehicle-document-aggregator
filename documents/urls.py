from django.urls import path

from documents import views

urlpatterns = [
    # GET /vehicles/<vin>/documents  (đọc-to test: "lấy documents của xe theo VIN")
    path("vehicles/<str:vin>/documents", views.vehicle_documents, name="vehicle-documents"),
]
