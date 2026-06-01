import random
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.db import IntegrityError

# Importación de modelos y formularios
from .models import Game, BingoCardSong, Song, BingoCard, GameHistory,ChatMessage
from .forms import SongForm

# Importaciones de Django Rest Framework (API)
from rest_framework.reverse import reverse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from .serializers import GameSerializer, BingoCardSongSerializer, SongSerializer

# Otras importaciones necesarias
import string
from datetime import datetime

# =====================================================================
# 🛡️ REGLAS DE SEGURIDAD
# =====================================================================
def es_administrador(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

# =====================================================================
# 🏠 VISTA PRINCIPAL (HOME)
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
# 🎛️ NUEVA CONSOLA DEL DIRECTOR (SEPARADA)
# =====================================================================

# 1. Pantalla de Configuración: Solo para crear la sala
@user_passes_test(es_administrador, login_url='login')
def configurar_sala(request):
    if request.method == 'POST':
        nombre_sala = request.POST.get('nombre_sala', 'Partida Principal')
        tamano_carton = int(request.POST.get('tamano_carton', 15))
        
        # Desactivar salas previas y crear la nueva
        Game.objects.update(active=False) 
        Game.objects.create(name=nombre_sala, card_size=tamano_carton, active=True)
        
        messages.success(request, f"Sala '{nombre_sala}' activada correctamente.")
        return redirect('consola_juego')
        
    return render(request, 'bingo/configurar_sala.html')

# 2. Pantalla de Juego: Solo para sacar canciones en vivo
@user_passes_test(es_administrador, login_url='login')
def consola_juego(request):
    game = Game.objects.filter(active=True).first()
    
    # Lógica para cantar una canción
    if request.method == 'POST':
        if game:
            cancion = game.play_random_song()
            if cancion:
                BingoCardSong.objects.filter(song=cancion).update(marked=True)
                messages.success(request, f"Lanzada: {cancion.nombre}")
            else:
                messages.warning(request, "¡No quedan más canciones!")
        return redirect('consola_juego')

    # Datos para la consola
    historial = []
    cancion_actual = None
    total_cartones = 0
    total_disponibles = Song.objects.filter(en_juego=True).count() # NUEVO

    if game:
        # Historial (invertido para que lo último aparezca arriba)
        historial = [record.song for record in game.history.select_related('song').order_by('-id')]
        if historial:
            cancion_actual = historial[0] # La última es la actual
            historial = historial[1:]     # El resto es el historial
            
        total_cartones = game.cards.count()

    return render(request, 'bingo/consola_juego.html', {
        'game': game,
        'cancion_actual': cancion_actual,
        'historial': historial,
        'total_cartones': total_cartones,
        'total_disponibles': total_disponibles, # PASAMOS EL NUEVO DATO
    })
# =====================================================================
# 🎵 GESTIÓN DE CANCIONES (HTML)
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
        messages.success(request, "Canción eliminada correctamente.")
    return redirect('listar_canciones')

@user_passes_test(es_administrador, login_url='login')
def editar_cancion(request, song_id):
    cancion = get_object_or_404(Song, id=song_id)
    if request.method == 'POST':
        form = SongForm(request.POST, instance=cancion)
        if form.is_valid():
            form.save()
            messages.success(request, "Canción actualizada con éxito.")
            return redirect('listar_canciones')
    else:
        form = SongForm(instance=cancion)
    return render(request, 'bingo/agregar_cancion.html', {'form': form})
# =====================================================================
# 🔐 SISTEMA DE REGISTRO E INICIO DE SESIÓN
# =====================================================================
def signup_view(request):
    if request.method == 'POST':
        u = request.POST.get('username', '').strip()
        p = request.POST.get('password', '').strip()
        
        if not u or not p:
            messages.error(request, 'Todos los campos son obligatorios.')
            return render(request, 'registration/signup.html')
            
        try:
            if User.objects.filter(username=u).exists():
                messages.error(request, 'Este nombre de usuario ya está registrado.')
                return render(request, 'registration/signup.html')
                
            user = User.objects.create_user(username=u, password=p)
            
            # Lo vinculamos automáticamente al grupo 'Jugadores'
            grupo_jugadores, _ = Group.objects.get_or_create(name='Jugadores')
            user.groups.add(grupo_jugadores)

            auth_login(request, user)
            messages.success(request, '¡Registro exitoso! Ya estás dentro del juego.')
            return redirect('generar_carton')
            
        except IntegrityError:
            messages.error(request, 'Error de base de datos al crear el usuario.')
        except Exception:
            messages.error(request, 'Ocurrió un error inesperado.')
            
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
# 🌐 ENDPOINTS DE LA API REST
# =====================================================================
@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request):
    return Response({
        'mensaje': '¡Bienvenido a la API de Music Bingo!',
        'juego_actual': reverse('current_game', request=request),
        'siguiente_cancion': reverse('next_song', request=request),
        'ver_mi_carton_ejemplo': reverse('my_card', args=[1], request=request).replace('/1/', '/{user_id}/')
    })

