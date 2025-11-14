from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional

# ==============================
# Tipos de residuos
# ==============================
class TipoResiduoRequesDto(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    
class TipoResiduoResponseDto(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str] = None

# ==============================
# Registrar residuo
# ==============================
class CrearResiduoRequestDto(BaseModel):
    dia: date
    cantidad_kg: float
    tipo_residuo_id: int

class CrearResiduoResponseDto(CrearResiduoRequestDto):
    id: int

# ==============================
# Listar residuos
# ==============================
class ListarResiduosResponseDto(BaseModel):
    id: int
    dia: date
    cantidad_kg: float
    tipo_residuo_id: int
    tipo_residuo: str                  
    descripcion_tipo_residuo: str       
    fecha_creacion: datetime

# ==============================
# Análisis IA
# ==============================
class AnalisisIARequestDto(BaseModel):
    fecha_inicio: date
    fecha_fin: date

class AnalisisIAResponseDto(BaseModel):
    id: int
    fecha_inicio: date
    fecha_fin: date
    resumen: Optional[str]
    recomendaciones: Optional[str]
    modelo_usado: str
    fecha_creacion: Optional[datetime] = None



## estadisticaa

class EstadisticaTipoDto(BaseModel):
    tipo_id: int
    tipo_residuo: str
    descripcion_tipo_residuo: str

    cantidad_registros: int
    total_kg: float
    promedio_kg: float
    minimo_kg: float
    maximo_kg: float

    porcentaje: float

class EstadisticasResponseDto(BaseModel):
    fecha_inicio: str
    fecha_fin: str
    total_global_kg: float
    tipos: list[EstadisticaTipoDto]
