from django.contrib import admin

from .models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "status", "total", "payment_method", "created_at")
    list_filter = ("status", "payment_method")
    search_fields = ("id", "address")
