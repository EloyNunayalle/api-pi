from datetime import date
import psycopg2.extras
from typing import List, Dict, Any
from app.config.settings import settings

class ResiduosRepository:
    def __init__(self, conn):
        self.conn = conn
        self.schema = settings.POSTGRES_SCHEMA

    def crear(self, dia, cantidad_kg, tipo_residuo_id) -> int:
        cursor = self.conn.cursor()
        cursor.execute(f"""
            INSERT INTO {self.schema}.registros_residuos
            (dia, cantidad_kg, tipo_residuo_id)
            VALUES (%s, %s, %s)
            RETURNING id
        """, (dia, cantidad_kg, tipo_residuo_id))

        residuo_id = cursor.fetchone()[0]
        self.conn.commit()
        return residuo_id
    
    def crear_lote(self, registros: list[dict]) -> int:
        """
        Inserta múltiples registros en registros_residuos.
        """
        cursor = self.conn.cursor()

        values = [
            (r["dia"], r["cantidad_kg"], r["tipo_residuo_id"])
            for r in registros
        ]

        cursor.executemany(
            f"""
            INSERT INTO {self.schema}.registros_residuos
            (dia, cantidad_kg, tipo_residuo_id)
            VALUES (%s, %s, %s)
            """
        , values)

        self.conn.commit()

        return len(values)
    
    def obtener_por_id(self, registro_id: int):
        cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cursor.execute(
            f"""
            SELECT 
                r.id,
                r.dia,
                r.cantidad_kg,
                r.tipo_residuo_id,
                t.nombre AS tipo_residuo,
                t.descripcion AS descripcion_tipo_residuo,
                r.fecha_creacion
            FROM {self.schema}.registros_residuos r
            JOIN {self.schema}.tipos_residuos t
                ON r.tipo_residuo_id = t.id
            WHERE r.id = %s
            """,
            (registro_id,)
        )

        return cursor.fetchone()



    def listar_por_rango(self, fecha_inicio, fecha_fin):
        cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cursor.execute(
            f"""
            SELECT 
                r.id,
                r.dia,
                r.cantidad_kg,
                r.tipo_residuo_id,
                t.nombre AS tipo_residuo,
                t.descripcion AS descripcion_tipo_residuo,
                r.fecha_creacion
            FROM {self.schema}.registros_residuos r
            JOIN {self.schema}.tipos_residuos t
                ON r.tipo_residuo_id = t.id
            WHERE r.dia BETWEEN %s AND %s
            ORDER BY r.dia ASC
            """,
            (fecha_inicio, fecha_fin)
        )

        return cursor.fetchall()
    
    def estadisticas_por_rango(self, fecha_inicio: date, fecha_fin: date):
        cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(f"""
            SELECT 
                tr.id AS tipo_id,
                tr.nombre AS tipo_residuo,
                tr.descripcion AS descripcion_tipo_residuo,

                COUNT(rr.id) AS cantidad_registros,
                SUM(rr.cantidad_kg) AS total_kg,
                AVG(rr.cantidad_kg) AS promedio_kg,
                MIN(rr.cantidad_kg) AS minimo_kg,
                MAX(rr.cantidad_kg) AS maximo_kg

            FROM {self.schema}.registros_residuos rr
            JOIN {self.schema}.tipos_residuos tr
                ON tr.id = rr.tipo_residuo_id

            WHERE rr.dia BETWEEN %s AND %s
            GROUP BY tr.id, tr.nombre, tr.descripcion
            ORDER BY total_kg DESC;
        """, (fecha_inicio, fecha_fin))

        return cursor.fetchall()



    

