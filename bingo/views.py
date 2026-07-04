import random
import string
from datetime import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.db import IntegrityError
from django.template.loader import render_to_string

from .models import Game, BingoCardSong, Song, BingoCard, GameHistory, ChatMessage
from .forms import SongForm

from rest_framework.reverse import reverse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from .serializers import GameSerializer, BingoCardSongSerializer, SongSerializer


# =====================================================================
# SEGURIDAD Y UTILIDADES
# =====================================================================

def es_administrador(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


def generar_codigo_carton():
    letras = ''.join(random.choices(string.ascii_uppercase, k=4))
    simbolo = random.choice(['*', '#'])
    fecha = datetime.now().strftime('%Y%m%d')
    return f"{letras}{simbolo}{fecha}"


def _generar_codigo_unico():
    for _ in range(10):
        codigo = generar_codigo_carton()
        if not BingoCard.objects.filter(codigo=codigo).exists():
            return codigo
    raise RuntimeError("No se pudo generar un codigo unico tras 10 intentos.")


def calcular_ganadores(game, cantadas_ids_set):
    ganadores = []
    cartones = game.cards.prefetch_related('songs').all()
    for carton in cartones:
        songs_in_card = [s.song_id for s in carton.songs.all()]
        if songs_in_card and all(s_id in cantadas_ids_set for s_id in songs_in_card):
            ganadores.append(carton)
    return ganadores


# =====================================================================
# VISTA PRINCIPAL (HOME)
# =====================================================================

def home(request):
    juegos_activos = Game.objects.filter(active=True)
    game = juegos_activos.first()
    canciones_salidas = []

    if game:
        canciones_salidas = [record.song for record in game.history.select_related('song')]

    context = {
        'juegos': juegos_activos,
        'game': game,
        'canciones_salidas': canciones_salidas,
    }
    return render(request, 'bingo/home.html', context)


# =====================================================================
# CONSOLA DEL DIRECTOR
# =====================================================================

@user_passes_test(es_administrador, login_url='login')
def configurar_sala(request):
    if request.method == 'POST':
        nombre_sala = request.POST.get('nombre_sala', 'Partida Principal')
        tamano_carton = int(request.POST.get('tamano_carton', 15))
        limite_canciones = int(request.POST.get('limite_canciones', 90))

        Game.objects.update(active=False)

        nuevo_juego = Game.objects.create(
            name=nombre_sala,
            card_size=tamano_carton,
            total_songs_limit=limite_canciones,
            active=True
        )

        canciones_seleccionadas = Song.objects.filter(en_juego=True).order_by('?')[:limite_canciones]
        nuevo_juego.songs_in_game.set(canciones_seleccionadas)

        messages.success(request, f"Sala '{nombre_sala}' iniciada con {canciones_seleccionadas.count()} canciones.")
        return redirect('consola_juego')

    return render(request, 'bingo/configurar_sala.html')


@user_passes_test(es_administrador, login_url='login')
def consola_juego(request):
    game = Game.objects.filter(active=True).first()

    if request.method == 'POST':
        if game:
            cancion = game.play_random_song()
            if cancion:
                # CORRECCIÓN: Filtrar por song Y por game (a través de la tarjeta)
                BingoCardSong.objects.filter(
                    song=cancion, 
                    card__game=game
                ).update(marked=True)

                # Notificar vía WebSocket
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    f'bingo_{game.id}',
                    {
                        'type': 'nueva_cancion',
                        'song_id': cancion.id,
                        'song_nombre': cancion.nombre,
                        'song_artista': cancion.artista,
                    }
                )
                messages.success(request, f"Se ha cantado: {cancion.nombre}")
            else:
                messages.warning(request, "¡La tómbola está vacía!")
        
        return redirect('consola_juego')

    # Datos para el GET
    historial, cancion_actual, ganadores = [], None, []
    
    if game:
        records = game.history.select_related('song').order_by('-id')
        historial_completo = [r.song for r in records]

        if historial_completo:
            cancion_actual = historial_completo[0]
            historial = historial_completo[1:]

        cantadas_ids = {s.id for s in historial_completo}
        ganadores = calcular_ganadores(game, cantadas_ids)

    return render(request, 'bingo/consola_juego.html', {
        'game': game,
        'cancion_actual': cancion_actual,
        'historial': historial,
        'total_cartones': game.cards.count() if game else 0,
        'ganadores': ganadores,
    })

@user_passes_test(es_administrador, login_url='login')
def actualizar_consola(request):
    game = Game.objects.filter(active=True).first()

    if not game:
        return JsonResponse({'html': '<p>No hay juego activo.</p>'})

    records = game.history.select_related('song').order_by('-id')
    historial_completo = [r.song for r in records]
    cancion_actual = historial_completo[0] if historial_completo else None
    historial = historial_completo[1:] if historial_completo else []

    cantadas_ids = {s.id for s in historial_completo}
    ganadores = calcular_ganadores(game, cantadas_ids)

    html = render_to_string('bingo/partials/consola_datos.html', {
        'game': game,
        'cancion_actual': cancion_actual,
        'historial': historial,
        'ganadores': ganadores,
        'total_cartones': game.cards.count(),
    })

    return JsonResponse({'html': html})


