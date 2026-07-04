import random
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator


# ==========================================
# MODELO 1: CANCION
# ==========================================
class Song(models.Model):
    # ✅ MinValueValidator: numero debe ser positivo
    numero = models.IntegerField(
        unique=True,
        verbose_name="Numero Identificador",
        validators=[MinValueValidator(1)]
    )
    nombre = models.CharField(max_length=255, verbose_name="Nombre de la Cancion")
    artista = models.CharField(max_length=255, verbose_name="Artista")
    fecha_publicacion = models.DateField(verbose_name="Fecha de Publicacion")
    en_juego = models.BooleanField(default=True, db_index=True)
    archivo_mp4 = models.FileField(upload_to='canciones/videos/', null=True, blank=True)
    imagen = models.ImageField(upload_to='canciones/portadas/', null=True, blank=True)

    class Meta:
        verbose_name = "Cancion"
        verbose_name_plural = "Canciones"
        ordering = ['numero']

    def __str__(self):
        return f"#{self.numero} - {self.nombre}"

    def save(self, *args, **kwargs):
        if self.pk:
            original = Song.objects.only('numero').get(pk=self.pk)
            if original.numero != self.numero:
                raise ValidationError("El numero identificador no se puede alterar.")
        super().save(*args, **kwargs)


# ==========================================
# MODELO 2: PARTIDA DE BINGO
# ==========================================
class Game(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nombre de la sala")
    active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # ✅ Validadores de rango minimo
    card_size = models.IntegerField(
        default=15,
        verbose_name="Tamano del carton",
        validators=[MinValueValidator(5)]
    )
    chat_enabled = models.BooleanField(default=True)
    current_song = models.ForeignKey(
        'Song',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='current_in_games'
    )
    total_songs_limit = models.IntegerField(
        default=90,
        verbose_name="Limite de canciones",
        help_text="Total de canciones para esta partida",
        validators=[MinValueValidator(10)]
    )
    songs_in_game = models.ManyToManyField(
        Song,
        related_name="games_included",
        blank=True
    )

    class Meta:
        verbose_name = "Partida"
        verbose_name_plural = "Partidas"

    def __str__(self):
        return f"{self.name} {'(Activa)' if self.active else ''}"

    # ✅ Validacion a nivel de modelo: card_size < total_songs_limit
    def clean(self):
        if self.card_size and self.total_songs_limit:
            if self.card_size >= self.total_songs_limit:
                raise ValidationError(
                    "El tamano del carton debe ser menor que el limite de canciones."
                )

    def play_random_song(self):
        historial_ids = self.history.values_list('song_id', flat=True)
        # ✅ FIX: Traer solo IDs en vez de objetos completos
        disponibles_ids = list(
            self.songs_in_game.exclude(id__in=historial_ids).values_list('id', flat=True)
        )

        if not disponibles_ids:
            return None

        # ✅ FIX: random.choice sobre lista de IDs — mucho mas eficiente que order_by('?')
        id_seleccionado = random.choice(disponibles_ids)
        seleccionada = Song.objects.get(pk=id_seleccionado)

        # ✅ FIX: update() en vez de save() — solo toca el campo current_song
        Game.objects.filter(pk=self.pk).update(current_song=seleccionada)
        self.current_song = seleccionada  # mantener instancia en memoria actualizada

        GameHistory.objects.create(game=self, song=seleccionada)
        return seleccionada


# ==========================================
# MODELO 3: HISTORIAL DE CANCIONES EMITIDAS
# ==========================================
class GameHistory(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='history')
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    played_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Historial de cancion"
        verbose_name_plural = "Historial de canciones"
        ordering = ['-played_at']
        # ✅ Indice compuesto para acelerar consultas por partida ordenadas por fecha
        indexes = [
            models.Index(fields=['game', '-played_at'], name='idx_history_game_played'),
        ]


# ==========================================
# MODELO 4: CARTON DEL JUGADOR
# ==========================================
class BingoCard(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bingo_cards')
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='cards')
    # ✅ FIX: null=False — el codigo siempre debe existir antes de crear el carton
    codigo = models.CharField(max_length=14, unique=True)

    class Meta:
        verbose_name = "Carton de bingo"
        verbose_name_plural = "Cartones de bingo"
        # ✅ FIX: restriccion a nivel de BD — un usuario, un carton por partida
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'game'],
                name='unique_carton_por_usuario_y_partida'
            )
        ]

    def __str__(self):
        return f"Carton {self.codigo} — {self.user.username}"

    def check_bingo(self):
        # ✅ FIX: verificar que TODAS las canciones del carton esten marcadas,
        # no solo contar las marcadas
        total = self.songs.count()
        if total == 0:
            return False
        marcadas = self.songs.filter(marked=True).count()
        return total == marcadas and total >= self.game.card_size


# ==========================================
# MODELO 5: CANCIONES DENTRO DEL CARTON
# ==========================================
class BingoCardSong(models.Model):
    card = models.ForeignKey(BingoCard, on_delete=models.CASCADE, related_name='songs')
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    marked = models.BooleanField(default=False, db_index=True)

    class Meta:
        verbose_name = "Cancion en carton"
        verbose_name_plural = "Canciones en cartones"
        # ✅ Evitar que la misma cancion aparezca dos veces en el mismo carton
        constraints = [
            models.UniqueConstraint(
                fields=['card', 'song'],
                name='unique_cancion_por_carton'
            )
        ]
        # ✅ Indice compuesto para acelerar deteccion de ganadores
        indexes = [
            models.Index(fields=['card', 'marked'], name='idx_bingocardson_card_marked'),
        ]


# ==========================================
# MODELO 6: MENSAJES DE CHAT
# ==========================================
class ChatMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(max_length=500)  # ✅ Limite de caracteres para evitar spam
    timestamp = models.DateTimeField(auto_now_add=True)
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='messages')

    class Meta:
        verbose_name = "Mensaje de chat"
        verbose_name_plural = "Mensajes de chat"
        ordering = ['timestamp']
        # ✅ Indice para cargar mensajes de una partida rapidamente
        indexes = [
            models.Index(fields=['game', 'timestamp'], name='idx_chat_game_timestamp'),
        ]