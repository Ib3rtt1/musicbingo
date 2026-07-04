from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/bingo/(?P<game_id>\d+)/$', consumers.BingoConsumer.as_asgi()),
]