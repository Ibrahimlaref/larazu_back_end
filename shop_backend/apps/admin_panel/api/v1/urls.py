from django.urls import path

from .views import (
    AdminLoginView,
    AdminOrderListView,
    AdminOrderDetailView,
    AdminOrderBulkView,
)
from .product_views import (
    AdminProductListCreateView,
    AdminProductDetailView,
    AdminProductToggleActiveView,
    AdminProductUpdateStockView,
    AdminProductScheduleView,
    AdminProductUpdatePriceView,
    AdminProductHistoryView,
    AdminProductAlertsView,
    AdminProductBulkView,
)
from .analytics_views import (
    RevenueAnalyticsView,
    OrdersSummaryView,
)

urlpatterns = [
    path("login/", AdminLoginView.as_view(), name="admin-login"),
    path("analytics/revenue/", RevenueAnalyticsView.as_view(), name="admin-analytics-revenue"),
    path("analytics/orders-summary/", OrdersSummaryView.as_view(), name="admin-analytics-orders-summary"),
    path("orders/", AdminOrderListView.as_view(), name="admin-orders-list"),
    path("orders/bulk/", AdminOrderBulkView.as_view(), name="admin-orders-bulk"),
    path("orders/<uuid:order_id>/", AdminOrderDetailView.as_view(), name="admin-order-detail"),
    path("products/", AdminProductListCreateView.as_view(), name="admin-products-list"),
    path("products/alerts/", AdminProductAlertsView.as_view(), name="admin-products-alerts"),
    path("products/bulk/", AdminProductBulkView.as_view(), name="admin-products-bulk"),
    path("products/<uuid:product_id>/", AdminProductDetailView.as_view(), name="admin-product-detail"),
    path("products/<uuid:product_id>/toggle-active/", AdminProductToggleActiveView.as_view(), name="admin-product-toggle-active"),
    path("products/<uuid:product_id>/update-stock/", AdminProductUpdateStockView.as_view(), name="admin-product-update-stock"),
    path("products/<uuid:product_id>/schedule/", AdminProductScheduleView.as_view(), name="admin-product-schedule"),
    path("products/<uuid:product_id>/update-price/", AdminProductUpdatePriceView.as_view(), name="admin-product-update-price"),
    path("products/<uuid:product_id>/history/", AdminProductHistoryView.as_view(), name="admin-product-history"),
]
