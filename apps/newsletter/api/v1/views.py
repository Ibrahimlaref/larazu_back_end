from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.newsletter.models import NewsletterSubscriber


class NewsletterSubscribeView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = (request.data.get("email") or "").strip()
        if not email:
            return Response({"error": "email is required"}, status=400)
        if NewsletterSubscriber.objects.filter(email__iexact=email).exists():
            return Response({"ok": True})
        NewsletterSubscriber.objects.create(email=email)
        return Response({"ok": True}, status=status.HTTP_201_CREATED)
