import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Order",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("items", models.JSONField()),
                ("subtotal", models.DecimalField(decimal_places=2, max_digits=10)),
                ("shipping", models.DecimalField(decimal_places=2, max_digits=10)),
                ("tax", models.DecimalField(decimal_places=2, max_digits=10)),
                ("total", models.DecimalField(decimal_places=2, max_digits=10)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("confirmed", "Confirmed"), ("processing", "Processing"), ("shipped", "Shipped"), ("delivered", "Delivered"), ("cancelled", "Cancelled")], default="pending", max_length=20)),
                ("address", models.JSONField()),
                ("payment_method", models.CharField(choices=[("ccp", "CCP"), ("baridimob", "Baridi Mob"), ("cash", "Cash")], max_length=20)),
                ("shipping_method", models.CharField(choices=[("standard", "Standard"), ("express", "Express"), ("sameday", "Same Day")], max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("estimated_delivery", models.DateTimeField()),
            ],
            options={"db_table": "lazuli_orders"},
        ),
        migrations.AddIndex(model_name="order", index=models.Index(fields=["status"], name="lazuli_orde_status_idx")),
        migrations.AddIndex(model_name="order", index=models.Index(fields=["-created_at"], name="lazuli_orde_created_idx")),
    ]
