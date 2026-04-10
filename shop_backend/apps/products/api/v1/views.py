from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.permissions import AllowAny

from apps.products.models import Product, Review
from apps.products.api.v1.serializers import ProductSerializer, ReviewSerializer


def error_response(message, status_code=400):
    return Response({"error": message}, status=status_code)


class ProductViewSet(ReadOnlyModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    lookup_field = "id"
    lookup_url_kwarg = "id"

    def get_queryset(self):
        from django.utils import timezone
        from django.db.models import Q
        now = timezone.now()
        qs = Product.objects.filter(
            is_active=True
        ).filter(
            Q(publish_at__isnull=True) | Q(publish_at__lte=now)
        ).filter(
            Q(unpublish_at__isnull=True) | Q(unpublish_at__gt=now)
        )
        category = self.request.query_params.get("category")
        if category:
            qs = qs.filter(category=category)
        sort = self.request.query_params.get("sort", "newest")
        if sort == "newest":
            qs = qs.order_by("-created_at")
        elif sort == "price-asc":
            qs = qs.order_by("price")
        elif sort == "price-desc":
            qs = qs.order_by("-price")
        elif sort == "popular":
            qs = qs.order_by("-rating", "-review_count")
        min_price = self.request.query_params.get("minPrice")
        if min_price is not None and min_price != "":
            try:
                qs = qs.filter(price__gte=float(min_price))
            except ValueError:
                pass
        max_price = self.request.query_params.get("maxPrice")
        if max_price is not None and max_price != "":
            try:
                qs = qs.filter(price__lte=float(max_price))
            except ValueError:
                pass
        sizes = self.request.query_params.getlist("sizes[]") or self.request.query_params.getlist("sizes")
        if sizes:
            from django.db.models import Q
            size_q = Q()
            for s in sizes:
                size_q |= Q(sizes__contains=s)
            qs = qs.filter(size_q)
        colors = self.request.query_params.getlist("colors[]") or self.request.query_params.getlist("colors")
        if colors:
            from django.db.models import Q
            q = Q()
            for c in colors:
                q |= Q(colors__icontains=c)
            qs = qs.filter(q)
        return qs

    @action(detail=False, url_path="featured", methods=["get"])
    def featured(self, request):
        qs = Product.objects.filter(badge__in=["new", "bestseller"])
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, url_path="search", methods=["get"])
    def search(self, request):
        q = request.query_params.get("q", "").strip()
        if not q:
            return Response([])
        from django.db.models import Q
        qs = Product.objects.filter(
            Q(name__icontains=q)
            | Q(category__icontains=q)
            | Q(description__icontains=q)
        )[:50]
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, url_path="slug/(?P<slug>[^/.]+)", methods=["get"])
    def by_slug(self, request, slug=None):
        product = get_object_or_404(Product, slug=slug)
        serializer = self.get_serializer(product)
        return Response(serializer.data)

    @action(detail=True, url_path="reviews", methods=["get", "post"])
    def reviews(self, request, id=None):
        product = self.get_object()
        if request.method == "GET":
            reviews = product.reviews.all()
            serializer = ReviewSerializer(reviews, many=True)
            return Response(serializer.data)
        # POST
        ser = ReviewSerializer(data=request.data, partial=False, context={"product": product})
        ser.is_valid(raise_exception=True)
        rating = ser.validated_data.get("rating")
        if rating is None or not (1 <= int(rating) <= 5):
            return error_response("Rating must be between 1 and 5", 400)
        rev = ser.save(product=product)
        return Response(ReviewSerializer(rev).data, status=status.HTTP_201_CREATED)
