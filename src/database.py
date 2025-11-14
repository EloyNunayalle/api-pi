import psycopg2
from app.config.settings import settings

def _init_tables(conn):
    cursor = conn.cursor()

    # Crear schema si no existe
    cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {settings.POSTGRES_SCHEMA}")
    cursor.execute(f"SET search_path TO {settings.POSTGRES_SCHEMA}")

    # ============================
    # 1. Tipos de residuos
    # ============================
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {settings.POSTGRES_SCHEMA}.tipos_residuos (
            id SERIAL PRIMARY KEY,
            nombre VARCHAR(50) NOT NULL,
            descripcion TEXT
        );
    """)

    # ============================
    # 2. Registros de residuos
    # ============================
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {settings.POSTGRES_SCHEMA}.registros_residuos (
            id SERIAL PRIMARY KEY,
            dia DATE NOT NULL,
            cantidad_kg DECIMAL(10,2) NOT NULL,

            tipo_residuo_id INT NOT NULL 
                REFERENCES {settings.POSTGRES_SCHEMA}.tipos_residuos(id)
                ON DELETE CASCADE,

            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # ============================
    # 3. Análisis generados por IA
    # ============================
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {settings.POSTGRES_SCHEMA}.analisis_ia (
            id SERIAL PRIMARY KEY,

            fecha_inicio DATE NOT NULL,
            fecha_fin DATE NOT NULL,

            resumen TEXT,
            recomendaciones TEXT,
            modelo_usado VARCHAR(100),

            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()


def get_db():
    conn = psycopg2.connect(
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        database=settings.POSTGRES_DB,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD
    )
    conn.autocommit = False

    _init_tables(conn)

    try:
        yield conn
    finally:
        conn.close()
