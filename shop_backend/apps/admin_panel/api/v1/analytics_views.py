"""Analytics endpoints for the LAZULI admin panel."""

from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, Sum, Q
from django.db.models.functions import TruncDay, TruncMonth
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.admin_panel.permissions import IsAdminToken
from apps.orders.models import Order


class RevenueAnalyticsView(APIView):
    """
    GET /api/admin/analytics/revenue/?period=daily|monthly

    Returns revenue data grouped by day (last 30 days) or month (last 12 months).
    Excludes cancelled orders.
    """
    permission_classes = [IsAdminToken]

    def get(self, request):
        period = request.query_params.get("period", "daily")
        now = timezone.now()

        # Build base queryset: exclude cancelled orders
        qs = Order.objects.exclude(status="cancelled")

        if period == "monthly":
            start_date = (now - timedelta(days=365)).replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )
            qs = qs.filter(created_at__gte=start_date)
            qs = (
                qs.annotate(period_label=TruncMonth("created_at"))
                .values("period_label")
                .annotate(
                    revenue=Sum("total"),
                    orders=Count("id"),
                )
                .order_by("period_label")
            )
            data = []
            for row in qs:
                rev = float(row["revenue"] or 0)
                cnt = row["orders"] or 0
                data.append({
                    "label": row["period_label"].strftime("%Y-%m"),
                    "revenue": round(rev),
                    "orders": cnt,
                    "avgOrderValue": round(rev / cnt) if cnt else 0,
                })
        else:
            # daily — last 30 days
            start_date = (now - timedelta(days=30)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            qs = qs.filter(created_at__gte=start_date)
            qs = (
                qs.annotate(period_label=TruncDay("created_at"))
                .values("period_label")
                .annotate(
                    revenue=Sum("total"),
                    orders=Count("id"),
                )
                .order_by("period_label")
            )
            data = []
            for row in qs:
                rev = float(row["revenue"] or 0)
                cnt = row["orders"] or 0
                data.append({
                    "label": row["period_label"].strftime("%Y-%m-%d"),
                    "revenue": round(rev),
                    "orders": cnt,
                    "avgOrderValue": round(rev / cnt) if cnt else 0,
                })

        # Totals
        total_revenue = sum(d["revenue"] for d in data)
        total_orders = sum(d["orders"] for d in data)

        return Response({
            "period": period,
            "data": data,
            "totals": {
                "revenue": total_revenue,
                "orders": total_orders,
                "avgOrderValue": round(total_revenue / total_orders) if total_orders else 0,
            },
        })


class OrdersSummaryView(APIView):
    """
    GET /api/admin/analytics/orders-summary/

    Returns status breakdown, today/week order counts and revenue.
    """
    permission_classes = [IsAdminToken]

    def get(self, request):
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=today_start.weekday())

        # Status breakdown — count per status
        status_counts = (
            Order.objects.values("status")
            .annotate(count=Count("id"))
        )
        breakdown = {
            "pending": 0,
            "confirmed": 0,
            "processing": 0,
            "shipped": 0,
            "delivered": 0,
            "cancelled": 0,
        }
        for row in status_counts:
            if row["status"] in breakdown:
                breakdown[row["status"]] = row["count"]

        # Today stats
        today_qs = Order.objects.filter(
            created_at__gte=today_start
        ).exclude(status="cancelled")
        today_agg = today_qs.aggregate(
            count=Count("id"),
            revenue=Sum("total"),
        )

        # Week stats
        week_qs = Order.objects.filter(
            created_at__gte=week_start
        ).exclude(status="cancelled")
        week_agg = week_qs.aggregate(
            count=Count("id"),
            revenue=Sum("total"),
        )

        return Response({
            "statusBreakdown": breakdown,
            "todayOrders": today_agg["count"] or 0,
            "todayRevenue": round(float(today_agg["revenue"] or 0)),
            "weekOrders": week_agg["count"] or 0,
            "weekRevenue": round(float(week_agg["revenue"] or 0)),
        })
