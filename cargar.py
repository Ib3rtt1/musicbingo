import os
import json
import django

# 1. Le avisamos a Python cuál es el archivo de configuración de tu proyecto
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'musicbingo.settings')
django.setup()

# 2. Ahora que Django está despierto, importamos tu modelo de canciones
from bingo.models import Song

def cargar_desde_json():
    ruta_json = 'canciones.json'
    canciones_a_crear = []

    try:
        # Leemos el archivo plano
        with open(ruta_json, mode='r', encoding='utf-8') as archivo:
            datos = json.load(archivo)
            
            for item in datos:
                nueva_cancion = Song(
                    numero=int(item['numero']),
                    nombre=str(item['nombre']).strip(),
                    artista=str(item['artista']).strip(),
                    fecha_publicacion=str(item['fecha_publicacion']).strip(),
                    en_juego=True
                )
                canciones_a_crear = canciones_a_crear + [nueva_cancion]
                
        if canciones_a_crear:
            # Inserta todo masivamente ignorando si el #1 o #2 ya existen en Postgres
            Song.objects.bulk_create(canciones_a_crear, ignore_conflicts=True)
            
            print("==========================================================")
            print(f" ¡ÉXITO! Script ejecutado correctamente.")
            print(f" Total de canciones actuales en la base de datos: {Song.objects.count()}")
            print("==========================================================")
            
    except FileNotFoundError:
        print(f"❌ Error: No encontramos el archivo '{ruta_json}' en esta carpeta.")
        print("Asegúrate de que esté al lado de manage.py.")
    except Exception as e:
        print(f"❌ Ocurrió un error inesperado: {e}")

if __name__ == '__main__':
    cargar_desde_json()