from django import forms
from .models import Song
from .models import Game 

class SongForm(forms.ModelForm):
    class Meta:
        model = Song
        # Ahora sí coinciden exactamente con tu modelo en español:
        fields = ['numero', 'nombre', 'artista', 'fecha_publicacion' ]
        
        # Opcional: Esto hace que el calendario se despliegue visualmente de forma nativa en el HTML
        widgets = {
            'fecha_publicacion': forms.DateInput(attrs={'type': 'date'}),
        }

def editar_cancion(request, song_id):
    cancion = get_object_or_404(Song, id=song_id)
    if request.method == 'POST':
        form = SongForm(request.POST, instance=cancion)
        if form.is_valid():
            form.save()
            return redirect('listar_canciones')
    else:
        form = SongForm(instance=cancion)
    return render(request, 'bingo/agregar_cancion.html', {'form': form})



class GameConfigForm(forms.ModelForm):
    class Meta:
        model = Game
        fields = ['total_songs_limit'] # El admin solo verá este campo