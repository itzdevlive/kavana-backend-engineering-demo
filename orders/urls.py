from django.urls import path
from .views import HealthView, OrderListCreateView, OrderDetailView, PaymentWebhookView
urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
    path("orders/", OrderListCreateView.as_view(), name="orders"),
    path("orders/<int:pk>/", OrderDetailView.as_view(), name="order-detail"),
    path("payments/webhook/", PaymentWebhookView.as_view(), name="payment-webhook"),
]
