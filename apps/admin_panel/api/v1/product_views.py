"""Admin product views with file upload, base64, and URL image support."""

import base64
import os
import uuid
import json
from datetime import datetime

from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from django.db.models import Q, F
from rest_framework import status
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone

from apps.admin_panel.permissions import IsAdminToken
from apps.products.models import Product, Review, ProductHistory
from apps.products.api.v1.serializers import ProductSerializer

try:
    from PIL import Image
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False


def error_response(message, status_code=400):
    return Response({"error": message}, status=status_code)


def _slug_from_name(name):
    base = slugify(name) or "product"
    slug = base
    n = 1
    while Product.objects.filter(slug=slug).exists():
        slug = f"{base}-{n}"
        n += 1
    return slug


def _ensure_products_dir():
    media_root = getattr(settings, "MEDIA_ROOT", None) or os.path.join(settings.BASE_DIR, "media")
    products_dir = os.path.join(str(media_root), "products")
    os.makedirs(products_dir, exist_ok=True)
    return products_dir


def _resize_image(file_path, max_width=1200):
    if not HAS_PILLOW:
        return
    try:
        img = Image.open(file_path)
        if img.width > max_width:
            ratio = max_width / img.width
            new_height = int(img.height * ratio)
            img = img.resize((max_width, new_height), Image.LANCZOS)
            img.save(file_path, quality=85, optimize=True)
    except Exception:
        pass


def _save_uploaded_file(uploaded_file):
    products_dir = _ensure_products_dir()
    ext = os.path.splitext(uploaded_file.name)[1].lower() or ".jpg"
    if ext not in (".jpg", ".jpeg", ".png", ".webp"):
        ext = ".jpg"
    fname = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(products_dir, fname)
    with open(file_path, "wb") as f:
        for chunk in uploaded_file.chunks():
            f.write(chunk)
    _resize_image(file_path)
    return f"/media/products/{fname}"


def _save_base64_image(data_str):
    products_dir = _ensure_products_dir()
    try:
        if data_str.startswith("data:"):
            header, b64_data = data_str.split(",", 1)
            mime = header.split(":")[1].split(";")[0]
            ext_map = {
                "image/jpeg": ".jpg",
                "image/png": ".png",
                "image/webp": ".webp",
                "image/jpg": ".jpg",
            }
            ext = ext_map.get(mime, ".jpg")
        else:
            b64_data = data_str
            ext = ".jpg"

        raw = base64.b64decode(b64_data)
        fname = f"{uuid.uuid4().hex}{ext}"
        file_path = os.path.join(products_dir, fname)
        with open(file_path, "wb") as f:
            f.write(raw)
        _resize_image(file_path)
        return f"/media/products/{fname}"
    except Exception:
        return None


def _process_images(images_data, files=None):
    urls = []
    if files:
        for f in files:
            url = _save_uploaded_file(f)
            urls.append(url)

    for img in (images_data or []):
        if isinstance(img, str):
            if img.startswith("data:"):
                url = _save_base64_image(img)
                if url:
                    urls.append(url)
            elif img.startswith(("http://", "https://", "/")):
                urls.append(img)
        elif isinstance(img, dict) and img.get("base64"):
            try:
                products_dir = _ensure_products_dir()
                raw = base64.b64decode(img["base64"])
                ext = img.get("ext", "png")
                fname = f"{uuid.uuid4().hex}.{ext}"
                file_path = os.path.join(products_dir, fname)
                with open(file_path, "wb") as f:
                    f.write(raw)
                _resize_image(file_path)
                urls.append(f"/media/products/{fname}")
            except Exception:
                pass
    return urls


