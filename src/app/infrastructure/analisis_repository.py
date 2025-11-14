import psycopg2.extras
from typing import List, Dict, Any, Optional
from app.config.settings import settings

class AnalisisIARepository:
    def __init__(self, conn):
        self.conn = conn
        self.schema = settings.POSTGRES_SCHEMA

    def crear(self, fecha_inicio, fecha_fin, resumen, recomendaciones, modelo_usado):
        cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cursor.execute(f"""
            INSERT INTO {self.schema}.analisis_ia
            (fecha_inicio, fecha_fin, resumen, recomendaciones, modelo_usado)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING *
        """, (fecha_inicio, fecha_fin, resumen, recomendaciones, modelo_usado))

        row = cursor.fetchone()
        self.conn.commit()
        return row



    def listar(self) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(f"""
            SELECT *
            FROM {self.schema}.analisis_ia
            ORDER BY fecha_creacion DESC
        """)
        return cursor.fetchall()

    def obtener_por_id(self, analisis_id: int) -> Optional[Dict[str, Any]]:
        cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(f"""
            SELECT *
            FROM {self.schema}.analisis_ia
            WHERE id = %s
        """, (analisis_id,))
        return cursor.fetchone()