@user_passes_test(es_administrador, login_url='login')
def toggle_chat(request):
    game = Game.objects.filter(active=True).first()
    if game:
        game.chat_enabled = not game.chat_enabled
        game.save()
    return redirect('consola_juego')


# =====================================================================
# GESTION DE CANCIONES
# =====================================================================

@user_passes_test(es_administrador, login_url='login')
def agregar_cancion(request):
    if request.method == 'POST':
        form = SongForm(request.POST)
        if form.is_valid():
            nueva_cancion = form.save()
            return redirect('subir_archivos', song_id=nueva_cancion.id)
    else:
        form = SongForm()
    return render(request, 'bingo/agregar_cancion.html', {'form': form})


@user_passes_test(es_administrador, login_url='login')
def subir_archivos(request, song_id):
    cancion = get_object_or_404(Song, id=song_id)

    if request.method == 'POST':
        if 'archivo_mp4' in request.FILES:
            cancion.archivo_mp4 = request.FILES['archivo_mp4']
        if 'imagen' in request.FILES:
            cancion.imagen = request.FILES['imagen']
        cancion.save()
        return redirect('home')

    return render(request, 'bingo/subir_archivos.html', {'cancion': cancion})


@user_passes_test(es_administrador, login_url='login')
def listar_canciones(request):
    canciones = Song.objects.all().order_by('nombre')
    return render(request, 'bingo/listar_canciones.html', {'canciones': canciones})


@user_passes_test(es_administrador, login_url='login')
def eliminar_cancion(request, song_id):
    cancion = get_object_or_404(Song, id=song_id)
    if request.method == 'POST':
        cancion.delete()
        messages.success(request, "Cancion eliminada correctamente.")
    return redirect('listar_canciones')


@user_passes_test(es_administrador, login_url='login')
def editar_cancion(request, song_id):
    cancion = get_object_or_404(Song, id=song_id)
    if request.method == 'POST':
        form = SongForm(request.POST, instance=cancion)
        if form.is_valid():
            form.save()
            messages.success(request, "Cancion actualizada con exito.")
            return redirect('listar_canciones')
    else:
        form = SongForm(instance=cancion)
    return render(request, 'bingo/agregar_cancion.html', {'form': form})


# =====================================================================
# REGISTRO E INICIO DE SESION
# =====================================================================

def signup_view(request):
    if request.method == 'POST':
        u = request.POST.get('username', '').strip()
        p = request.POST.get('password', '').strip()

        if not u or not p:
            messages.error(request, 'Todos los campos son obligatorios.')
            return render(request, 'registration/signup.html')

        if User.objects.filter(username=u).exists():
            messages.error(request, 'Este nombre de usuario ya esta registrado.')
            return render(request, 'registration/signup.html')

        try:
            user = User.objects.create_user(username=u, password=p)
            grupo_jugadores, _ = Group.objects.get_or_create(name='Jugadores')
            user.groups.add(grupo_jugadores)
            auth_login(request, user)
            messages.success(request, 'Registro exitoso! Ya estas dentro del juego.')
            return redirect('generar_carton')
        except IntegrityError:
            messages.error(request, 'Error de base de datos al crear el usuario.')
        except Exception:
            messages.error(request, 'Ocurrio un error inesperado.')

    return render(request, 'registration/signup.html')


def login_view(request):
    if request.method == 'POST':
        u = request.POST.get('username', '').strip()
        p = request.POST.get('password', '').strip()

        user = authenticate(request, username=u, password=p)

        if user is not None:
            auth_login(request, user)
            request.session.modify = True
            return redirect('ver_mi_carton')
        else:
            messages.error(request, 'Por favor, introduzca un nombre de usuario y clave correctos.')

    return render(request, 'registration/login.html')


# =====================================================================
# CARTONES
# =====================================================================

@login_required
def generar_carton(request):
    game = Game.objects.filter(active=True).first()

    if request.method == 'POST':
        if not game:
            messages.error(request, "No hay una partida activa en este momento.")
            return redirect('home')

        if BingoCard.objects.filter(user=request.user, game=game).exists():
            messages.warning(request, "Ya tienes un carton para esta partida.")
            return redirect('ver_mi_carton')

        ids_partida = list(game.songs_in_game.values_list('id', flat=True))

        if len(ids_partida) < game.card_size:
            messages.error(request, "No hay suficientes canciones en esta partida para llenar el carton.")
            return redirect('home')

        nuevo_codigo = _generar_codigo_unico()

        card = BingoCard.objects.create(
            user=request.user,
            game=game,
            codigo=nuevo_codigo
        )

        ids_seleccionados = random.sample(ids_partida, game.card_size)

        BingoCardSong.objects.bulk_create([
            BingoCardSong(card=card, song_id=s_id)
            for s_id in ids_seleccionados
        ])

        messages.success(request, f"Tu carton {nuevo_codigo} ha sido generado con canciones de esta partida!")
        return redirect('ver_mi_carton')

    return render(request, 'bingo/generar_carton.html')


