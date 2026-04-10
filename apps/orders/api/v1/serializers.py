from rest_framework import serializers

from apps.orders.models import Order


class OrderCreateSerializer(serializers.Serializer):
    items = serializers.ListField(
        child=serializers.DictField(),
        min_length=1,
        help_text="List of {productId, name, price, image, color, size, quantity}",
    )
    address = serializers.DictField(
        help_text="{firstName, lastName, email, phone, wilaya, city, postalCode, address, notes}"
    )
    paymentMethod = serializers.ChoiceField(choices=["ccp", "baridimob", "cash"])
    shippingMethod = serializers.ChoiceField(choices=["standard", "express", "sameday"])

    def validate_address(self, value):
        required = ["firstName", "lastName", "email", "phone", "wilaya", "city", "address"]
        for k in required:
            if not value.get(k):
                raise serializers.ValidationError(f"address.{k} is required")
        from apps.orders.services import is_valid_wilaya
        if not is_valid_wilaya(value.get("wilaya")):
            raise serializers.ValidationError("Invalid wilaya")
        return value

    def validate_items(self, value):
        for i, item in enumerate(value):
            for k in ["productId", "name", "price", "quantity"]:
                if k not in item:
                    raise serializers.ValidationError(f"items[{i}].{k} is required")
            try:
                qty = int(item["quantity"])
                if qty < 1:
                    raise serializers.ValidationError(f"items[{i}].quantity must be >= 1")
            except (TypeError, ValueError):
                raise serializers.ValidationError(f"items[{i}].quantity must be an integer")
        return value


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = (
            "id",
            "items",
            "subtotal",
            "shipping",
            "tax",
            "total",
            "status",
            "address",
            "payment_method",
            "shipping_method",
            "created_at",
            "estimated_delivery",
        )
        read_only_fields = fields
