import hashlib, hmac, json
from django.conf import settings
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import Order, WebhookEvent

def verify_demo_signature(raw_body: bytes, supplied_signature: str) -> bool:
    expected = hmac.new(
        settings.PAYMENT_WEBHOOK_SECRET.encode("utf-8"), raw_body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, supplied_signature or "")

@transaction.atomic
def process_payment_event(payload: dict):
    event_id = payload.get("event_id")
    order_id = payload.get("order_id")
    status = payload.get("status")
    if not event_id or not order_id or status not in ("captured", "failed"):
        raise ValidationError("event_id, order_id and a valid status are required.")

    event, created = WebhookEvent.objects.get_or_create(
        event_id=event_id,
        defaults={"event_type": "payment.status", "payload": payload},
    )
    if not created:
        return {"duplicate": True, "event_id": event_id}

    order = Order.objects.select_for_update().get(pk=order_id)
    # Do not downgrade a paid order due to a late failure notification.
    if order.status != Order.Status.PAID:
        order.status = Order.Status.PAID if status == "captured" else Order.Status.FAILED
        order.save(update_fields=["status", "updated_at"])
    return {"duplicate": False, "event_id": event_id, "order_status": order.status}
