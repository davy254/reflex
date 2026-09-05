import uuid
from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=[
        ("retailer_staff", "Retailer Staff"),
        ("dispatcher", "Dispatcher"),
        ("rider", "Rider"),
    ])
    shop = models.CharField(max_length=50, default="Main Shop")


class DeliveryRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING"
        ASSIGNED = "ASSIGNED"
        PICKED_UP = "PICKED_UP"
        DELIVERED = "DELIVERED"
        FAILED = "FAILED"
        CANCELLED = "CANCELLED"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    retailer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="deliveries")
    customer_name = models.CharField(max_length=100)
    customer_phone = models.CharField(max_length=20)
    delivery_address = models.TextField()
    item_description = models.TextField()
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    assigned_rider = models.ForeignKey(User, null=True, blank=True,
                                       on_delete=models.SET_NULL, related_name="assigned_deliveries")
    qr_code_token = models.UUIDField(default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class StatusEvent(models.Model):
    delivery = models.ForeignKey(DeliveryRequest, on_delete=models.CASCADE, related_name="events")
    from_status = models.CharField(max_length=12, blank=True, default="")
    to_status = models.CharField(max_length=12)
    actor = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    photo_proof = models.BooleanField(default=False)     # simulated in prototype
    scan_verified = models.BooleanField(default=False)


class Notification(models.Model):   # the SMS outbox
    delivery = models.ForeignKey(DeliveryRequest, on_delete=models.CASCADE, related_name="notifications")
    channel = models.CharField(max_length=10, default="sms")
    payload = models.TextField()
    status = models.CharField(max_length=10, default="pending",
                              choices=[("pending", "pending"), ("sent", "sent"), ("failed", "failed")])
    attempts = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)