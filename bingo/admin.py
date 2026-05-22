from django.contrib import admin
from .models import Song, Game, BingoCard, BingoCardSong

# 1️⃣ REGISTRO AVANZADO DE CANCIONES (Usando la clase personalizada)
@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    # Lista de campos que se verán en la tabla principal del admin
    list_display = ('numero', 'nombre', 'artista', 'en_juego')
    
    # Permite buscar canciones por nombre o artista rápidamente
    search_fields = ('nombre', 'artista')
    
    # Añade un filtro lateral para activar/desactivar canciones en las tandas
    list_filter = ('en_juego',)

    # Candado visual: Bloquea el número identificador si estás editando
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Si el objeto ya existe (editando), el número no se toca
            return ['numero']
        return []


# 2️⃣ REGISTRO SIMPLE DEL RESTO DE LOS MODELOS (¡Sin duplicar Song!)
admin.site.register(Game)
admin.site.register(BingoCard)
admin.site.register(BingoCardSong)