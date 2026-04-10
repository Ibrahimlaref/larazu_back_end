import uuid

from django.db import models


class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("processing", "Processing"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    ]
    PAYMENT_CHOICES = [
        ("ccp", "CCP"),
        ("baridimob", "Baridi Mob"),
        ("cash", "Cash"),
    ]
    SHIPPING_CHOICES = [
        ("standard", "Standard"),
        ("express", "Express"),
        ("sameday", "Same Day"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    items = models.JSONField()
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    shipping = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    address = models.JSONField()
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES)
    shipping_method = models.CharField(max_length=20, choices=SHIPPING_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    estimated_delivery = models.DateTimeField()

    class Meta:
        db_table = "lazuli_orders"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["-created_at"]),
        ]
