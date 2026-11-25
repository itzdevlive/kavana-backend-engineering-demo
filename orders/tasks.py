from celery import shared_task
from django.utils import timezone

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def record_order_created(self, order_id: int):
    # Replace with a real downstream integration; keep side effects idempotent.
    return {"order_id": order_id, "processed_at": timezone.now().isoformat()}
