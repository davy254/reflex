# ⚡ Reflex — Real-Time Delivery Dispatch & Tracking System


**Author:** David Munyiri Ndirangu  
**Status:** Working Prototype (Frozen Design Build)  
**Stack:** Django, Django Channels, WebSockets, Tailwind CSS, Vanilla JS


---


## 📖 Description


**Reflex** is a real-time logistics and delivery tracking application designed to bridge the gap between retailers, dispatchers, and riders. Built with a focus on edge-case resilience, Reflex ensures that package tracking remains accurate even in low-connectivity environments. 


This repository contains a fully functional, single-page prototype that demonstrates the core architectural decisions of the system, including real-time WebSocket broadcasting, the Outbox pattern for SMS notifications, and graceful degradation for hardware scanning failures.


---


## ✨ Key Features


- **Real-Time Dispatch Board:** Powered by Django Channels (WebSockets). New delivery requests appear instantly on the dispatcher's board without page refreshes.
- **Simulated SMS Outbox Pattern:** SMS notifications are decoupled from the main request cycle. Messages are queued and "delivered" asynchronously, ensuring third-party API outages never block core operations.
- **Graceful QR Verification:** At the point of delivery, the system requires a photo and a QR scan. If the QR scan fails to match, the system logs a discrepancy (`scan_verified = False`) rather than hard-blocking the rider, preventing stranded packages.
- **Hybrid Real-Time/REST Architecture:** If a WebSocket connection drops (e.g., a rider goes underground), the frontend automatically falls back to REST polling on reconnect to sync the UI state.
- **Server-Authoritative Security:** QR tokens are generated server-side as UUIDs to prevent client-side spoofing. Sequential IDs are never exposed to the public.
- **Single-Page Demo UI:** A unified Tailwind CSS interface that displays the Retailer, Dispatcher, Riders, and a simulated "Customer Phone" simultaneously for easy stakeholder demonstrations.


---


## 📂 Project Structure


```text
reflex-proto/
├── manage.py
├── reflex/                  # Main Django project configuration
│   ├── settings.py          # Configured for In-Memory channels & SQLite (prototype)
│   ├── asgi.py              # ASGI config routing HTTP and WebSockets
│   └── urls.py              # Main URL routing
└── core/                    # Main application logic
    ├── models.py            # Data models (DeliveryRequest, StatusEvent, Notification)
    ├── views.py             # REST API endpoints and UI rendering
    ├── consumers.py         # Django Channels WebSocket consumers
    ├── routing.py           # WebSocket URL routing
    ├── realtime.py          # Helper functions for broadcasting to channel groups
    ├── sms_worker.py        # Simulated background worker for SMS outbox
    └── templates/
        └── core/
            └── demo.html    # The unified Tailwind CSS single-page demo interface
```


---


## 🛠️ Setup & Installation


This prototype is designed to run with zero external dependencies (uses SQLite and In-Memory channel layers). 


### Prerequisites
- Python 3.10 or higher
- Git (optional)


### Steps


1. **Clone the repository and navigate to the project:**
   ```bash
   cd reflex-proto
   ```


2. **Create and activate a virtual environment:**
   ```bash
   # macOS/Linux
   python -m venv venv
   source venv/bin/activate


   # Windows
   python -m venv venv
   venv\Scripts\activate
   ```


3. **Install dependencies:**
   ```bash
   pip install django channels daphne
   ```


4. **Apply database migrations:**
   ```bash
   python manage.py makemigrations core
   python manage.py migrate
   ```


5. **Run the development server:**
   ```bash
   python manage.py runserver
   ```


The application will now be running at `http://127.0.0.1:8000/`.


---


## 🚀 Usage (Demo Guide)


Open `http://127.0.0.1:8000/` in your browser. The interface is divided into 5 columns representing the entire ecosystem.


**The Happy Path Demo:**
1. **Retailer (Column 1):** Fill out the delivery form and click **Create**. Watch the QR code generate instantly.
2. **Dispatcher (Column 2):** Look at the "Pending queue". The new request appears in real-time. Select `rider1` and click **Assign**.
3. **Rider 1 (Column 3):** The assigned task appears. Click **Mark PICKED UP**.
4. **Customer Phone (Column 5):** Watch the SMS message appear as `⏳ queued` and flip to `✓✓ delivered` 2 seconds later (simulating the background worker).
5. **Rider 1 (Column 3):** Click **Mark DELIVERED**. Ensure the "Photo proof" checkbox is ticked, and click **✅ scan correct**.
6. **Audit Log (Column 2):** Verify the `✅scan` flag in the dispatcher's audit log.


**Testing Edge Cases:**
- **Scan Mismatch:** Try delivering a second package, but click **⚠️ scan wrong**. The delivery will succeed, but the audit log will flag `⚠️scan-mismatch`.
- **Missing Photo:** Untick the photo proof and try to deliver. The server will reject the action (Hard Rule).
- **WebSocket Disconnect:** Open the browser's Developer Tools (F12) -> Network -> Throttling, and set it to "Offline". Re-enable it to watch the UI auto-recover via the REST fallback.


---


## 🏭 Moving to Production


This prototype uses an In-Memory channel layer and SQLite. To deploy Reflex to production, the following architectural swaps must be made:


1. **Database:** Swap SQLite for **PostgreSQL** to ensure relational integrity and handle concurrent writes.
2. **Channel Layer:** Swap the In-Memory layer for **Redis** (`channels-redis`) to allow WebSocket pub/sub across multiple Daphne/Gunicorn server workers.
3. **Background Workers:** Replace the simulated `threading.Timer` in `sms_worker.py` with a robust task queue like **Celery** or **Django-Q** backed by Redis/RabbitMQ.
4. **File Storage:** Implement a real `ImageField` upload to cloud storage (AWS S3 / DigitalOcean Spaces) for proof-of-delivery photos.
5. **ASGI Server:** Serve the application using **Daphne** or **Uvicorn** behind a reverse proxy like **Nginx**, and use **Gunicorn** for standard HTTP WSGI fallback if needed.


*Example `settings.py` production overrides:*
```python
# Production Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "reflex_db",
        "USER": "db_user",
        "PASSWORD": "secure_password",
        "HOST": "localhost",
        "PORT": "5432",
    }
}


# Production Channel Layer
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [("127.0.0.1", 6379)]},
    },
}
```


---


## 📄 License


This project is licensed under the MIT License


*Copyright (c) 2026 David Munyiri Ndirangu*
