from rest_framework import serializers
from .models import Order

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["id", "customer_email", "amount_paise", "currency", "status", "created_at", "updated_at"]
        read_only_fields = ["id", "status", "created_at", "updated_at"]

    def validate_amount_paise(self, value):
        if value <= 0:
            raise serializers.ValidationError("amount_paise must be greater than zero.")
        if value > 100_000_000:
            raise serializers.ValidationError("amount_paise exceeds the demo limit.")
        return value

    def validate_currency(self, value):
        value = value.upper()
        if len(value) != 3 or not value.isalpha():
            raise serializers.ValidationError("currency must be a three-letter code.")
        return value
