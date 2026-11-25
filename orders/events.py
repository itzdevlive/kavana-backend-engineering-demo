import json
from django.conf import settings

def publish_order_event(event: dict):
    if not settings.KAFKA_ENABLED:
        return {"published": False, "reason": "Kafka disabled"}
    from kafka import KafkaProducer
    producer = KafkaProducer(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS.split(","),
        value_serializer=lambda value: json.dumps(value).encode("utf-8"),
        acks="all",
        retries=3,
    )
    try:
        future = producer.send("orders.events", event)
        metadata = future.get(timeout=10)
        return {"published": True, "topic": metadata.topic, "partition": metadata.partition}
    finally:
        producer.flush()
        producer.close()
