from django import forms
from .models import Song

class SongForm(forms.ModelForm):
    class Meta:
        model = Song
        # Ahora sí coinciden exactamente con tu modelo en español:
        fields = ['numero', 'nombre', 'artista', 'fecha_publicacion' ]
        
        # Opcional: Esto hace que el calendario se despliegue visualmente de forma nativa en el HTML
        widgets = {
            'fecha_publicacion': forms.DateInput(attrs={'type': 'date'}),
        }