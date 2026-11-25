# Kavana Backend Engineering Demo

A portfolio-grade backend demonstration built around a small **Order & Event API**.
It demonstrates REST APIs, PostgreSQL data modeling, idempotent payment-webhook handling,
Celery background jobs, Redis configuration, WebSocket notifications, Kafka event publishing,
automated tests, Docker, and operational health checks.

> This is a demonstrator, not a production payment system. The payment webhook uses HMAC
> verification and a simulated payment event. Do not connect real payment credentials until
> security, compliance, reconciliation, and provider-specific verification have been reviewed.

## Architecture

```text
Client
  |
  v
Django REST API ---- PostgreSQL (orders, webhook event ledger)
  |       |
  |       +---- Celery task queue ---- Redis broker
  |
  +---- WebSocket notifications (Django Channels / Redis channel layer)
  |
  +---- Kafka event publisher (optional; enabled with KAFKA_ENABLED=true)
```

## Quick start (Docker)

1. Copy `.env.example` to `.env`.
2. Run:

   ```bash
   docker compose up --build
   ```

3. In another terminal:

   ```bash
   docker compose exec web python manage.py migrate
   docker compose exec web python manage.py createsuperuser
   ```

4. Open `http://localhost:8000/api/health/`.

The API container starts Django's development server for demonstration. For production,
use a hardened ASGI/WSGI server, TLS termination, secrets management, structured logs,
metrics, database backups, and deployment-specific settings.

## Main endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health/` | Liveness/readiness-style health response |
| POST | `/api/orders/` | Create an order |
| GET | `/api/orders/` | List orders |
| GET | `/api/orders/{id}/` | Retrieve an order |
| POST | `/api/payments/webhook/` | Verify and record a simulated payment webhook |

### Create an order

```bash
curl -X POST http://localhost:8000/api/orders/ \
  -H 'Content-Type: application/json' \
  -d '{"customer_email":"demo@example.com","amount_paise":129900,"currency":"INR"}'
```

### Simulate a signed payment webhook

The demo secret is `local-demo-secret` unless overridden in `.env`. The signature is
an HMAC-SHA256 hex digest of the exact raw request body.

```bash
BODY='{"event_id":"evt_demo_001","order_id":1,"status":"captured"}'
SIGNATURE=$(printf '%s' "$BODY" | openssl dgst -sha256 -hmac 'local-demo-secret' | awk '{print $2}')
curl -X POST http://localhost:8000/api/payments/webhook/ \
  -H 'Content-Type: application/json' \
  -H "X-Demo-Signature: $SIGNATURE" \
  -d "$BODY"
```

Send the same `event_id` again to see idempotent duplicate handling.

## Run tests

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py test
```

For local non-Docker development, set `DATABASE_URL` to a PostgreSQL database or use the
SQLite fallback, and set `CELERY_TASK_ALWAYS_EAGER=true` to execute tasks synchronously.

## Engineering notes

- Money is stored as integer paise to avoid floating-point currency errors.
- Webhook event IDs have a database uniqueness constraint; duplicate delivery is safe.
- The webhook signature is checked against the raw request bytes using constant-time comparison.
- Order creation and payment state changes use database transactions.
- The list endpoint uses pagination and explicit ordering.
- Kafka publishing is optional so the demo runs without a Kafka broker.
- Celery tasks are safe to retry at the task boundary; real downstream side effects should
  also use idempotency keys.
- WebSocket notifications are best-effort signals; persisted database state remains canonical.

## Before presenting this to an employer

1. Run the project and tests yourself.
2. Replace the demo webhook with a provider's official signature scheme and test vectors.
3. Add authentication, authorization, rate limiting, and per-customer access controls.
4. Add OpenAPI schema generation, structured logging, metrics, tracing, and CI.
5. Deploy to a staging environment and include a short screen recording.
6. Be prepared to explain trade-offs and the limitations listed above.