def _extract_product_data(request):
    data = request.data
    result = {}
    
    # String and Text fields
    str_fields = ["name", "category", "badge", "description", "details", "ref", "sku", "meta_title", "meta_description"]
    for field in str_fields:
        if field in data:
            val = data[field]
            result[field] = val if val != "" else None

    # Floats / Decimals
    for field in ["price", "sale_price", "weight"]:
        if field in data:
            val = data[field]
            if val is None or val == "" or val == "null":
                result[field] = None
            else:
                try:
                    result[field] = float(val)
                except (ValueError, TypeError):
                    pass

    # Booleans
    for field in ["in_stock", "is_active", "track_stock"]:
        if field in data:
            val = data[field]
            if isinstance(val, bool):
                result[field] = val
            elif isinstance(val, str):
                result[field] = val.lower() in ("true", "1", "yes")
            elif val is None:
                pass
            else:
                result[field] = bool(val)

    # Integers
    for field in ["stock_quantity", "low_stock_threshold"]:
        if field in data:
            val = data[field]
            if val is not None and val != "":
                try:
                    result[field] = int(val)
                except (ValueError, TypeError):
                    pass

    # Datetimes
    for field in ["publish_at", "unpublish_at"]:
        if field in data:
            val = data[field]
            if val is None or val == "" or val == "null":
                result[field] = None
            else:
                result[field] = val

    # JSON Lists
    for json_field in ["sizes", "colors", "tags", "variants"]:
        if json_field in data:
            val = data[json_field]
            if isinstance(val, str):
                try:
                    result[json_field] = json.loads(val)
                except (json.JSONDecodeError, ValueError):
                    if json_field in ("sizes", "tags"):
                        result[json_field] = [s.strip() for s in val.split(",") if s.strip()]
            elif isinstance(val, list):
                result[json_field] = val

    return result


class AdminProductListCreateView(APIView):
    permission_classes = [IsAdminToken]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get(self, request):
        qs = Product.objects.all()

        # Summary computation before pagination
        total = qs.count()
        active = qs.filter(is_active=True).count()
        inactive = qs.filter(is_active=False).count()
        out_of_stock = qs.filter(in_stock=False).count()
        
        # For low stock: track_stock=True and stock_quantity <= low_stock_threshold (approximate ignoring variants in query)
        low_stock = qs.filter(track_stock=True, stock_quantity__lte=F('low_stock_threshold'), stock_quantity__gt=0).count()
        scheduled = qs.filter(publish_at__gt=timezone.now()).count()

        summary = {
            "total": total,
            "active": active,
            "inactive": inactive,
            "out_of_stock": out_of_stock,
            "low_stock": low_stock,
            "scheduled": scheduled
        }

        # Filtering
        status_param = request.query_params.get("status")
        if status_param == "active":
            qs = qs.filter(is_active=True)
        elif status_param == "inactive":
            qs = qs.filter(is_active=False)
        elif status_param == "out_of_stock":
            qs = qs.filter(in_stock=False)
        elif status_param == "low_stock":
             # Best effort db filter
             qs = qs.filter(track_stock=True, stock_quantity__lte=F('low_stock_threshold'), stock_quantity__gt=0)
        elif status_param == "scheduled":
             qs = qs.filter(publish_at__gt=timezone.now())

        category = request.query_params.get("category")
        if category:
            qs = qs.filter(category=category)
            
        badge = request.query_params.get("badge")
        if badge:
            qs = qs.filter(badge=badge)

        search = request.query_params.get("search")
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(sku__icontains=search) | Q(ref__icontains=search))

        tags_param = request.query_params.get("tags")
        if tags_param:
            tags_list = [t.strip() for t in tags_param.split(",")]
            for t in tags_list:
                qs = qs.filter(tags__contains=t)

        sort = request.query_params.get("sort", "newest")
        if sort == "newest":
            qs = qs.order_by("-updated_at", "-created_at")
        elif sort == "oldest":
            qs = qs.order_by("created_at")
        elif sort == "price-asc":
            qs = qs.order_by("price")
        elif sort == "price-desc":
            qs = qs.order_by("-price")
        elif sort == "stock-asc":
            qs = qs.order_by("stock_quantity")
        elif sort == "stock-desc":
            qs = qs.order_by("-stock_quantity")
        elif sort == "name-asc":
            qs = qs.order_by("name")

        # Pagination
        try:
            page = int(request.query_params.get("page", 1))
            page_size = int(request.query_params.get("pageSize", 20))
        except ValueError:
            page = 1
            page_size = 20

        count = qs.count()
        total_pages = (count + page_size - 1) // page_size
        offset = (page - 1) * page_size
        results = qs[offset:offset + page_size]

        return Response({
            "results": ProductSerializer(results, many=True).data,
            "count": count,
            "page": page,
            "pageSize": page_size,
            "totalPages": total_pages,
            "summary": summary
        })

    def post(self, request):
        product_data = _extract_product_data(request)
        name = product_data.get("name")
        if not name:
            return error_response("name is required", 400)

        slug = request.data.get("slug") or _slug_from_name(name)
        if Product.objects.filter(slug=slug).exists():
            slug = _slug_from_name(name)

        images_json = request.data.get("images", [])
        if isinstance(images_json, str):
            try:
                images_json = json.loads(images_json)
            except (json.JSONDecodeError, ValueError):
                images_json = []

        uploaded_files = request.FILES.getlist("images")
        images = _process_images(images_json, files=uploaded_files)

        product = Product.objects.create(
            name=name,
            slug=slug,
            category=product_data.get("category", "women"),
            price=product_data.get("price", 0),
            sale_price=product_data.get("sale_price"),
            images=images,
            colors=product_data.get("colors", []),
            sizes=product_data.get("sizes", []),
            badge=product_data.get("badge"),
            description=product_data.get("description", ""),
            details=product_data.get("details", ""),
            in_stock=product_data.get("in_stock", True),
            ref=product_data.get("ref"),
            stock_quantity=product_data.get("stock_quantity", 0),
            low_stock_threshold=product_data.get("low_stock_threshold", 5),
            is_active=product_data.get("is_active", True),
            track_stock=product_data.get("track_stock", True),
            publish_at=product_data.get("publish_at"),
            unpublish_at=product_data.get("unpublish_at"),
            tags=product_data.get("tags", []),
            sku=product_data.get("sku"),
            weight=product_data.get("weight"),
            meta_title=product_data.get("meta_title"),
            meta_description=product_data.get("meta_description"),
            variants=product_data.get("variants", [])
        )
        
        ProductHistory.objects.create(
            product=product,
            action="created",
            note="Product created via Admin"
        )
        return Response(ProductSerializer(product).data, status=status.HTTP_201_CREATED)


