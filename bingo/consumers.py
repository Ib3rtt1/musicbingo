import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser


class BingoConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        # Rechazar conexiones no autenticadas
        if self.scope['user'] is None or isinstance(self.scope['user'], AnonymousUser):
            await self.close()
            return

        self.game_id = self.scope['url_route']['kwargs']['game_id']
        self.group_name = f'bingo_{self.game_id}'

        # Unirse al grupo de la partida
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    # Recibe mensaje del cliente (solo chat)
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        tipo = data.get('type')

        if tipo == 'chat_message':
            content = data.get('content', '').strip()
            if not content or len(content) > 500:
                return

            # Verificar que el chat este habilitado
            chat_habilitado = await self.get_chat_status()
            if not chat_habilitado:
                return

            # Guardar en BD
            await self.guardar_mensaje(content)

            # Broadcast al grupo
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'chat_message',
                    'content': content,
                    'user': self.scope['user'].username,
                }
            )

    # Handler: nuevo mensaje de chat
    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'content': event['content'],
            'user': event['user'],
        }))

    # Handler: nueva cancion cantada (lo llama la vista consola_juego)
    async def nueva_cancion(self, event):
        await self.send(text_data=json.dumps({
            'type': 'nueva_cancion',
            'song_id': event['song_id'],
            'song_nombre': event['song_nombre'],
            'song_artista': event['song_artista'],
        }))

    # Handler: ganador detectado
    async def ganador(self, event):
        await self.send(text_data=json.dumps({
            'type': 'ganador',
            'username': event['username'],
            'codigo': event['codigo'],
        }))

    # -------------------------------------------------------
    # Helpers de base de datos (sync_to_async obligatorio)
    # -------------------------------------------------------
    @database_sync_to_async
    def get_chat_status(self):
        from .models import Game
        game = Game.objects.filter(pk=self.game_id).first()
        return game.chat_enabled if game else False

    @database_sync_to_async
    def guardar_mensaje(self, content):
        from .models import Game, ChatMessage
        game = Game.objects.filter(pk=self.game_id).first()
        if game:
            ChatMessage.objects.create(
                user=self.scope['user'],
                content=content,
                game=game
            )