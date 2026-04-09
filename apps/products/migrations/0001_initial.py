import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Product",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=255)),
                ("slug", models.SlugField(max_length=255, unique=True)),
                ("category", models.CharField(choices=[("women", "Women"), ("men", "Men"), ("kids", "Kids"), ("streetwear", "Streetwear"), ("accessories", "Accessories")], max_length=50)),
                ("price", models.DecimalField(decimal_places=2, max_digits=10)),
                ("sale_price", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("images", models.JSONField(default=list)),
                ("colors", models.JSONField(default=list)),
                ("sizes", models.JSONField(default=list)),
                ("badge", models.CharField(blank=True, choices=[("new", "New"), ("sale", "Sale"), ("bestseller", "Bestseller")], max_length=20, null=True)),
                ("description", models.TextField()),
                ("details", models.TextField()),
                ("in_stock", models.BooleanField(default=True)),
                ("rating", models.DecimalField(decimal_places=2, default=0, max_digits=3)),
                ("review_count", models.IntegerField(default=0)),
                ("ref", models.CharField(blank=True, max_length=50, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"db_table": "lazuli_products"},
        ),
        migrations.CreateModel(
            name="Review",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("author", models.CharField(max_length=100)),
                ("rating", models.IntegerField()),
                ("comment", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("product", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="reviews", to="products.product")),
            ],
            options={"db_table": "lazuli_reviews"},
        ),
        migrations.AddIndex(model_name="product", index=models.Index(fields=["category"], name="lazuli_prod_categor_idx")),
        migrations.AddIndex(model_name="product", index=models.Index(fields=["badge"], name="lazuli_prod_badge_idx")),
        migrations.AddIndex(model_name="product", index=models.Index(fields=["-created_at"], name="lazuli_prod_created_idx")),
    ]
