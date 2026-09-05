from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def broadcast_to(groups, data):
    """Send one WebSocket event to several Channels groups (design groups + demo_page)."""
    layer = get_channel_layer()
    for g in groups:
        async_to_sync(layer.group_send)(g, {"type": "broadcast.event", "data": data})