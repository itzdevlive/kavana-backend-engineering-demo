import hashlib, hmac, json
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from .models import Order, WebhookEvent

@override_settings(PAYMENT_WEBHOOK_SECRET="test-secret", CELERY_TASK_ALWAYS_EAGER=True)
class BackendDemoTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_health(self):
        response = self.client.get("/api/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "ok")

    def test_create_order_and_validation(self):
        response = self.client.post("/api/orders/", {
            "customer_email": "qa@example.com", "amount_paise": 25000, "currency": "INR"
        }, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["amount_paise"], 25000)
        invalid = self.client.post("/api/orders/", {
            "customer_email": "qa@example.com", "amount_paise": 0, "currency": "INR"
        }, format="json")
        self.assertEqual(invalid.status_code, 400)

    def _signed_webhook(self, payload):
        body = json.dumps(payload, separators=(",", ":")).encode()
        signature = hmac.new(b"test-secret", body, hashlib.sha256).hexdigest()
        return self.client.post("/api/payments/webhook/", body, content_type="application/json",
                                HTTP_X_DEMO_SIGNATURE=signature)

    def test_webhook_is_idempotent(self):
        order = Order.objects.create(customer_email="pay@example.com", amount_paise=9900)
        payload = {"event_id": "evt_123", "order_id": order.id, "status": "captured"}
        first = self._signed_webhook(payload)
        second = self._signed_webhook(payload)
        self.assertEqual(first.status_code, 200)
        self.assertFalse(first.data["duplicate"])
        self.assertTrue(second.data["duplicate"])
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PAID)
        self.assertEqual(WebhookEvent.objects.count(), 1)

    def test_webhook_rejects_bad_signature(self):
        response = self.client.post("/api/payments/webhook/", b'{}',
            content_type="application/json", HTTP_X_DEMO_SIGNATURE="wrong")
        self.assertEqual(response.status_code, 401)
