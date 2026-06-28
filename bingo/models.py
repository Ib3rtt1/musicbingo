import random
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

# ==========================================
# MODELO 1: CANCIÓN
# ==========================================
class Song(models.Model):
    numero = models.IntegerField(unique=True, verbose_name="Número Identificador")
    nombre = models.CharField(max_length=255, verbose_name="Nombre de la Canción")
    artista = models.CharField(max_length=255, verbose_name="Artista")
    fecha_publicacion = models.DateField(verbose_name="Fecha de Publicación")
    en_juego = models.BooleanField(default=True, db_index=True) # Indexado para filtrado rápido
    archivo_mp4 = models.FileField(upload_to='canciones/videos/', null=True, blank=True)
    imagen = models.ImageField(upload_to='canciones/portadas/', null=True, blank=True)

    def __str__(self):
        return f"#{self.numero} - {self.nombre}"

    def save(self, *args, **kwargs):
        if self.pk:
            original = Song.objects.only('numero').get(pk=self.pk)
            if original.numero != self.numero:
                raise ValidationError("El número identificador no se puede alterar.")
        super().save(*args, **kwargs)

# ==========================================
# MODELO 2: PARTIDA DE BINGO
# ==========================================
class Game(models.Model):
    name = models.CharField(max_length=100)
    active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    card_size = models.IntegerField(default=15)
    chat_enabled = models.BooleanField(default=True)
    current_song = models.ForeignKey(
        'Song', on_delete=models.SET_NULL, null=True, blank=True, related_name='current_in_games'
    )
    total_songs_limit = models.IntegerField(default=90, help_text="Total de canciones para esta partida")
    
    # NUEVO: Aquí guardaremos las canciones elegidas al azar al crear la sala
    songs_in_game = models.ManyToManyField(Song, related_name="games_included")

    def play_random_song(self):
        # Filtramos canciones YA CANTADAS en este juego específico
        historial_ids = self.history.values_list('song_id', flat=True)
        
        # Filtramos canciones DISPONIBLES dentro de las que pertenecen a ESTA partida
        # y que aún no han salido
        disponibles = self.songs_in_game.exclude(id__in=historial_ids)
        
        if disponibles.exists():
            seleccionada = disponibles.order_by('?').first()
            self.current_song = seleccionada
            self.save()
            GameHistory.objects.create(game=self, song=seleccionada)
            return seleccionada
        return None

    def __str__(self):
        return f"{self.name} {'(Activa)' if self.active else ''}"
# ==========================================
# MODELO 3: HISTORIAL DE CANCIONES EMITIDAS
# ==========================================
class GameHistory(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='history')
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    played_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-played_at']


# ==========================================
# MODELO 4: CARTÓN DEL JUGADOR
# ==========================================
class BingoCard(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bingo_cards')
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='cards')
    # Cambiamos a null=True para evitar errores con registros previos
    codigo = models.CharField(max_length=14, unique=True, null=True, blank=True) 

    def check_bingo(self):
        # Asegúrate de que 'self.songs' exista como related_name en BingoCardSong
        marcadas_count = self.songs.filter(marked=True).count()
        return marcadas_count >= self.game.card_size

# ==========================================
# MODELO 5: CANCIONES DENTRO DEL CARTÓN
# ==========================================
class BingoCardSong(models.Model):
    card = models.ForeignKey(BingoCard, on_delete=models.CASCADE, related_name='songs')
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    marked = models.BooleanField(default=False, db_index=True) # Indispensable para validar bingo


# ==========================================
# MODELO 6: MENSAJES DE CHAT
# ==========================================
class ChatMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='messages')

    class Meta:
        ordering = ['timestamp']