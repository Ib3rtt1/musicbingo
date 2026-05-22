from rest_framework.reverse import reverse
from django.contrib.auth.models import User, Group
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.decorators import login_required

from .models import Game, BingoCardSong, Song, BingoCard
from .serializers import GameSerializer, BingoCardSongSerializer, SongSerializer

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from .forms import SongForm

import random
from django.contrib import messages
# 🔥 Importamos la función de login interna de Django para el inicio automático
from django.contrib.auth import login as auth_login  

from django.contrib.auth.forms import UserCreationForm # El formulario nativo y seguro de Django
from django.db import IntegrityError
from django.contrib.auth import authenticate, login

# 🛡️ REGLA DE SEGURIDAD: Solo Administradores, Superusuarios o Staff pueden gestionar canciones en HTML
def es_administrador(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


# 1️⃣ PASO 1 (HTML): AGREGAR SÓLO LOS DATOS BÁSICOS DE LA CANCIÓN
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


# 2️⃣ PASO 2 (HTML): ADJUNTAR EL MP4 Y LA IMAGEN MÁS TARDE
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


# 🏠 VISTA PARA CARGAR EL FRONTEND DE LA PÁGINA
def home(request):
    juegos_activos = Game.objects.filter(active=True)
    context = {
        'juegos': juegos_activos,
    }
    return render(request, 'bingo/home.html', context)


# =====================================================================
# 🌐 ENDPOINTS DE LA API REST (DJANGO REST FRAMEWORK)
# =====================================================================

# 🗺️ ÍNDICE DE LA API
@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request):
    return Response({
        'mensaje': '¡Bienvenido a la API de Music Bingo!',
        'juego_actual': reverse('current_game', request=request),
        'siguiente_cancion': reverse('next_song', request=request),
        'ver_mi_carton_ejemplo': reverse('my_card', args=[1], request=request).replace('/1/', '/{user_id}/')
    })


