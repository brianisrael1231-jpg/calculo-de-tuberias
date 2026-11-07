"""Modelos de datos para el cálculo y verificación simplificada de Hazen-Williams."""

from dataclasses import dataclass
from enum import Enum
from typing import List


class EstadoVelocidad(str, Enum):
    OPTIMO = "OPTIMO"
    SEDIMENTACION = "SEDIMENTACION"
    EROSION = "EROSION"


@dataclass
class DatosEntrada:
    """Los cuatro datos solicitados al usuario."""
    longitud_m: float
    diametro_valor: float
    diametro_unidad: str  # 'mm' o 'pulgadas'
    caudal_valor: float
    caudal_unidad: str    # 'l_s' o 'm3_s'
    material_id: str      # 'pvc', 'polietileno', 'acero', 'hierro_fundido'


@dataclass
class PasoMemoria:
    """Paso detallado de memoria de cálculo."""
    titulo: str
    formula: str
    sustitucion: str
    resultado: str
    unidad: str


@dataclass
class ResultadoCalculo:
    """Valores devueltos de forma inmediata."""
    # 1. Coeficiente de rugosidad aplicado automáticamente
    material_nombre: str
    c_rugosidad: float

    # Datos en unidades SI normalizadas
    longitud_m: float
    diametro_mm: float
    diametro_pulgadas: float
    diametro_m: float
    caudal_l_s: float
    caudal_m3_s: float
    area_m2: float

    # 2. Velocidad resultante y diagnóstico
    velocidad_ms: float
    estado_velocidad: EstadoVelocidad
    mensaje_velocidad: str
    clase_css_velocidad: str  # 'success', 'warning', 'danger'

    # 3. Pérdida de carga acumulada
    j_unitaria_m_m: float
    j_unitaria_m_100m: float
    perdida_carga_mca: float  # en metros de columna de agua
    perdida_carga_bar: float  # en bar

    # Memoria técnica
    pasos_memoria: List[PasoMemoria]


@dataclass
class DatosEntradaDiametro:
    """Datos para calcular el diámetro necesario de una cañería."""
    caudal_valor: float
    caudal_unidad: str      # 'l_s', 'm3_s', 'm3_h'
    longitud_m: float
    material_id: str        # 'pvc', 'polietileno', 'acero', 'hierro_fundido', 'hormigon'
    criterio_tipo: str      # 'perdida_mca', 'perdida_bar', 'velocidad'
    criterio_valor: float   # Valor límite fijado (m.c.a., bar o m/s)


@dataclass
class ResultadoCalculoDiametro:
    """Resultados del cálculo de diámetro necesario."""
    material_nombre: str
    c_rugosidad: float
    longitud_m: float
    caudal_l_s: float
    caudal_m3_s: float
    criterio_descripcion: str

    # Diámetro teórico mínimo calculado
    d_min_teorico_mm: float
    d_min_teorico_pulg: float
    d_min_teorico_m: float
    v_teorica_ms: float

    # Diámetro comercial recomendado inmediato superior
    dn_comercial_sugerido: str
    d_comercial_mm: float
    d_comercial_pulg: str

    # Comprobaciones reales con el diámetro comercial elegido
    v_comercial_ms: float
    estado_v_comercial: EstadoVelocidad
    mensaje_v_comercial: str
    clase_css_v_comercial: str
    hf_comercial_mca: float
    hf_comercial_bar: float
    j_comercial_m_100m: float

    # Pasos explicativos
    pasos_memoria: List[PasoMemoria]
