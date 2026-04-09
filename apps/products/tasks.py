from celery import shared_task
from django.utils import timezone
from apps.products.models import Product

@shared_task
def sync_product_scheduling():
    now = timezone.now()
    
    # Auto-publish scheduled products
    Product.objects.filter(
        publish_at__lte=now,
        publish_at__isnull=False,
        is_active=False
    ).update(is_active=True)
    
    # Auto-unpublish expired products
    Product.objects.filter(
        unpublish_at__lte=now,
        unpublish_at__isnull=False,
        is_active=True
    ).update(is_active=False)
