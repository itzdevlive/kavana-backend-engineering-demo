import json
from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Order
from .serializers import OrderSerializer
from .services import verify_demo_signature, process_payment_event
from .tasks import record_order_created
from .events import publish_order_event

class HealthView(APIView):
    authentication_classes = []
    permission_classes = []
    def get(self, request):
        return Response({"status": "ok", "service": "kavana-backend-demo"})

class OrderListCreateView(generics.ListCreateAPIView):
    queryset = Order.objects.all().select_related()
    serializer_class = OrderSerializer
    def perform_create(self, serializer):
        with transaction.atomic():
            order = serializer.save()
            transaction.on_commit(lambda: record_order_created.delay(order.id))
            transaction.on_commit(lambda: publish_order_event({
                "event": "order.created", "order_id": order.id,
                "amount_paise": order.amount_paise, "currency": order.currency
            }))

class OrderDetailView(generics.RetrieveAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

class PaymentWebhookView(APIView):
    authentication_classes = []
    permission_classes = []
    def post(self, request):
        raw_body = request.body
        signature = request.headers.get("X-Demo-Signature", "")
        if not verify_demo_signature(raw_body, signature):
            return Response({"detail": "Invalid signature."}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            payload = json.loads(raw_body)
            result = process_payment_event(payload)
        except (json.JSONDecodeError, DjangoValidationError, Order.DoesNotExist, ValueError) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        if not result.get("duplicate"):
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                "order_updates",
                {"type": "order.update", "data": {
                    "event": "payment.updated", "event_id": result["event_id"],
                    "order_status": result.get("order_status")
                }},
            )
        return Response(result, status=status.HTTP_200_OK)
