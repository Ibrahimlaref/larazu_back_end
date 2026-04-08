from rest_framework import serializers

from apps.products.models import Product, Review


class ProductSerializer(serializers.ModelSerializer):
    stock_status = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "slug",
            "category",
            "price",
            "sale_price",
            "images",
            "colors",
            "sizes",
            "badge",
            "description",
            "details",
            "in_stock",
            "rating",
            "review_count",
            "ref",
            "stock_quantity",
            "low_stock_threshold",
            "is_active",
            "track_stock",
            "publish_at",
            "unpublish_at",
            "tags",
            "sku",
            "weight",
            "meta_title",
            "meta_description",
            "variants",
            "stock_status",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields

    def get_stock_status(self, obj):
        return obj.get_stock_status()


class ProductListSerializer(ProductSerializer):
    pass


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ("id", "product", "author", "rating", "comment", "created_at")
        read_only_fields = ("id", "product", "created_at")

    def create(self, validated_data):
        product = self.context.get("product")
        if not product:
            raise serializers.ValidationError("Product is required")
        return Review.objects.create(product=product, **validated_data)