@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response({'error': 'Usuario y contraseña requeridos.'}, status=status.HTTP_400_BAD_REQUEST)
        
    if User.objects.filter(username=username).exists():
        return Response({'error': 'El nombre de usuario ya existe.'}, status=status.HTTP_400_BAD_REQUEST)
    
    user = User.objects.create_user(username=username, password=password)
    grupo_jugadores, _ = Group.objects.get_or_create(name='Jugadores')
    user.groups.add(grupo_jugadores)
    
    return Response({'message': 'Usuario registrado con éxito como Jugador.'}, status=status.HTTP_201_CREATED)

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
        cards = BingoCardSong.objects.filter(song=song)
        cards.update(marked=True)

    serializer = GameSerializer(game)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_game(request):
    game = Game.objects.filter(active=True).first()
    if not game:
        return Response({'message': 'No hay ninguna partida activa aún.'}, status=status.HTTP_200_OK)
    serializer = GameSerializer(game)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_card(request, user_id):
    if request.user.id != user_id and not request.user.is_staff:
        return Response({'error': 'No tienes permiso para ver el cartón de otro jugador.'}, status=status.HTTP_403_FORBIDDEN)

    songs = BingoCardSong.objects.filter(card__user__id=user_id)
    serializer = BingoCardSongSerializer(songs, many=True)
    return Response(serializer.data)

@login_required
def generar_carton(request):
    game = Game.objects.filter(active=True).first()
    
    if request.method == 'POST':
        if not game:
            messages.error(request, "No hay una partida activa en este momento.")
            return redirect('home')
        
        # 1. Validar canciones
        canciones_disponibles = list(Song.objects.filter(en_juego=True))
        if len(canciones_disponibles) < game.card_size:
            messages.error(request, "No hay suficientes canciones para llenar el cartón.")
            return redirect('home')
        
        # 2. Generar el código y guardarlo en una variable
        nuevo_codigo = generar_codigo_carton() 
        
        # 3. Crear el Cartón usando esa variable
        card = BingoCard.objects.create(
            user=request.user, 
            game=game, 
            codigo=nuevo_codigo 
        )
        
        # 4. Seleccionar y asignar las canciones
        seleccionadas = random.sample(canciones_disponibles, game.card_size)
        for s in seleccionadas:
            BingoCardSong.objects.create(card=card, song=s)
            
        # Ahora 'nuevo_codigo' sí existe y se puede mostrar en el mensaje
        messages.success(request, f"¡Tu cartón {nuevo_codigo} ha sido generado!")
        return redirect('ver_mi_carton')
        
    return render(request, 'bingo/generar_carton.html')

@login_required
def ver_mi_carton(request):
    game = Game.objects.filter(active=True).first()
    carton = BingoCard.objects.filter(user=request.user, game=game).first()
    
    # Asegúrate de que el nombre de la variable sea 'casillas'
    casillas = []
    if carton:
        casillas = carton.songs.all().select_related('song')
    
    return render(request, 'bingo/mi_carton.html', {
        'casillas': casillas, # <--- CAMBIO AQUÍ para que coincida con el for en tu HTML
    })

def generar_codigo_carton():
    # 4 letras aleatorias
    letras = ''.join(random.choices(string.ascii_uppercase, k=4))
    # 1 símbolo (asterisco o gato)
    simbolo = random.choice(['*', '#'])
    # Fecha de hoy en formato 8 números (YYYYMMDD)
    fecha = datetime.now().strftime('%Y%m%d')
    
    return f"{letras}{simbolo}{fecha}"

@login_required
def verificar_canciones_jugadas(request):
    game = Game.objects.filter(active=True).first()
    if not game:
        return JsonResponse({'canciones_jugadas': []})
    
    # Obtenemos los IDs de todas las canciones que ya han salido en esta partida
    # Historial de canciones ya marcadas como verdaderas en el juego
    jugadas = BingoCardSong.objects.filter(card__game=game, marked=True).values_list('song_id', flat=True).distinct()
    
    return JsonResponse({'canciones_jugadas': list(jugadas)})

@login_required
def enviar_mensaje(request):
    if request.method == 'POST':
        game = Game.objects.filter(active=True).first()
        
        # Validación de seguridad: no dejar enviar si chat_enabled es False
        if not game or not game.chat_enabled:
            return JsonResponse({'error': 'El chat está desactivado'}, status=403)
            
        content = request.POST.get('content', '').strip()
        if content:
            ChatMessage.objects.create(user=request.user, content=content, game=game)
            return JsonResponse({'status': 'ok'})
            
    return JsonResponse({'status': 'error'}, status=400)

def obtener_mensajes(request):
    game = Game.objects.filter(active=True).first()
    # Retornamos también el estado del chat para que el frontend sepa si bloquear el input
    chat_enabled = game.chat_enabled if game else False
    
    mensajes = ChatMessage.objects.filter(game=game).order_by('-timestamp')[:20]
    data = [{'user': m.user.username, 'content': m.content} for m in reversed(mensajes)]
    
    return JsonResponse({
        'mensajes': data,
        'chat_enabled': chat_enabled
    })

@user_passes_test(es_administrador, login_url='login')
def toggle_chat(request):
    game = Game.objects.filter(active=True).first()
    if game:
        game.chat_enabled = not game.chat_enabled
        game.save()
    return redirect('consola_juego') # Asegúrate de que esta URL exista