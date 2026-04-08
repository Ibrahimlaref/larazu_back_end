import os
from django.conf import settings
from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.admin_panel.permissions import IsAdminToken
from apps.orders.models import Order
from apps.products.models import Product, Review
from apps.products.api.v1.serializers import ProductSerializer, ReviewSerializer


def error_response(message, status_code=400):
    return Response({"error": message}, status=status_code)


class AdminLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = (request.data.get("email") or "").strip()
        password = request.data.get("password")
        if not email or not password:
            return error_response("email and password are required", 400)
        User = __import__("django.contrib.auth", fromlist=["get_user_model"]).get_user_model()
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return error_response("Invalid credentials", 401)
        user = authenticate(request, username=user.username, password=password)
        if user and user.is_active and (user.is_staff or user.is_superuser):
            token = getattr(settings, "LAZULI_ADMIN_TOKEN", "lazuli-admin-token-dev")
            return Response({"token": token})
        return error_response("Invalid credentials", 401)


# Admin Orders
class AdminOrderListView(APIView):
    permission_classes = [IsAdminToken]

    def get(self, request):
        from math import ceil
        from django.db.models import Q
        from apps.orders.api.v1.serializers import OrderSerializer

        qs = Order.objects.all()

        # --- Filters ---
        status_filter = request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)

        search = request.query_params.get("search", "").strip()
        if search:
            qs = qs.filter(
                Q(id__icontains=search)
                | Q(address__icontains=search)
            )

        date_from = request.query_params.get("dateFrom")
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)

        date_to = request.query_params.get("dateTo")
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)

        payment_method = request.query_params.get("paymentMethod")
        if payment_method:
            qs = qs.filter(payment_method=payment_method)

        wilaya = request.query_params.get("wilaya")
        if wilaya:
            qs = qs.filter(address__wilaya__icontains=wilaya)

        # --- Sorting ---
        sort = request.query_params.get("sort", "newest")
        sort_map = {
            "newest": "-created_at",
            "oldest": "created_at",
            "total-asc": "total",
            "total-desc": "-total",
        }
        qs = qs.order_by(sort_map.get(sort, "-created_at"))

        # --- Pagination ---
        total_count = qs.count()
        try:
            page = max(1, int(request.query_params.get("page", 1)))
        except (ValueError, TypeError):
            page = 1
        try:
            page_size = min(100, max(1, int(request.query_params.get("pageSize", 20))))
        except (ValueError, TypeError):
            page_size = 20

        total_pages = ceil(total_count / page_size) if page_size else 1
        offset = (page - 1) * page_size
        orders = qs[offset:offset + page_size]

        data = [OrderSerializer(o).data for o in orders]
        return Response({
            "results": data,
            "count": total_count,
            "page": page,
            "pageSize": page_size,
            "totalPages": total_pages,
        })


class AdminOrderDetailView(APIView):
    permission_classes = [IsAdminToken]

    def patch(self, request, order_id):
        order = Order.objects.filter(id=order_id).first()
        if not order:
            return error_response("Order not found", 404)
        new_status = request.data.get("status")
        if not new_status:
            return error_response("status is required", 400)
        valid = [c[0] for c in Order.STATUS_CHOICES]
        if new_status not in valid:
            return error_response(f"Invalid status. Must be one of: {valid}", 400)
        order.status = new_status
        order.save()
        from apps.orders.api.v1.serializers import OrderSerializer
        return Response(OrderSerializer(order).data)


class AdminOrderBulkView(APIView):
    permission_classes = [IsAdminToken]

    def patch(self, request):
        ids = request.data.get("ids", [])
        new_status = request.data.get("status")
        if not ids or not new_status:
            return error_response("ids and status are required", 400)
        valid = [c[0] for c in Order.STATUS_CHOICES]
        if new_status not in valid:
            return error_response(f"Invalid status. Must be one of: {valid}", 400)
        count = Order.objects.filter(id__in=ids).update(status=new_status)
        return Response({"count": count})


# Admin Products
class AdminProductListView(APIView):
    permission_classes = [IsAdminToken]

    def get(self, request):
        qs = Product.objects.all().order_by("-created_at")
        data = [ProductSerializer(p).data for p in qs]
        return Response(data)