class AdminProductDetailView(APIView):
    permission_classes = [IsAdminToken]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def put(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        product_data = _extract_product_data(request)
        
        old_price = product.price

        valid_fields = [
            "name", "category", "price", "sale_price", "badge",
            "description", "details", "in_stock", "ref",
            "stock_quantity", "low_stock_threshold", "is_active",
            "track_stock", "publish_at", "unpublish_at",
            "sku", "weight", "meta_title", "meta_description"
        ]
        
        for field in valid_fields:
            if field in product_data:
                setattr(product, field, product_data[field])

        for json_field in ["sizes", "colors", "tags", "variants"]:
            if json_field in product_data:
                setattr(product, json_field, product_data[json_field])

        images_json = request.data.get("images", None)
        uploaded_files = request.FILES.getlist("images")
        if images_json is not None or uploaded_files:
            if isinstance(images_json, str):
                try:
                    images_json = json.loads(images_json)
                except (json.JSONDecodeError, ValueError):
                    images_json = []
            images = _process_images(images_json, files=uploaded_files)
            if images:
                product.images = images

        if "name" in product_data and "slug" not in request.data:
            product.slug = _slug_from_name(product.name)

        product.save()

        ProductHistory.objects.create(
            product=product,
            action="updated",
            note="Product updated completely"
        )
        
        if "price" in product_data and product_data["price"] != old_price:
            ProductHistory.objects.create(
                product=product,
                action="price_changed",
                old_value={"price": str(old_price)},
                new_value={"price": str(product.price)}
            )

        return Response(ProductSerializer(product).data)

    def delete(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminProductToggleActiveView(APIView):
    permission_classes = [IsAdminToken]
    def patch(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        product.is_active = not product.is_active
        product.save()
        ProductHistory.objects.create(
            product=product,
            action="status_changed",
            new_value={"is_active": product.is_active},
            note="Deactivated" if not product.is_active else "Activated"
        )
        return Response({
            "is_active": product.is_active,
            "message": f"Product {'activated' if product.is_active else 'deactivated'}"
        })

class AdminProductUpdateStockView(APIView):
    permission_classes = [IsAdminToken]
    def patch(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        
        old_stock = product.get_total_stock()
        
        if "stock_quantity" in request.data:
            product.stock_quantity = request.data["stock_quantity"]
        if "variants" in request.data:
            product.variants = request.data["variants"]
            
        product.save()
        
        note = request.data.get("note", "")
        ProductHistory.objects.create(
            product=product,
            action="stock_updated",
            old_value={"stock": old_stock},
            new_value={"stock": product.get_total_stock()},
            note=note
        )
        
        return Response({
            "stock_status": product.get_stock_status(),
            "stock_quantity": product.get_total_stock()
        })

class AdminProductScheduleView(APIView):
    permission_classes = [IsAdminToken]
    def patch(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        
        if "publish_at" in request.data:
            product.publish_at = request.data["publish_at"]
        if "unpublish_at" in request.data:
            product.unpublish_at = request.data["unpublish_at"]
            
        product.save()
        ProductHistory.objects.create(
            product=product,
            action="scheduled",
            note="Scheduling updated"
        )
        return Response(ProductSerializer(product).data)

class AdminProductUpdatePriceView(APIView):
    permission_classes = [IsAdminToken]
    def patch(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        
        old_price = product.price
        old_sale = product.sale_price
        
        if "price" in request.data:
            product.price = request.data["price"]
        if "sale_price" in request.data:
            product.sale_price = request.data["sale_price"]
            
        product.save()
        
        ProductHistory.objects.create(
            product=product,
            action="price_changed",
            old_value={"price": str(old_price), "sale_price": str(old_sale) if old_sale else None},
            new_value={"price": str(product.price), "sale_price": str(product.sale_price) if product.sale_price else None}
        )
        return Response(ProductSerializer(product).data)

class AdminProductHistoryView(APIView):
    permission_classes = [IsAdminToken]
    def get(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        history = product.history.all()
        # Serialize history simply
        data = []
        for h in history:
            data.append({
                "id": h.id,
                "action": h.action,
                "old_value": h.old_value,
                "new_value": h.new_value,
                "note": h.note,
                "created_at": h.created_at.isoformat()
            })
        return Response(data)

class AdminProductBulkView(APIView):
    permission_classes = [IsAdminToken]
    def post(self, request):
        ids = request.data.get("ids", [])
        action = request.data.get("action")
        value = request.data.get("value")
        
        if not ids or not action:
            return error_response("ids and action are required", 400)
            
        qs = Product.objects.filter(id__in=ids)
        count = qs.count()
        
        if action == "activate":
            qs.update(is_active=True)
            for p in qs: p.save() # trigger save loop if needed for in_stock, but update() doesn't
        elif action == "deactivate":
            qs.update(is_active=False)
        elif action == "delete":
            qs.delete()
        elif action == "set_badge":
            qs.update(badge=value)
            
        # Optional: log everything to history, but for simplicity we skip mass inserts here
        
        return Response({
            "count": count,
            "action": action
        })

class AdminProductAlertsView(APIView):
    permission_classes = [IsAdminToken]
    def get(self, request):
        # We need to manually calculate exact out of stock and low stock since variations hold stock
        # For simplicity in pure ORM, we'll fetch track_stock=True
        all_tracked = Product.objects.filter(track_stock=True)
        
        low_stock = []
        out_of_stock = []
        
        for p in all_tracked:
            total = p.get_total_stock()
            if total is None: continue
            if total <= 0:
                out_of_stock.append({
                    "id": p.id,
                    "name": p.name,
                    "ref": p.ref,
                    "stock_quantity": total,
                    "low_stock_threshold": p.low_stock_threshold,
                    "category": p.category
                })
            elif total <= p.low_stock_threshold:
                low_stock.append({
                    "id": p.id,
                    "name": p.name,
                    "ref": p.ref,
                    "stock_quantity": total,
                    "low_stock_threshold": p.low_stock_threshold,
                    "category": p.category
                })
                
        now = timezone.now()
        tomorrow = now + timezone.timedelta(days=1)
        
        scheduled_today_qs = Product.objects.filter(
            Q(publish_at__range=(now, tomorrow)) | Q(unpublish_at__range=(now, tomorrow))
        )
        
        scheduled_today = []
        for p in scheduled_today_qs:
            scheduled_today.append({
                "id": p.id,
                "name": p.name,
                "ref": p.ref,
                "category": p.category,
                "is_active": p.is_active,
                "publish_at": p.publish_at.isoformat() if p.publish_at else None,
                "unpublish_at": p.unpublish_at.isoformat() if p.unpublish_at else None
            })
            
        return Response({
            "low_stock": low_stock[:50], # Limit output size
            "out_of_stock": out_of_stock[:50],
            "scheduled_today": scheduled_today,
            "counts": {
                "low_stock": len(low_stock),
                "out_of_stock": len(out_of_stock),
                "scheduled_today": len(scheduled_today)
            }
        })
