from datetime import date
import logging
from typing import List
from fastapi import UploadFile, File
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)



from app.infrastructure.tipos_residuos_repository import TiposResiduosRepository
from app.infrastructure.residuos_repository import ResiduosRepository
from app.infrastructure.analisis_repository import AnalisisIARepository

from app.domain.waste_service import WasteService

from app.dto.waste_dto import (
    CrearResiduoRequestDto,
    CrearResiduoResponseDto,
    EstadisticasResponseDto,
    ListarResiduosResponseDto,
    TipoResiduoRequesDto,
    TipoResiduoResponseDto,
    AnalisisIARequestDto,
    AnalisisIAResponseDto,
)
from database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================
#  Dependency Injector
# ============================================================
def get_waste_service(conn=Depends(get_db)) -> WasteService:
    tipos_repo = TiposResiduosRepository(conn)
    residuos_repo = ResiduosRepository(conn)
    analisis_repo = AnalisisIARepository(conn)
    return WasteService(tipos_repo, residuos_repo, analisis_repo)


# ============================================================
#  Endpoints de Tipos de Residuo
# ============================================================
@router.post(
    "/tipos",
    response_model=TipoResiduoResponseDto,
    status_code=status.HTTP_201_CREATED
)
def crear_tipo_residuo(
    dto: TipoResiduoRequesDto,
    service: WasteService = Depends(get_waste_service),
):
    try:
        return service.crear_tipo_residuo(dto.nombre, dto.descripcion)
    except ValueError as e:
        logger.warning(f"Validación fallida al crear tipo: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error interno al crear tipo: {e}")
        raise HTTPException(status_code=500, detail="Error interno al crear tipo de residuo.")
    
@router.get("/tipos/{tipo_id}", response_model=TipoResiduoResponseDto)
def get_tipo_residuo(tipo_id: int, service: WasteService = Depends(get_waste_service)):
    try:
        return service.obtener_tipo_por_id(tipo_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error al obtener tipo de residuo: {e}")
        raise HTTPException(status_code=500, detail="Error interno")

@router.get(
    "/tipos",
    response_model=List[TipoResiduoResponseDto]
)
def listar_tipos_residuo(service: WasteService = Depends(get_waste_service)):
    try:
        return service.listar_tipos()
    except Exception as e:
        logger.error(f"Error al listar tipos: {e}")
        raise HTTPException(status_code=500, detail="No se pudieron obtener los tipos de residuo.")


# ============================================================
#  Endpoints de Registros de Residuos
# ============================================================
@router.get(
    "/registros/{registro_id}",
    response_model=ListarResiduosResponseDto
)
def obtener_residuo(
    registro_id: int,
    service: WasteService = Depends(get_waste_service)
):
    try:
        return service.obtener_residuo_por_id(registro_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error interno al obtener residuo {registro_id}: {e}")
        raise HTTPException(status_code=500, detail="Error interno al obtener el residuo.")

@router.get(
    "/registros",
    response_model=List[ListarResiduosResponseDto]
)
def listar_residuos(
    fecha_inicio: str,
    fecha_fin: str,
    service: WasteService = Depends(get_waste_service),
):
    try:
        return service.listar_residuos(fecha_inicio, fecha_fin)
    except ValueError as e:
        logger.warning(f"Rango inválido: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error al listar residuos: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno al listar residuos: {e}")
    


@router.post(
    "/registros",
    response_model=CrearResiduoResponseDto,
    status_code=status.HTTP_201_CREATED
)
def registrar_residuo(
    request: CrearResiduoRequestDto,
    service: WasteService = Depends(get_waste_service),
):
    try:
        return service.registrar_residuo(request)
    except ValueError as e:
        logger.warning(f"Error de validación al registrar residuo: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error interno al registrar residuo: {e}")
        raise HTTPException(status_code=500, detail="Error interno al registrar residuo.")

@router.get("/estadisticas", response_model=EstadisticasResponseDto)
def obtener_estadisticas(
    fecha_inicio: str,
    fecha_fin: str,
    service: WasteService = Depends(get_waste_service)
):
    try:
        fi = date.fromisoformat(fecha_inicio)
        ff = date.fromisoformat(fecha_fin)
        return service.obtener_estadisticas(fi, ff)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        raise HTTPException(status_code=500, detail="Error interno")


@router.post("/registros/upload-txt", status_code=201)
async def registrar_residuos_txt(
    archivo: UploadFile = File(...),
    service: WasteService = Depends(get_waste_service),
):
    try:
        return await service.registrar_residuos_desde_txt(archivo)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error al procesar archivo TXT: {e}")
        raise HTTPException(status_code=500, detail="Error interno procesando archivo TXT")


@router.post("/registros/lote", status_code=201)
def registrar_residuos_lote(
    registros: list[CrearResiduoRequestDto],
    service: WasteService = Depends(get_waste_service)
):
    try:
        return service.registrar_residuos_lote(registros)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error registrando lote: {e}")
        raise HTTPException(status_code=500, detail="Error interno al registrar lote")
    



# ============================================================
#  Endpoints de Análisis con IA
# ============================================================
@router.post(
    "/analisis",
    response_model=AnalisisIAResponseDto,
    status_code=status.HTTP_201_CREATED
)
def generar_analisis(
    request: AnalisisIARequestDto,
    service: WasteService = Depends(get_waste_service),
):
    """
    Genera un análisis IA en base a varios registros de residuos.
    """
    try:
        return service.generar_analisis(request)
    except ValueError as e:
        logger.warning(f"No se pudo generar análisis: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        logger.error(f"Error IA Azure: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.exception("Error inesperado generando análisis")
        raise HTTPException(status_code=500, detail="Error inesperado generando análisis.")


@router.post(
    "/analisis/estadistico",
    response_model=AnalisisIAResponseDto,
    status_code=status.HTTP_201_CREATED
)
def generar_analisis_estadistico(
    request: AnalisisIARequestDto,
    service: WasteService = Depends(get_waste_service)
):
    """
    Genera un análisis avanzado basado en estadísticas reales
    y un reporte detallado generado por IA.
    """
    try:
        return service.generar_analisis_estadistico(
            request.fecha_inicio,
            request.fecha_fin
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    except Exception as e:
        logger.exception("Error inesperado generando análisis estadístico")
        raise HTTPException(status_code=500, detail="Error inesperado generando análisis estadístico.")



@router.get(
    "/analisis",
    response_model=List[AnalisisIAResponseDto]
)
def listar_analisis(service: WasteService = Depends(get_waste_service)):
    try:
        return service.listar_analisis()
    except Exception as e:
        logger.error(f"Error al obtener análisis: {e}")
        raise HTTPException(status_code=500, detail="Error interno al obtener los análisis.")


@router.get(
    "/analisis/{analisis_id}",
    response_model=AnalisisIAResponseDto
)
def obtener_analisis(analisis_id: int, service: WasteService = Depends(get_waste_service)):
    try:
        return service.obtener_analisis_por_id(analisis_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error interno al obtener análisis {analisis_id}: {e}")
        raise HTTPException(status_code=500, detail="Error interno al obtener el análisis.")
