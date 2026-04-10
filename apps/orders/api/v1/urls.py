from django.urls import path

from apps.orders.api.v1.views import OrderCreateView, OrderDetailView

urlpatterns = [
    path("", OrderCreateView.as_view(), name="order-create"),
    path("<uuid:order_id>/", OrderDetailView.as_view(), name="order-detail"),
]
