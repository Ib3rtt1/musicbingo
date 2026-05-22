import json
from django.core.management.base import BaseCommand
from bingo.models import Song

class Command(BaseCommand):
    help = 'Carga masiva de 100 canciones desde un archivo JSON'

    def handle(self, *args, **options):
        ruta_json = 'canciones.json'
        canciones_a_crear = []

        try:
            # Abrimos y leemos el archivo JSON
            with open(ruta_json, mode='r', encoding='utf-8') as archivo:
                datos = json.load(archivo)
                
                for item in datos:
                    # Creamos la instancia en memoria
                    nueva_cancion = Song(
                        numero=int(item['numero']),
                        nombre=str(item['nombre']).strip(),
                        artista=str(item['artista']).strip(),
                        fecha_publicacion=str(item['fecha_publicacion']).strip(),
                        en_juego=True  # Quedan listas para jugar inmediatamente
                    )
                    canciones_a_crear = canciones_a_crear + [nueva_cancion]

            # ⚡ BULK CREATE: Inserta las 100 canciones de un solo viaje SQL
            if canciones_a_crear:
                # 'ignore_conflicts=True' evita que el script falle si encuentra un número repetido
                Song.objects.bulk_create(canciones_a_crear, ignore_conflicts=True)
                self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se procesaron {len(canciones_a_crear)} canciones en la base de datos.'))
            
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'Error: No se encontró el archivo "{ruta_json}" en la raíz del proyecto.'))
        except KeyError as e:
            self.stdout.write(self.style.ERROR(f'Error de formato: Falta el campo obligatorio {e} en el JSON.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ocurrió un error inesperado: {e}'))