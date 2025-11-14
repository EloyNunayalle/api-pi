import logging
from datetime import date
from typing import List
import io
from openai import AzureOpenAI

from app.config.settings import settings
from app.infrastructure.tipos_residuos_repository import TiposResiduosRepository
from app.infrastructure.residuos_repository import ResiduosRepository
from app.infrastructure.analisis_repository import AnalisisIARepository

from app.dto.waste_dto import (
    CrearResiduoRequestDto,
    CrearResiduoResponseDto,
    ListarResiduosResponseDto,
    AnalisisIARequestDto,
    AnalisisIAResponseDto,
    TipoResiduoRequesDto,
    TipoResiduoResponseDto,
    EstadisticaTipoDto, 
    EstadisticasResponseDto
)

logger = logging.getLogger(__name__)


class WasteService:

    def __init__(
        self,
        tipos_repo: TiposResiduosRepository,
        residuos_repo: ResiduosRepository,
        analisis_repo: AnalisisIARepository,
    ):
        self.tipos_repo = tipos_repo
        self.residuos_repo = residuos_repo
        self.analisis_repo = analisis_repo

        self.ai_client = AzureOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_KEY,
            api_version="2024-05-01-preview",
        )

    # ============================================================
    # TIPOS DE RESIDUO
    # ============================================================
    def crear_tipo_residuo(self, nombre: str, descripcion: str | None) -> TipoResiduoResponseDto:
        # Evitar duplicados
        tipos_existentes = self.tipos_repo.listar()
        nombres_lower = [t["nombre"].strip().lower() for t in tipos_existentes]

        if nombre.strip().lower() in nombres_lower:
            logger.warning(f"Intento de crear tipo duplicado: {nombre}")
            raise ValueError("El tipo de residuo ya existe")

        tipo_id = self.tipos_repo.crear(nombre, descripcion)
        logger.info(f"Tipo de residuo creado: {nombre} (ID {tipo_id})")
        return TipoResiduoResponseDto(id=tipo_id, nombre=nombre, descripcion=descripcion)

    def listar_tipos(self) -> List[TipoResiduoResponseDto]:
        tipos = self.tipos_repo.listar()
        return [TipoResiduoResponseDto(**t) for t in tipos]

    def validar_tipo_residuo(self, tipo_residuo_id: int):
        tipo = self.tipos_repo.obtener_por_id(tipo_residuo_id)
        if not tipo:
            logger.error(f"Tipo de residuo no encontrado: ID={tipo_residuo_id}")
            raise ValueError("El tipo de residuo no existe")
        return tipo
    
    def obtener_tipo_por_id(self, tipo_id: int) -> TipoResiduoResponseDto:
        tipo = self.tipos_repo.obtener_por_id(tipo_id)

        if not tipo:
            logger.error(f"Tipo de residuo no encontrado: ID={tipo_id}")
            raise ValueError("Tipo de residuo no encontrado")

        return TipoResiduoResponseDto(**tipo)

    # ============================================================
    # REGISTROS DE RESIDUOS
    # ============================================================
    def registrar_residuo(self, dto: CrearResiduoRequestDto) -> CrearResiduoResponseDto:
        # Validar que el tipo exista
        self.validar_tipo_residuo(dto.tipo_residuo_id)

        # Validaciones básicas
        if dto.cantidad_kg <= 0:
            logger.error(f"Cantidad inválida: {dto.cantidad_kg}")
            raise ValueError("La cantidad debe ser mayor a cero")

        if not isinstance(dto.dia, date):
            logger.error(f"Fecha inválida: {dto.dia}")
            raise ValueError("Fecha inválida")

        residuo_id = self.residuos_repo.crear(
            dia=dto.dia,
            cantidad_kg=dto.cantidad_kg,
            tipo_residuo_id=dto.tipo_residuo_id,
        )

        logger.info(
            f"Registro creado: ID={residuo_id} Tipo={dto.tipo_residuo_id} {dto.cantidad_kg}kg"
        )

        return CrearResiduoResponseDto(id=residuo_id, **dto.model_dump())
    


    async def registrar_residuos_desde_txt(self, archivo) -> dict:
        # Leer contenido como texto
        contenido = (await archivo.read()).decode("utf-8")
        lineas = contenido.strip().split("\n")

        if not lineas:
            raise ValueError("El archivo TXT está vacío")

        registros = []

        for numero_linea, linea in enumerate(lineas, start=1):
            partes = [p.strip() for p in linea.split(",")]

            if len(partes) != 3:
                raise ValueError(f"Formato inválido en la línea {numero_linea}: {linea}")

            dia_str, cantidad_str, tipo_str = partes

            # Validar fecha
            try:
                dia = date.fromisoformat(dia_str)
            except:
                raise ValueError(f"Fecha inválida en línea {numero_linea}: {dia_str}")

            # Validar cantidad
            try:
                cantidad = float(cantidad_str)
                if cantidad <= 0:
                    raise ValueError
            except:
                raise ValueError(f"Cantidad inválida en línea {numero_linea}: {cantidad_str}")

            # Validar tipo_residuo_id
            try:
                tipo_residuo_id = int(tipo_str)
            except:
                raise ValueError(f"Tipo de residuo inválido en línea {numero_linea}: {tipo_str}")

            # Validar que exista en BD
            self.validar_tipo_residuo(tipo_residuo_id)

            registros.append({
                "dia": dia,
                "cantidad_kg": cantidad,
                "tipo_residuo_id": tipo_residuo_id
            })

        # Registrar en lote
        creados = self.residuos_repo.crear_lote(registros)

        return {
            "registros_creados": creados,
            "lineas_procesadas": len(registros)
        }

    

    def registrar_residuos_lote(self, registros: list[CrearResiduoRequestDto]) -> dict:
        if not registros:
            raise ValueError("La lista de registros está vacía")

        registros_validados = []

        for dto in registros:
            # Validación del tipo de residuo
            self.validar_tipo_residuo(dto.tipo_residuo_id)

            # Validar cantidad
            if dto.cantidad_kg <= 0:
                raise ValueError(f"Cantidad inválida en día {dto.dia}: {dto.cantidad_kg}")

            # Validar fecha
            if not isinstance(dto.dia, date):
                raise ValueError(f"Fecha inválida en registro: {dto.dia}")

            registros_validados.append({
                "dia": dto.dia,
                "cantidad_kg": dto.cantidad_kg,
                "tipo_residuo_id": dto.tipo_residuo_id
            })

        creados = self.residuos_repo.crear_lote(registros_validados)

        logger.info(f"{creados} registros creados en lote")

        return {"registros_creados": creados}
    
    def obtener_residuo_por_id(self, registro_id: int) -> ListarResiduosResponseDto:
        row = self.residuos_repo.obtener_por_id(registro_id)

        if not row:
            raise ValueError("Registro de residuo no encontrado")

        return ListarResiduosResponseDto(**row)



    def listar_residuos(
        self, fecha_inicio: date, fecha_fin: date
    ) -> List[ListarResiduosResponseDto]:

        if fecha_fin < fecha_inicio:
            logger.error(f"Rango de fechas inválido: {fecha_inicio} - {fecha_fin}")
            raise ValueError("La fecha fin debe ser mayor o igual a la fecha inicio")

        registros = self.residuos_repo.listar_por_rango(fecha_inicio, fecha_fin)
        logger.info(f"{len(registros)} registros encontrados en rango dado")

        return [ListarResiduosResponseDto(**r) for r in registros]
    

   
    def obtener_estadisticas(self, fecha_inicio: date, fecha_fin: date) -> EstadisticasResponseDto:

        if fecha_fin < fecha_inicio:
            raise ValueError("La fecha fin debe ser mayor o igual a la fecha inicio")

        rows = self.residuos_repo.estadisticas_por_rango(fecha_inicio, fecha_fin)

        if not rows:
            raise ValueError("No existen registros en el rango indicado")

        # Total global
        total_global = sum(float(r["total_kg"]) for r in rows)

        tipos_dto = []

        for r in rows:
            porcentaje = round(
                (float(r["total_kg"]) / total_global) * 100, 2
            )

            tipos_dto.append(
                EstadisticaTipoDto(
                    tipo_id=r["tipo_id"],
                    tipo_residuo=r["tipo_residuo"],
                    descripcion_tipo_residuo=r["descripcion_tipo_residuo"],

                    cantidad_registros=r["cantidad_registros"],
                    total_kg=float(r["total_kg"]),
                    promedio_kg=float(r["promedio_kg"]),
                    minimo_kg=float(r["minimo_kg"]),
                    maximo_kg=float(r["maximo_kg"]),

                    porcentaje=porcentaje
                )
            )

        return EstadisticasResponseDto(
            fecha_inicio=str(fecha_inicio),
            fecha_fin=str(fecha_fin),
            total_global_kg=total_global,
            tipos=tipos_dto
        )


    # ============================================================
    # ANÁLISIS IA
    # ============================================================
    def generar_analisis(self, dto: AnalisisIARequestDto) -> AnalisisIAResponseDto:

        if dto.fecha_fin < dto.fecha_inicio:
            raise ValueError("La fecha fin debe ser mayor o igual a la fecha inicio")

        # 1. Obtener registros
        registros = self.residuos_repo.listar_por_rango(dto.fecha_inicio, dto.fecha_fin)
        if not registros:
            logger.warning("Intento de análisis sin registros")
            raise ValueError("No existen registros en el rango indicado")

        # 2. Construir texto enriquecido para la IA
        texto_registros = "\n".join(
            f"{r['dia']} — {r['tipo_residuo']} "
            f"({r['descripcion_tipo_residuo']}): "
            f"{float(r['cantidad_kg'])} kg"
            for r in registros
        )

        # 3. Prompt mejorado
        prompt = f"""
        Eres un especialista en gestión de residuos en comedores industriales.

        A continuación se muestran registros individuales de residuos generados día por día.
        Cada registro contiene:

        - Fecha exacta
        - Tipo de residuo
        - Descripción del residuo
        - Cantidad en kilogramos

        Registros:
        {texto_registros}

        Con esta información, genera:

        1. Un análisis narrativo del comportamiento de los residuos durante el periodo.
        2. Observaciones sobre patrones diarios (picos, reducciones, irregularidades).
        3. Posibles causas operativas que expliquen estos cambios día a día.
        4. Recomendaciones prácticas aplicables al funcionamiento diario del comedor.
        5. Oportunidades simples de valorización basadas en los tipos observados.
        6. No calcules estadísticas ni porcentajes; solo analiza lo que se observa de los registros.

        Responde en español, con un tono profesional y claro.
        """

        # 4. Llamada a Azure OpenAI
        try:
            resp = self.ai_client.chat.completions.create(
                model=settings.AZURE_OPENAI_DEPLOYMENT,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
            )
            texto_ai = resp.choices[0].message.content

        except Exception as e:
            logger.error(f"Error generando análisis IA: {e}")
            raise RuntimeError("Error al generar análisis con IA")

        # 5. Guardar en BD
        row = self.analisis_repo.crear(
            fecha_inicio=dto.fecha_inicio,
            fecha_fin=dto.fecha_fin,
            resumen="Resumen automático generado por IA",
            recomendaciones=texto_ai,
            modelo_usado=settings.AZURE_OPENAI_DEPLOYMENT,
        )

        logger.info(f"Análisis IA creado {row}")

        return AnalisisIAResponseDto(**row)
    

    def generar_analisis_estadistico(self, fecha_inicio: date, fecha_fin: date) -> AnalisisIAResponseDto:

        if fecha_fin < fecha_inicio:
            raise ValueError("La fecha fin debe ser mayor o igual a la fecha inicio")

        # 1. Obtener estadísticas reales
        stats = self.residuos_repo.estadisticas_por_rango(fecha_inicio, fecha_fin)
        if not stats:
            raise ValueError("No existen registros en el rango indicado")

        total_global = sum(float(s["total_kg"]) for s in stats)

        # 2. Convertir estadísticas a texto para IA
        texto_stats = "\n".join(
            f"{s['tipo_residuo']} ({s['descripcion_tipo_residuo']}): "
            f"{float(s['total_kg'])} kg — {round((float(s['total_kg'])/total_global)*100, 2)}%"
            for s in stats
        )

        prompt = f"""
    Eres un especialista en gestión de residuos industriales.

    Usa las siguientes estadísticas para generar un informe avanzado.
    No inventes números, solo analiza los que se te dan.

    Estadísticas (reales y exactas):
    {texto_stats}

    Genera:

    1. Un análisis profesional del comportamiento de los residuos.
    2. Identificación de puntos críticos.
    3. Explicación de causas probables.
    4. Recomendaciones específicas para el comedor de Textil del Valle.
    5. Ideas de valorización (compostaje, biodigestión, reducción, optimización en cocina).
    6. Sugerencias de control y mejora continua.

    Responde solo en español.
    """

        try:
            resp = self.ai_client.chat.completions.create(
                model=settings.AZURE_OPENAI_DEPLOYMENT,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )
            texto_ai = resp.choices[0].message.content

        except Exception as e:
            logger.error(f"Error IA: {e}")
            raise RuntimeError("Error al generar análisis con IA")

        # 5. Guardar en BD
        row = self.analisis_repo.crear(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            resumen="Análisis estadístico avanzado generado por IA",
            recomendaciones=texto_ai,
            modelo_usado=settings.AZURE_OPENAI_DEPLOYMENT,
        )

        return AnalisisIAResponseDto(**row)


    # ============================================================
    # OBTENER ANÁLISIS
    # ============================================================
    def listar_analisis(self) -> List[AnalisisIAResponseDto]:
        rows = self.analisis_repo.listar()
        return [AnalisisIAResponseDto(**r) for r in rows]

    def obtener_analisis_por_id(self, analisis_id: int) -> AnalisisIAResponseDto:
        row = self.analisis_repo.obtener_por_id(analisis_id)
        if not row:
            logger.error(f"Análisis no encontrado: ID={analisis_id}")
            raise ValueError("Análisis no encontrado")
        return AnalisisIAResponseDto(**row)