@login_required
def ver_mi_carton(request):
    game = Game.objects.filter(active=True).first()

    if not game:
        return render(request, 'bingo/mi_carton.html', {'casillas': []})

    carton = BingoCard.objects.filter(user=request.user, game=game).first()
    casillas = carton.songs.select_related('song').all() if carton else []

    return render(request, 'bingo/mi_carton.html', {'casillas': casillas})


# =====================================================================
# CONTROL DE CARTONES
# =====================================================================

@user_passes_test(es_administrador, login_url='login')
def vista_control_cartones(request, game_id):
    game = get_object_or_404(Game, id=game_id)

    canciones_cantadas_ids = set(game.history.values_list('song_id', flat=True))
    cartones = game.cards.prefetch_related('songs').all()

    return render(request, 'bingo/control_cartones.html', {
        'game': game,
        'cartones': cartones,
        'canciones_cantadas': canciones_cantadas_ids,
    })


# =====================================================================
# CHAT
# =====================================================================

@login_required
def enviar_mensaje(request):
    if request.method == 'POST':
        game = Game.objects.filter(active=True).first()

        if not game or not game.chat_enabled:
            return JsonResponse({'error': 'El chat esta desactivado'}, status=403)

        content = request.POST.get('content', '').strip()
        if content:
            ChatMessage.objects.create(user=request.user, content=content, game=game)
            return JsonResponse({'status': 'ok'})

    return JsonResponse({'status': 'error'}, status=400)

@login_required
def obtener_mensajes(request):
    game = Game.objects.filter(active=True).first()
    chat_enabled = game.chat_enabled if game else False

    mensajes = ChatMessage.objects.filter(game=game).order_by('-timestamp')[:20]
    data = [{'user': m.user.username, 'content': m.content} for m in reversed(list(mensajes))]

    return JsonResponse({
        'mensajes': data,
        'chat_enabled': chat_enabled,
    })


# =====================================================================
# API REST
# =====================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request):
    return Response({
        'mensaje': 'Bienvenido a la API de Music Bingo!',
        'juego_actual': reverse('current_game', request=request),
        'siguiente_cancion': reverse('next_song', request=request),
        'ver_mi_carton_ejemplo': reverse('my_card', args=[1], request=request).replace('/1/', '/{user_id}/'),
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response({'error': 'Usuario y contrasena requeridos.'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=username).exists():
        return Response({'error': 'El nombre de usuario ya existe.'}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(username=username, password=password)
    grupo_jugadores, _ = Group.objects.get_or_create(name='Jugadores')
    user.groups.add(grupo_jugadores)

    return Response({'message': 'Usuario registrado con exito como Jugador.'}, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_song(request):
    es_creador = request.user.groups.filter(name='Creadores').exists()
    if not es_creador and not request.user.is_staff:
        return Response({'error': 'No tienes permisos para agregar canciones.'}, status=status.HTTP_403_FORBIDDEN)

    serializer = SongSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def next_song(request):
    es_director = request.user.groups.filter(name='Directores').exists()
    if not es_director and not request.user.is_staff:
        return Response({'error': 'No tienes permisos para manejar la consola.'}, status=status.HTTP_403_FORBIDDEN)

    game = Game.objects.filter(active=True).first()
    if not game:
        return Response({'error': 'No hay ninguna partida activa.'}, status=status.HTTP_404_NOT_FOUND)

    song = game.play_random_song()
    if song:
        BingoCardSong.objects.filter(song=song).update(marked=True)

    serializer = GameSerializer(game)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_game(request):
    game = Game.objects.filter(active=True).first()
    if not game:
        return Response({'message': 'No hay ninguna partida activa aun.'}, status=status.HTTP_200_OK)
    serializer = GameSerializer(game)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_card(request, user_id):
    if request.user.id != user_id and not request.user.is_staff:
        return Response({'error': 'No tienes permiso para ver el carton de otro jugador.'}, status=status.HTTP_403_FORBIDDEN)

    songs = BingoCardSong.objects.filter(card__user__id=user_id)
    serializer = BingoCardSongSerializer(songs, many=True)
    return Response(serializer.data)


# =====================================================================
# VERIFICACION DE CANCIONES JUGADAS
# =====================================================================

@login_required
def verificar_canciones_jugadas(request):
    game = Game.objects.filter(active=True).first()
    if not game:
        return JsonResponse({'canciones_jugadas': []})

    jugadas = list(game.history.values_list('song_id', flat=True).distinct())
    return JsonResponse({'canciones_jugadas': jugadas})
