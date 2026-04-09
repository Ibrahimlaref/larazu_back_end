import uuid

from django.db import models
from django.db.models import Avg, Count
from django.utils.text import slugify


class Product(models.Model):
    CATEGORY_CHOICES = [
        ("women", "Women"),
        ("men", "Men"),
        ("kids", "Kids"),
        ("streetwear", "Streetwear"),
        ("accessories", "Accessories"),
    ]
    BADGE_CHOICES = [
        ("new", "New"),
        ("sale", "Sale"),
        ("bestseller", "Bestseller"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, db_index=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    images = models.JSONField(default=list)  # list of URLs
    colors = models.JSONField(default=list)  # [{"name": str, "hex": str}]
    sizes = models.JSONField(default=list)  # ["S","M","L",...]
    badge = models.CharField(max_length=20, null=True, blank=True, choices=BADGE_CHOICES)
    description = models.TextField()
    details = models.TextField()
    in_stock = models.BooleanField(default=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    review_count = models.IntegerField(default=0)
    ref = models.CharField(max_length=50, null=True, blank=True)
    
    # Stock Management
    stock_quantity = models.IntegerField(default=0)
    low_stock_threshold = models.IntegerField(default=5)
    is_active = models.BooleanField(default=True)
    track_stock = models.BooleanField(default=True)

    # Scheduling
    publish_at = models.DateTimeField(null=True, blank=True)
    unpublish_at = models.DateTimeField(null=True, blank=True)

    # Organization
    tags = models.JSONField(default=list)
    sku = models.CharField(max_length=100, unique=True, null=True, blank=True)
    weight = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    meta_title = models.CharField(max_length=255, null=True, blank=True)
    meta_description = models.TextField(null=True, blank=True)

    # Variants (per size/color stock tracking)
    variants = models.JSONField(default=list)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "lazuli_products"
        indexes = [
            models.Index(fields=["category"]),
            models.Index(fields=["badge"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return self.name

    def get_total_stock(self):
        if not self.track_stock:
            return None
        if self.variants:
            return sum(v.get('stock', 0) for v in self.variants)
        return self.stock_quantity

    def is_low_stock(self):
        total = self.get_total_stock()
        if total is None:
            return False
        return total <= self.low_stock_threshold

    def is_out_of_stock(self):
        total = self.get_total_stock()
        if total is None:
            return False
        return total <= 0

    def get_stock_status(self):
        if not self.is_active:
            return "inactive"
        if self.is_out_of_stock():
            return "out_of_stock"
        if self.is_low_stock():
            return "low_stock"
        return "in_stock"

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)
            slug = base
            n = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug
        
        if self.track_stock:
            total = self.get_total_stock()
            if total is not None:
                self.in_stock = total > 0
                
        super().save(*args, **kwargs)

class ProductHistory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='history')
    action = models.CharField(max_length=50)
    # "price_changed", "stock_updated", "status_changed", "published", "unpublished", "created", "updated"
    old_value = models.JSONField(null=True)
    new_value = models.JSONField(null=True)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class Review(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    author = models.CharField(max_length=100)
    rating = models.IntegerField()  # 1-5
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "lazuli_reviews"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._recalculate_product_rating()

    def delete(self, *args, **kwargs):
        product = self.product
        super().delete(*args, **kwargs)
        Review._recalculate_for_product(product)

    def _recalculate_product_rating(self):
        Review._recalculate_for_product(self.product)

    @staticmethod
    def _recalculate_for_product(product):
        agg = Review.objects.filter(product=product).aggregate(
            avg_rating=Avg("rating"), count=Count("id")
        )
        product.rating = agg["avg_rating"] or 0
        product.review_count = agg["count"] or 0
        product.save(update_fields=["rating", "review_count"])
