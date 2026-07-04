from django import forms
from .models import Song, Game  # ✅ Un solo import


class SongForm(forms.ModelForm):
    class Meta:
        model = Song
        fields = ['numero', 'nombre', 'artista', 'fecha_publicacion']

        # ✅ Labels legibles para el usuario
        labels = {
            'numero': 'Numero de cancion',
            'nombre': 'Nombre de la cancion',
            'artista': 'Artista',
            'fecha_publicacion': 'Fecha de publicacion',
        }

        # ✅ Textos de ayuda debajo de cada campo
        help_texts = {
            'numero': 'Numero unico que identifica la cancion en el bombo.',
            'fecha_publicacion': 'No puede ser una fecha futura.',
        }

        widgets = {
            'fecha_publicacion': forms.DateInput(attrs={'type': 'date'}),
            # ✅ Placeholders para mejor UX
            'nombre': forms.TextInput(attrs={'placeholder': 'Ej: Bohemian Rhapsody'}),
            'artista': forms.TextInput(attrs={'placeholder': 'Ej: Queen'}),
        }

    # ✅ Validacion: numero debe ser positivo
    def clean_numero(self):
        numero = self.cleaned_data.get('numero')
        if numero is not None and numero <= 0:
            raise forms.ValidationError('El numero debe ser mayor que cero.')
        # Evitar duplicados al crear (no al editar la misma instancia)
        qs = Song.objects.filter(numero=numero)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(f'Ya existe una cancion con el numero {numero}.')
        return numero

    # ✅ Validacion: fecha no puede ser futura
    def clean_fecha_publicacion(self):
        from datetime import date
        fecha = self.cleaned_data.get('fecha_publicacion')
        if fecha and fecha > date.today():
            raise forms.ValidationError('La fecha de publicacion no puede ser futura.')
        return fecha


class GameConfigForm(forms.ModelForm):
    class Meta:
        model = Game
        fields = ['total_songs_limit']

        labels = {
            'total_songs_limit': 'Limite de canciones en la partida',
        }

        help_texts = {
            'total_songs_limit': 'Cuantas canciones se usaran en esta partida (entre 10 y 200).',
        }

        widgets = {
            'total_songs_limit': forms.NumberInput(attrs={'min': 10, 'max': 200}),
        }

    # ✅ Validacion de rango en el servidor (el min/max del HTML es solo visual)
    def clean_total_songs_limit(self):
        limite = self.cleaned_data.get('total_songs_limit')
        if limite is not None and not (10 <= limite <= 200):
            raise forms.ValidationError('El limite debe estar entre 10 y 200 canciones.')
        return limite