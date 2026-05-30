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
    active = models.BooleanField(default=False, db_index=True) # Cambiado a False por defecto
    created_at = models.DateTimeField(auto_now_add=True)
    card_size = models.IntegerField(default=15)
    current_song = models.ForeignKey(
        'Song', on_delete=models.SET_NULL, null=True, blank=True, related_name='current_in_games'
    )

    def play_random_song(self):
        # Filtra canciones en juego que NO han salido en ESTE juego específico
        historial_ids = self.history.values_list('song_id', flat=True)
        disponibles = Song.objects.filter(en_juego=True).exclude(id__in=historial_ids)
        
        if disponibles.exists():
            seleccionada = random.choice(list(disponibles))
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
    def check_bingo(self):
        # Cuenta cuántas canciones de este cartón están marcadas como True
        marcadas_count = self.songs.filter(marked=True).count()
        # Compara con el tamaño configurado en la partida
        return marcadas_count >= self.game.card_size


# ==========================================
# MODELO 5: CANCIONES DENTRO DEL CARTÓN
# ==========================================
class BingoCardSong(models.Model):
    card = models.ForeignKey(BingoCard, on_delete=models.CASCADE, related_name='songs')
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    marked = models.BooleanField(default=False, db_index=True) # Indispensable para validar bingo