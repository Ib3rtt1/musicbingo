"""
Configuración de URL global para el proyecto musicbingo.
"""
from django.contrib import admin
from django.urls import path, include  # 👈 Importamos 'include'
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 🎯 LA MAGIA: Todo lo que llegue a la raíz (o cualquier subruta)
    # es redirigido automáticamente al urls.py de la aplicación 'bingo'
    path('', include('bingo.urls')), 
]

# Servidor de archivos multimedia en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)