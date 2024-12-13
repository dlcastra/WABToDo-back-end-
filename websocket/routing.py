from django.urls import re_path

from websocket import consumers

websocket_urlpatterns = [
    re_path(r"^ws/comnt/$", consumers.CommentConsumer.as_asgi()),
]
