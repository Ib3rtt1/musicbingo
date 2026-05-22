from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User
import random
#
from django.core.exceptions import ValidationError

#modelo song
class Song(models.Model):
    numero = models.IntegerField(unique=True, verbose_name="Número Identificador")
    nombre = models.CharField(max_length=255, verbose_name="Nombre de la Canción")
    artista = models.CharField(max_length=255, verbose_name="Artista")
    fecha_publicacion = models.DateField(verbose_name="Fecha de Publicación")

    # Campo para la tómbola
    en_juego = models.BooleanField(default=True, verbose_name="¿Disponible para esta partida?")
    
    # Campos multimedia que permiten nulos para el Paso 2
    archivo_mp4 = models.FileField(
        upload_to='canciones/videos/',
        verbose_name="Archivo MP4 (Video/Audio)",
        null=True,
        blank=True
    )
    imagen = models.ImageField(
        upload_to='canciones/portadas/',
        verbose_name="Imagen de Portada",
        null=True,
        blank=True
    )

    def __str__(self):
        return f"#{self.numero} - {self.nombre} ({self.artista})"

    # Validar que el número NO se pueda alterar después de creado
    def save(self, *args, **kwargs):
        if self.pk:  # Si ya existe en la base de datos (es una actualización)
            # ⚡ Optimizado con .only() para no sobrecargar la base de datos
            original = Song.objects.only('numero').get(pk=self.pk)
            if original.numero != self.numero:
                raise ValidationError("Seguridad: El número correspondiente de la canción no se puede alterar.")
        
        # 💻 ¡Corregido el cierre del paréntesis aquí!
        super().save(*args, **kwargs)
        
    # unique=True evita que dos canciones tengan el mismo número
    
    numero = models.IntegerField(unique=True, verbose_name="Número Identificador")
    nombre = models.CharField(max_length=255, verbose_name="Nombre de la Canción")
    artista = models.CharField(max_length=255, verbose_name="Artista")
    fecha_publicacion = models.DateField(verbose_name="Fecha de Publicación")

    # 🔥 NUEVO CAMPO: Tú decides si entra al sorteo o no
    en_juego = models.BooleanField(default=True, verbose_name="¿Disponible para esta partida?")
    
    # 🔥 Al agregar null=True y blank=True, permites que se guarden vacíos al inicio
    archivo_mp4 = models.FileField(
        upload_to='canciones/videos/', 
        verbose_name="Archivo MP4 (Video/Audio)", 
        null=True, 
        blank=True
    )
    imagen = models.ImageField(
        upload_to='canciones/portadas/', 
        verbose_name="Imagen de Portada", 
        null=True, 
        blank=True
    )
    def __str__(self):
        return f"#{self.numero} - {self.nombre} ({self.artista})"

    # 🔥 Validar que el número NO se pueda alterar después de creado
    def save(self, *args, **kwargs):
        if self.pk: # Si el objeto ya existe en la base de datos (es una actualización)
            original = Song.objects.get(pk=self.pk)
            if original.numero != self.numero:
                raise ValidationError("Seguridad: El número correspondiente de la canción no se puede alterar.")
        super().save(*args, **kwargs)

class Game(models.Model):
    name = models.CharField(max_length=100)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    current_song = models.ForeignKey(
        Song,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='current_song'
    )

    def play_random_song(self):
        
        songs = Song.objects.filter(en_juego=True)
        
        if songs.exists():
            self.current_song = random.choice(songs)
            self.save()

        return self.current_song

    def __str__(self):
        return self.name


class BingoCard(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)

    def __str__(self):
        return f"Card {self.id} - {self.user.username}"


class BingoCardSong(models.Model):
    card = models.ForeignKey(BingoCard, on_delete=models.CASCADE)
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    marked = models.BooleanField(default=False)

    def __str__(self):
        # Esta línea de abajo DEBE tener una sangría (4 espacios más adentro que el "def")
        return f"{self.card.id} - {self.song.nombre}"