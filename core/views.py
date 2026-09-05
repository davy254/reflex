from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from .models import DeliveryRequest, StatusEvent, Notification
from .realtime import broadcast_to
from . import sms_worker


def ensure_users():
    """Auto-create the demo accounts on first page load (no manual setup)."""
    for username, role in [("retailer", "retailer_staff"), ("dispatcher", "dispatcher"),
                           ("rider1", "rider"), ("rider2", "rider"), ("rider3", "rider")]:
        user, created = User.objects.get_or_create(username=username)
        if created:
            user.set_password("demo123")
            user.save()


def serialize_delivery(d):
    return {
        "id": str(d.id), "short": str(d.id)[:8],
        "customer_name": d.customer_name, "customer_phone": d.customer_phone,
        "address": d.delivery_address, "item": d.item_description,
        "status": d.status,
        "rider": d.assigned_rider.username if d.assigned_rider else None,
        "qr_token": str(d.qr_code_token),
        "events": [{"from": e.from_status, "to": e.to_status, "actor": e.actor.username,
                    "time": e.timestamp.strftime("%H:%M:%S"), "ts": e.timestamp.isoformat(),
                    "photo": e.photo_proof, "scan": e.scan_verified}
                   for e in d.events.order_by("timestamp")],
    }


def serialize_sms(n):
    return {"id": n.id, "payload": n.payload, "status": n.status,
            "phone": n.delivery.customer_phone}


@ensure_csrf_cookie
def demo(request):
    ensure_users()
    return render(request, "core/demo.html")


def api_state(request):
    """REST fallback — the page fetches this on load AND on every WebSocket reconnect."""
    ensure_users()
    return JsonResponse({
        "deliveries": [serialize_delivery(d) for d in DeliveryRequest.objects.order_by("-created_at")],
        "sms": [serialize_sms(n) for n in Notification.objects.order_by("id")],
    })


@require_POST
def create_delivery(request):
    retailer = User.objects.get(username="retailer")
    d = DeliveryRequest.objects.create(
        retailer=retailer,
        customer_name=request.POST.get("customer_name") or "Walk-in customer",
        customer_phone=request.POST.get("customer_phone") or "+254700000000",
        delivery_address=request.POST.get("delivery_address") or "—",
        item_description=request.POST.get("item_description") or "—",
    )
    StatusEvent.objects.create(delivery=d, to_status="PENDING", actor=retailer)
    groups = ["dispatch_board", "retailer_shop1"]
    broadcast_to(["demo_page"] + groups,
                 {"kind": "new_request", "delivery": serialize_delivery(d), "groups": groups})
    return JsonResponse({"ok": True})


@require_POST
def assign_rider(request):
    d = get_object_or_404(DeliveryRequest, id=request.POST["delivery_id"])
    rider = User.objects.get(username=request.POST["rider"])
    dispatcher = User.objects.get(username="dispatcher")
    if d.status != "PENDING":
        return JsonResponse({"ok": False, "error": "Already assigned"})
    d.assigned_rider, d.status = rider, "ASSIGNED"
    d.save()
    StatusEvent.objects.create(delivery=d, from_status="PENDING", to_status="ASSIGNED", actor=dispatcher)
    groups = ["dispatch_board", f"rider_{rider.username}", "retailer_shop1"]
    broadcast_to(["demo_page"] + groups,
                 {"kind": "assigned", "delivery": serialize_delivery(d), "groups": groups})
    return JsonResponse({"ok": True})


@require_POST
def advance_status(request):
    d = get_object_or_404(DeliveryRequest, id=request.POST["delivery_id"])
    rider = User.objects.get(username=request.POST["rider"])
    action = request.POST["action"]
    if {"ASSIGNED": "PICKED_UP", "PICKED_UP": "DELIVERED"}.get(d.status) != action:
        return JsonResponse({"ok": False, "error": "Invalid transition"})

    photo, scan = False, False
    if action == "DELIVERED":
        photo = request.POST.get("photo") == "1"
        if not photo:
            return JsonResponse({"ok": False, "error": "Photo proof is REQUIRED at DELIVERED (hard rule)."})
        # Soft rule: wrong scan does NOT block, it only flags the discrepancy.
        scan = request.POST.get("scan_token", "").strip() == str(d.qr_code_token)

    old = d.status
    d.status = action
    d.save()
    StatusEvent.objects.create(delivery=d, from_status=old, to_status=action,
                               actor=rider, photo_proof=photo, scan_verified=scan)
    groups = ["dispatch_board", f"rider_{rider.username}", "retailer_shop1"]
    broadcast_to(["demo_page"] + groups,
                 {"kind": "status_update", "delivery": serialize_delivery(d), "groups": groups})

    if action == "PICKED_UP":
        sms_worker.queue_sms(d, f"Reflex: {rider.username} picked up your parcel ({d.id.hex[:8]}). On the way!")
    if action == "DELIVERED":
        sms_worker.queue_sms(d, f"Reflex: Your parcel ({d.id.hex[:8]}) was DELIVERED. Thank you!")
    return JsonResponse({"ok": True})