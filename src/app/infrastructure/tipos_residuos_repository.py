import psycopg2.extras
from typing import List, Dict, Any, Optional
from app.config.settings import settings

class TiposResiduosRepository:
    def __init__(self, conn):
        self.conn = conn
        self.schema = settings.POSTGRES_SCHEMA

    def crear(self, nombre: str, descripcion: str | None = None) -> int:
        cursor = self.conn.cursor()
        cursor.execute(f"""
            INSERT INTO {self.schema}.tipos_residuos (nombre, descripcion)
            VALUES (%s, %s)
            RETURNING id
        """, (nombre, descripcion))

        new_id = cursor.fetchone()[0]
        self.conn.commit()
        return new_id

    def listar(self) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(f"""
            SELECT *
            FROM {self.schema}.tipos_residuos
            ORDER BY id ASC
        """)
        return cursor.fetchall()
    
    def obtener_por_id(self, tipo_id: int) -> Optional[Dict[str, Any]]:
        cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(f"""
            SELECT *
            FROM {self.schema}.tipos_residuos
            WHERE id = %s
            LIMIT 1
        """, (tipo_id,))
        result = cursor.fetchone()
        return result 
    

