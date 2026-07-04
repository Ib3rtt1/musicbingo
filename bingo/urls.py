from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [

    # =========================================================
    # Publica
    # =========================================================
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('registro/', views.signup_view, name='signup'),

    # =========================================================
    # Jugador (requieren login — el decorador esta en views.py)
    # =========================================================
    path('generar-carton/', views.generar_carton, name='generar_carton'),
    path('mi-carton/', views.ver_mi_carton, name='ver_mi_carton'),
    path('juego/verificar-marcado/', views.verificar_canciones_jugadas, name='verificar_canciones'),

    # =========================================================
    # Chat (requieren login — el decorador esta en views.py)
    # =========================================================
    path('chat/enviar/', views.enviar_mensaje, name='enviar_mensaje'),   # ✅ faltaba
    path('chat/obtener/', views.obtener_mensajes, name='obtener_mensajes'),

    # =========================================================
    # Panel admin (requieren es_administrador — decorator en views.py)
    # =========================================================
    path('panel-admin/configurar/', views.configurar_sala, name='configurar_sala'),
    path('panel-admin/juego/', views.consola_juego, name='consola_juego'),
    path('panel-admin/actualizar-consola/', views.actualizar_consola, name='actualizar_consola'),
    path('panel-admin/toggle-chat/', views.toggle_chat, name='toggle_chat'),
    path('panel-admin/agregar/', views.agregar_cancion, name='agregar_cancion'),
    path('panel-admin/subir-archivos/<int:song_id>/', views.subir_archivos, name='subir_archivos'),
    path('panel-admin/canciones/', views.listar_canciones, name='listar_canciones'),
    path('panel-admin/canciones/eliminar/<int:song_id>/', views.eliminar_cancion, name='eliminar_cancion'),
    path('panel-admin/canciones/editar/<int:song_id>/', views.editar_cancion, name='editar_cancion'),
    path('panel-admin/control-cartones/<int:game_id>/', views.vista_control_cartones, name='control_cartones'),

    # =========================================================
    # API REST (autenticacion manejada por DRF en views.py)
    # =========================================================
    path('api/v1/register/', views.register_user, name='register'),
    path('api/v1/add-song/', views.add_song, name='add_song'),
    path('api/v1/current-game/', views.current_game, name='current_game'),
    path('api/v1/next-song/', views.next_song, name='next_song'),
    path('api/v1/my-card/<int:user_id>/', views.my_card, name='my_card'),

    # =========================================================
    # Recuperacion de contrasena
    # =========================================================
    path('reset_password/',
         auth_views.PasswordResetView.as_view(template_name="registration/password_reset_form.html"),
         name="reset_password"),
    path('reset_password_sent/',
         auth_views.PasswordResetDoneView.as_view(template_name="registration/password_reset_done.html"),
         name="password_reset_done"),
    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name="registration/password_reset_confirm.html"),
         name="reset_password_confirm"),
    path('reset_password_complete/',
         auth_views.PasswordResetCompleteView.as_view(template_name="registration/password_reset_complete.html"),
         name="password_reset_complete"),
]