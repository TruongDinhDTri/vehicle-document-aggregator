from django.urls import path

from documents import views

urlpatterns = [
    path("vehicles/<str:vin>/documents", views.vehicle_documents, name="vehicle-documents"),
]
