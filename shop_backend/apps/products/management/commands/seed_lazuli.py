"""
Seed LAZULI e-commerce data:
- Admin user: admin@lazuli.dz / admin123
- 20+ products across all 5 categories with varied badges
- 3+ reviews per product
- 5+ sample orders in different statuses
"""
import uuid
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class Command(BaseCommand):
    help = "Seed LAZULI e-commerce demo data"

    def handle(self, *args, **options):
        self.stdout.write("Seeding LAZULI data...")

        # Admin user
        admin, created = User.objects.get_or_create(
            email="admin@lazuli.dz",
            defaults={
                "username": "admin@lazuli.dz",
                "first_name": "Admin",
                "last_name": "Lazuli",
                "is_staff": True,
                "is_superuser": True,
                "is_active": True,
            },
        )
        if created:
            admin.set_password("admin123")
            admin.save()
            self.stdout.write("  Created admin user: admin@lazuli.dz / admin123")
        else:
            admin.set_password("admin123")
            admin.save()
            self.stdout.write("  Updated admin password: admin123")

        # Products
        from apps.products.models import Product, Review
        from apps.orders.models import Order
        from apps.orders.services import get_shipping_cost, calculate_tax, get_estimated_delivery

        products_data = [
            # women
            {"name": "Classic Blazer", "category": "women", "price": 8500, "badge": "new"},
            {"name": "Floral Dress", "category": "women", "price": 6200, "sale_price": 4999, "badge": "sale"},
            {"name": "Wool Coat", "category": "women", "price": 12500},
            {"name": "Silk Blouse", "category": "women", "price": 4500, "badge": "bestseller"},
            {"name": "Tailored Trousers", "category": "women", "price": 3800},
            # men
            {"name": "Cotton T-Shirt", "category": "men", "price": 1800, "badge": "bestseller"},
            {"name": "Chino Pants", "category": "men", "price": 4200},
            {"name": "Leather Jacket", "category": "men", "price": 15000, "badge": "new"},
            {"name": "Oxford Shirt", "category": "men", "price": 3500},
            {"name": "Denim Jeans", "category": "men", "price": 5500, "sale_price": 4499, "badge": "sale"},
            # kids
            {"name": "Kids Hoodie", "category": "kids", "price": 2200, "badge": "new"},
            {"name": "Children Sneakers", "category": "kids", "price": 3800},
            {"name": "School Backpack", "category": "kids", "price": 2500, "badge": "bestseller"},
            {"name": "Rain Jacket Kids", "category": "kids", "price": 4200},
            {"name": "Cotton Pajamas", "category": "kids", "price": 1500},
            # streetwear
            {"name": "Oversized Hoodie", "category": "streetwear", "price": 5500, "badge": "bestseller"},
            {"name": "Cargo Pants", "category": "streetwear", "price": 4800},
            {"name": "Graphic Tee", "category": "streetwear", "price": 2200, "badge": "new"},
            {"name": "Platform Sneakers", "category": "streetwear", "price": 7200},
            {"name": "Bucket Hat", "category": "streetwear", "price": 1200},
            # accessories
            {"name": "Leather Belt", "category": "accessories", "price": 1800},
            {"name": "Sunglasses", "category": "accessories", "price": 3500, "badge": "sale"},
            {"name": "Silk Scarf", "category": "accessories", "price": 2200},
            {"name": "Crossbody Bag", "category": "accessories", "price": 5800, "badge": "new"},
        ]

        created_products = []
        for i, pd in enumerate(products_data):
            slug = f"{pd['name'].lower().replace(' ', '-')}-{i}"
            p, _ = Product.objects.get_or_create(
                slug=slug,
                defaults={
                    "name": pd["name"],
                    "category": pd["category"],
                    "price": Decimal(str(pd["price"])),
                    "sale_price": Decimal(str(pd["sale_price"])) if pd.get("sale_price") else None,
                    "badge": pd.get("badge"),
                    "images": [f"/media/products/{slug}.jpg"],
                    "colors": [{"name": "Black", "hex": "#000000"}, {"name": "White", "hex": "#FFFFFF"}, {"name": "Navy", "hex": "#000080"}],
                    "sizes": ["S", "M", "L", "XL"],
                    "description": f"High quality {pd['name']}. Perfect for everyday wear.",
                    "details": "100% quality materials. Machine washable. Made with care.",
                    "in_stock": True,
                    "ref": f"LAZ-{1000 + i}",
                },
            )
            created_products.append(p)

        self.stdout.write(f"  Created/verified {len(created_products)} products")

        # Reviews
        authors = ["Sarah", "Ahmed", "Lina", "Karim", "Nadia", "Omar", "Yasmine", "Mehdi"]
        for p in created_products:
            existing = Review.objects.filter(product=p).count()
            if existing >= 3:
                continue
            for j in range(3 - existing):
                Review.objects.create(
                    product=p,
                    author=authors[(hash(str(p.id)) + j) % len(authors)],
                    rating=3 + (j % 3),
                    comment=f"Great product! Very satisfied with my purchase.",
                )
        self.stdout.write("  Added reviews to products")

        # Sample orders
        sample_address = {
            "firstName": "Mohamed",
            "lastName": "Benali",
            "email": "mohamed@example.com",
            "phone": "+213555123456",
            "wilaya": "16",
            "city": "Algiers",
            "postalCode": "16000",
            "address": "123 Main Street",
            "notes": "Please ring the bell",
        }
        statuses = ["pending", "confirmed", "processing", "shipped", "delivered", "cancelled"]
        now = timezone.now()
        for i in range(6):
            items = [
                {
                    "productId": str(created_products[i % len(created_products)].id),
                    "name": created_products[i % len(created_products)].name,
                    "price": float(created_products[i % len(created_products)].price),
                    "image": "/media/sample.jpg",
                    "color": "Black",
                    "size": "M",
                    "quantity": 1 + (i % 2),
                }
            ]
            subtotal = sum(it["price"] * it["quantity"] for it in items)
            shipping = 0 if i % 3 == 0 else (500 if i % 3 == 1 else 1000)
            tax = int(subtotal * 0.05)
            total = subtotal + shipping + tax
            ed = now + timedelta(days=5 - i) if i < 5 else now + timedelta(days=1)
            Order.objects.create(
                items=items,
                subtotal=Decimal(subtotal),
                shipping=Decimal(shipping),
                tax=Decimal(tax),
                total=Decimal(total),
                status=statuses[i],
                address=sample_address,
                payment_method=["ccp", "baridimob", "cash"][i % 3],
                shipping_method=["standard", "express", "sameday"][i % 3],
                estimated_delivery=ed,
            )
        self.stdout.write("  Created 6 sample orders")

        self.stdout.write(self.style.SUCCESS("LAZULI seed completed."))
