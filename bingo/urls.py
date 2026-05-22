"""
Configuración de URL específica para la aplicación bingo.
"""
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views  # 👈 Importa las vistas locales de la app

urlpatterns = [
    # Vista base / Raíz del proyecto
    path('', views.home, name='home'),

    # Rutas para el Login / Logout
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Panel de Administración (HTML)
    path('panel-admin/agregar/', views.agregar_cancion, name='agregar_cancion'),
    path('panel-admin/subir-archivos/<int:song_id>/', views.subir_archivos, name='subir_archivos'),
    path('panel-admin/consola/', views.consola_director, name='consola_director'),

    # Rutas para el Jugador
    path('generar-carton/', views.generar_carton, name='generar_carton'),
    path('mi-carton/', views.ver_mi_carton, name='ver_mi_carton'),

    # Endpoints de la API REST (DRF)
    path('api/register/', views.register_user, name='register'),
    path('api/add-song/', views.add_song, name='add_song'),
    path('api/current-game/', views.current_game, name='current_game'),
    path('api/next-song/', views.next_song, name='next_song'),
    path('api/my-card/<int:user_id>/', views.my_card, name='my_card'),

    # 🎯 Esta es la ruta que tu HTML de login usará en el botón verde
    path('registro/', views.registro_web, name='signup'),

    # ⚡ Tu endpoint de API sigue intacto para integraciones móviles o fetch
    path('api/register/', views.register_user, name='register'),
]

