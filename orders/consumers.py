import json
from channels.generic.websocket import AsyncWebsocketConsumer

class OrderEventsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Demo endpoint. Add authenticated, per-user group authorization before production use.
        await self.channel_layer.group_add("order_updates", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("order_updates", self.channel_name)

    async def order_update(self, event):
        await self.send(text_data=json.dumps(event["data"]))
