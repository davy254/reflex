import threading
from .realtime import broadcast_to


def queue_sms(delivery, text):
    from .models import Notification
    n = Notification.objects.create(delivery=delivery, payload=text)
    sms = {"id": n.id, "payload": n.payload, "status": n.status, "phone": delivery.customer_phone}
    broadcast_to(["demo_page", "sms_phone"],
                 {"kind": "sms_queued", "sms": sms, "groups": ["sms_phone"]})
    threading.Timer(2.0, _send, args=[n.id]).start()   # simulates the background worker


def _send(notification_id):
    from .models import Notification
    try:
        n = Notification.objects.get(id=notification_id)
    except Notification.DoesNotExist:
        return
    n.status = "sent"
    n.attempts += 1
    n.save()
    broadcast_to(["demo_page", "sms_phone"],
                 {"kind": "sms_sent", "id": n.id, "groups": ["sms_phone"]})