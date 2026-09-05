from django.urls import path
from . import consumers

websocket_urlpatterns = [path("ws/demo/", consumers.DemoConsumer.as_asgi())]