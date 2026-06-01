"""
Configuración de URL específica para la aplicación bingo.
"""
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views 

urlpatterns = [
    # Vista base / Raíz del proyecto
    path('', views.home, name='home'),

    # Rutas para el Login / Logout
    path('login/', views.login_view, name='login'), 
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # 🎯 Ruta de Registro
    path('registro/', views.signup_view, name='signup'),

    # Panel de Administración (HTML)
    path('panel-admin/agregar/', views.agregar_cancion, name='agregar_cancion'),
    path('panel-admin/subir-archivos/<int:song_id>/', views.subir_archivos, name='subir_archivos'),
    path('panel-admin/configurar/', views.configurar_sala, name='configurar_sala'),
    path('panel-admin/juego/', views.consola_juego, name='consola_juego'),
    path('panel-admin/canciones/', views.listar_canciones, name='listar_canciones'),
    path('panel-admin/canciones/eliminar/<int:song_id>/', views.eliminar_cancion, name='eliminar_cancion'),
    path('panel-admin/canciones/editar/<int:song_id>/', views.editar_cancion, name='editar_cancion'),

    # Rutas para el Jugador
    path('generar-carton/', views.generar_carton, name='generar_carton'),
    path('mi-carton/', views.ver_mi_carton, name='ver_mi_carton'),
    path('juego/verificar-marcado/', views.verificar_canciones_jugadas, name='verificar_canciones'),
    path('chat/obtener/', views.obtener_mensajes, name='obtener_mensajes'),
    path('toggle-chat/', views.toggle_chat, name='toggle_chat'),

    # Endpoints de la API REST (DRF)
    path('api/register/', views.register_user, name='register'),
    path('api/add-song/', views.add_song, name='add_song'),
    path('api/current-game/', views.current_game, name='current_game'),
    path('api/next-song/', views.next_song, name='next_song'),
    path('api/my-card/<int:user_id>/', views.my_card, name='my_card'),

    # Rutas de Recuperación de Contraseña
    path('reset_password/', 
         auth_views.PasswordResetView.as_view(template_name="registration/password_reset_form.html"), 
         name="reset_password"),
    path('reset_password_sent/', 
         auth_views.PasswordResetDoneView.as_view(template_name="registration/password_reset_done.html"), 
         name="password_reset_done"),
    path('reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(template_name="registration/password_reset_confirm.html"), 
         name="password_reset_confirm"),
    path('reset_password_complete/', 
         auth_views.PasswordResetCompleteView.as_view(template_name="registration/password_reset_complete.html"), 
         name="password_reset_complete"),
]