# 🎯 INTERFAZ DE REGISTRO WEB CORREGIDA (Con Login Automático y Redirección al Cartón)
def registro_web(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        # Validamos que no envíen campos vacíos
        if not username or not password:
            messages.error(request, 'Por favor, completa todos los campos.')
            return render(request, 'registration/signup.html')
            
        # Validamos si el nombre de jugador ya está tomado
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Este nombre de usuario ya está registrado. Elige otro.')
            return render(request, 'registration/signup.html')
        
        try:
            # 1. Creamos el usuario en PostgreSQL de manera segura (con hash)
            user = User.objects.create_user(username=username, password=password)
            
            # 2. Lo vinculamos automáticamente al grupo 'Jugadores'
            grupo_jugadores, _ = Group.objects.get_or_create(name='Jugadores')
            user.groups.add(grupo_jugadores)
            
            # 3. 🔥 ¡MAGIA! Iniciamos su sesión web inmediatamente sin pedir credenciales de nuevo
            auth_login(request, user)
            
            # 4. Lo enviamos directo a que obtenga su cartón automáticamente
            messages.success(request, '¡Registro exitoso! Ya estás dentro del juego.')
            return redirect('generar_carton')
            
        except Exception as e:
            messages.error(request, 'Hubo un error al registrar tu cuenta. Inténtalo de nuevo.')
            return render(request, 'registration/signup.html')
            
    return render(request, 'registration/signup.html')


# 📝 ENDPOINT REST DE REGISTRO (Para Postman, apps móviles o fetch con JSON)
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


# 🎵 API PARA AGREGAR CANCIONES
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


# 🕹️ CONTROL DE CONSOLA (Siguiente canción aleatoria via API)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def next_song(request):
    es_director = request.user.groups.filter(name='Directores').exists()
    if not es_director and not request.user.is_staff:
        return Response({'error': 'No tienes permisos para manejar la consola.'}, status=status.HTTP_403_FORBIDDEN)

    game = Game.objects.first()
    if not game:
        return Response({'error': 'No hay ninguna partida activa.'}, status=status.HTTP_404_NOT_FOUND)
        
    song = game.play_random_song()
    cards = BingoCardSong.objects.filter(song=song)
    cards.update(marked=True)

    serializer = GameSerializer(game)
    return Response(serializer.data)


# 👁️ VER ESTADO DEL JUEGO ACTUAL
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_game(request):
    game = Game.objects.first()
    if not game:
        return Response({'message': 'No hay ninguna partida creada aún.'}, status=status.HTTP_200_OK)
    serializer = GameSerializer(game)
    return Response(serializer.data)


# 🎴 VER EL CARTÓN PROPIO DEL JUGADOR LOGUEADO
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_card(request, user_id):
    if request.user.id != user_id and not request.user.is_staff:
        return Response({'error': 'No tienes permiso para ver el cartón de otro jugador.'}, status=status.HTTP_403_FORBIDDEN)

    songs = BingoCardSong.objects.filter(card__user__id=user_id)
    serializer = BingoCardSongSerializer(songs, many=True)
    return Response(serializer.data)


# 🕹️ CONTROL DE CONSOLA EN HTML (Siguiente canción aleatoria para el Director)
@user_passes_test(es_administrador, login_url='login')
def consola_director(request):
    game = Game.objects.first()
    if not game:
        game = Game.objects.create(name="Partida Principal")
    
    if request.method == 'POST':
        cancion_ganadora = game.play_random_song()
        
        if cancion_ganadora:
            cards = BingoCardSong.objects.filter(song=cancion_ganadora)
            cards.update(marked=True)
            
        return redirect('consola_director')

    canciones_disponibles = Song.objects.filter(en_juego=True).count()
    
    return render(request, 'bingo/consola.html', {
        'game': game,
        'canciones_disponibles': canciones_disponibles
    })


# =====================================================================
# 🎟️ VISTAS PARA LOS JUGADORES (GENERAR Y VER CARTÓN)
# =====================================================================

@login_required(login_url='login')
def generar_carton(request):
    game = Game.objects.first()
    if not game:
        game = Game.objects.create(name="Partida Principal")

    carton_existente = BingoCard.objects.filter(user=request.user, game=game).first()
    if carton_existente:
        return redirect('ver_mi_carton')

    canciones_disponibles = list(Song.objects.filter(en_juego=True))
    
    if len(canciones_disponibles) < 15:
        messages.error(request, f"Faltan {15 - len(canciones_disponibles)} canciones en la base de datos para jugar.")
        return redirect('home')

    canciones_elegidas = random.sample(canciones_disponibles, 15)
    nuevo_carton = BingoCard.objects.create(user=request.user, game=game)

    for cancion in canciones_elegidas:
        BingoCardSong.objects.create(card=nuevo_carton, song=cancion)

    return redirect('ver_mi_carton')


@login_required(login_url='login')
def ver_mi_carton(request):
    game = Game.objects.first()
    carton = BingoCard.objects.filter(user=request.user, game=game).first()
    
    if not carton:
        return redirect('home')

    casillas = BingoCardSong.objects.filter(card=carton)
    
    return render(request, 'bingo/mi_carton.html', {'casillas': casillas})

# =====================================================================
# 🎯 INTERFAZ DE REGISTRO WEB (Con Login Automático y Redirección al Cartón)
# =====================================================================
def signup_view(request):
    if request.method == 'POST':
        u = request.POST.get('username', '').strip()
        p = request.POST.get('password', '').strip()
        
        # 1. Validación de campos vacíos
        if not u or not p:
            print("❌ ERROR: Nombre de usuario o contraseña vacíos.")  # Ver en consola
            messages.error(request, 'Todos los campos son obligatorios.')
            return render(request, 'registration/signup.html')
            
        try:
            # 2. Intentar crear el usuario de forma segura
            if User.objects.filter(username=u).exists():
                print(f"❌ ERROR: El usuario '{u}' ya existe en PostgreSQL.")
                messages.error(request, 'Este nombre de usuario ya está registrado.')
                return render(request, 'registration/signup.html')
                
            user = User.objects.create_user(username=u, password=p)
            print(f"✅ ÉXITO: Usuario '{u}' creado correctamente en la base de datos.")
            
            # Autenticar automáticamente al jugador
            login(request, user)
            return redirect('generar_carton')
            
        except IntegrityError as e:
            print(f"❌ ERROR DE INTEGRIDAD BASE DE DATOS: {e}")
            messages.error(request, 'Error de base de datos al crear el usuario.')
        except Exception as e:
            print(f"❌ ERROR INESPERADO: {e}")
            messages.error(request, 'Ocurrió un error inesperado.')
            
    return render(request, 'registration/signup.html')

def login_view(request):
    if request.method == 'POST':
        u = request.POST.get('username', '').strip()
        p = request.POST.get('password', '').strip()
        
        # Authenticate verifica la clave contra el hash encriptado de Postgres
        user = authenticate(request, username=u, password=p)
        
        if user is not None:
            login(request, user)
            # Forzamos a que la sesión se guarde limpiamente
            request.session.modify = True 
            return redirect('mi_carton') # O la vista de tu juego
        else:
            messages.error(request, 'Por favor, introduzca un nombre de usuario y clave correctos.')
            
    return render(request, 'registration/login.html')