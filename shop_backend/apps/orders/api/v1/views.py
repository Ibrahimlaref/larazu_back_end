from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.orders.models import Order
from apps.orders.api.v1.serializers import OrderCreateSerializer, OrderSerializer
from apps.orders.services import (
    get_shipping_cost,
    calculate_tax,
    get_estimated_delivery,
)


def error_response(message, status_code=400):
    return Response({"error": message}, status=status_code)


class OrderCreateView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        ser = OrderCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        items = data["items"]
        address = data["address"]
        payment_method = data["paymentMethod"]
        shipping_method = data["shippingMethod"]

        subtotal = sum(
            float(item["price"]) * int(item["quantity"])
            for item in items
        )
        shipping = get_shipping_cost(shipping_method)
        tax = calculate_tax(subtotal)
        total = subtotal + shipping + tax
        estimated_delivery = get_estimated_delivery(shipping_method)

        order = Order.objects.create(
            items=items,
            subtotal=subtotal,
            shipping=shipping,
            tax=tax,
            total=total,
            address=address,
            payment_method=payment_method,
            shipping_method=shipping_method,
            estimated_delivery=estimated_delivery,
        )
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class OrderDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)
        return Response(OrderSerializer(order).data)
