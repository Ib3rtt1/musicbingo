from rest_framework import serializers
from .models import Song, Game, BingoCard, BingoCardSong

class SongSerializer(serializers.ModelSerializer):
    class Meta:
        model = Song
        fields = '__all__'


class GameSerializer(serializers.ModelSerializer):
    # Esto mostrará todos los detalles de la canción actual en las consultas (GET)
    current_song = SongSerializer(read_only=True)
    
    # Este campo oculto te permitirá asignar una canción usando solo su ID al crear/editar (POST/PUT)
    current_song_id = serializers.PrimaryKeyRelatedField(
        queryset=Song.objects.all(), 
        source='current_song', 
        write_only=True
    )

    class Meta:
        model = Game
        fields = '__all__'


class BingoCardSongSerializer(serializers.ModelSerializer):
    song = SongSerializer(read_only=True)

    class Meta:
        model = BingoCardSong
        fields = '__all__'


class BingoCardSerializer(serializers.ModelSerializer):
    # Muestra las canciones que pertenecen a este cartón a través del modelo intermedio
    # NOTA: Si en tu modelo 'BingoCardSong' definiste un 'related_name' hacia BingoCard, 
    # cambia 'bingocardsong_set' por ese nombre.
    songs = BingoCardSongSerializer(many=True, read_only=True, source='bingocardsong_set')

    class Meta:
        model = BingoCard
        fields = '__all__'