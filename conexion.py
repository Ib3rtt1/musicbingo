
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 1. Definir la URL de conexión (Connection String)
# Estructura: postgresql+psycopg://usuario:password@host:puerto/base_de_datos
DATABASE_URL = "postgresql+psycopg://usuario_bingo:mi_password_seguro@localhost:5432/bingomusic_db"

# 2. Crear el motor de conexión (Engine)
# echo=True nos permite ver en la terminal todo el SQL que se ejecuta por detrás
engine = create_engine(DATABASE_URL, echo=True)

# 3. Crear una fábrica de sesiones
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def probar_conexion():
    print("Intentando conectar a la base de datos en Docker...")
    
    # Abrimos una sesión que se cerrará automáticamente al salir del bloque 'with'
    with SessionLocal() as session:
        try:
            # Ejecutamos una consulta de prueba nativa
            resultado = session.execute(text("SELECT current_database(), version();"))
            db_nombre, db_version = resultado.fetchone()
            
            print("\n¡Conexión exitosa! 🎉")
            print(f"-> Conectado a la base de datos: {db_nombre}")
            print(f"-> Versión de Postgres: {db_version}\n")
            
        except Exception as e:
            print(f"\n❌ Error al conectar a la base de datos: {e}")

if __name__ == "__main__":
    probar_conexion()