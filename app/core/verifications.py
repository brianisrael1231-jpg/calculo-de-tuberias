"""Módulo de verificaciones técnicas y generación de semáforos (CUMPLE / ADVERTENCIA / NO CUMPLE).

Todos los criterios se basan en parámetros configurables y visibles para el usuario.
"""

from typing import List, Optional

from app.config import (
    HAZEN_WILLIAMS_D_MIN_MM,
    HAZEN_WILLIAMS_V_MAX_MS,
)
from app.core.models import (
    DiametroSugeridoInfo,
    EstadoSemaforo,
    ItemVerificacion,
    TramoCalculado,
)


def _formatear_numero(v: float, dec: int = 2) -> str:
    from app.core.hydraulics import fmt_es
    return fmt_es(v, dec)


def verificar_sistema(
    tramos: List[TramoCalculado],
    presion_residual_mca: Optional[float],
    presion_min_requerida_mca: Optional[float],
    v_min_limite: float,
    v_max_limite: float,
    j_max_limite_m_m: Optional[float],
) -> List[ItemVerificacion]:
    """Evalúa las condiciones hidráulicas del sistema completo y genera la lista de verificaciones."""
    resultados: List[ItemVerificacion] = []

    # 1. Verificación de velocidad y límites empíricos por tramo
    for t in tramos:
        # Velocidad dentro de límites de diseño
        if t.velocidad_ms < v_min_limite:
            resultados.append(
                ItemVerificacion(
                    parametro=f"Tramo {t.numero} - Velocidad de flujo",
                    estado=EstadoSemaforo.ADVERTENCIA,
                    valor_obtenido=f"{_formatear_numero(t.velocidad_ms, 2)} m/s",
                    limite_referencia=f"Mínimo: {_formatear_numero(v_min_limite, 2)} m/s",
                    mensaje="Velocidad baja. Riesgo de sedimentación de sólidos en suspensión.",
                    nivel_clase_css="warning",
                )
            )
        elif t.velocidad_ms > v_max_limite:
            resultados.append(
                ItemVerificacion(
                    parametro=f"Tramo {t.numero} - Velocidad de flujo",
                    estado=EstadoSemaforo.NO_CUMPLE,
                    valor_obtenido=f"{_formatear_numero(t.velocidad_ms, 2)} m/s",
                    limite_referencia=f"Máximo: {_formatear_numero(v_max_limite, 2)} m/s",
                    mensaje="Velocidad excesiva. Riesgo de ruidos, erosión y sobrepresiones elevadas por golpe de ariete.",
                    nivel_clase_css="danger",
                )
            )
        else:
            resultados.append(
                ItemVerificacion(
                    parametro=f"Tramo {t.numero} - Velocidad de flujo",
                    estado=EstadoSemaforo.CUMPLE,
                    valor_obtenido=f"{_formatear_numero(t.velocidad_ms, 2)} m/s",
                    limite_referencia=f"[{_formatear_numero(v_min_limite, 2)} - {_formatear_numero(v_max_limite, 2)}] m/s",
                    mensaje="Velocidad dentro del rango normativo admisible.",
                    nivel_clase_css="success",
                )
            )

        # Validez de Hazen-Williams: Diámetro
        if t.d_interior_mm < HAZEN_WILLIAMS_D_MIN_MM:
            resultados.append(
                ItemVerificacion(
                    parametro=f"Tramo {t.numero} - Validez Hazen-Williams (Diámetro)",
                    estado=EstadoSemaforo.ADVERTENCIA,
                    valor_obtenido=f"{_formatear_numero(t.d_interior_mm, 1)} mm",
                    limite_referencia=f"Recomendado >= {_formatear_numero(HAZEN_WILLIAMS_D_MIN_MM, 0)} mm",
                    mensaje=(
                        "Diámetro menor a 50 mm. La fórmula empírica de Hazen-Williams pierde precisión "
                        "en tuberías pequeñas; se recomienda contrastar con Darcy-Weisbach."
                    ),
                    nivel_clase_css="warning",
                )
            )
        else:
            resultados.append(
                ItemVerificacion(
                    parametro=f"Tramo {t.numero} - Validez Hazen-Williams (Diámetro)",
                    estado=EstadoSemaforo.CUMPLE,
                    valor_obtenido=f"{_formatear_numero(t.d_interior_mm, 1)} mm",
                    limite_referencia=f">= {_formatear_numero(HAZEN_WILLIAMS_D_MIN_MM, 0)} mm",
                    mensaje="Diámetro dentro del rango habitual de validez empírica.",
                    nivel_clase_css="success",
                )
            )

        # Validez de Hazen-Williams: Velocidad máxima
        if t.velocidad_ms > HAZEN_WILLIAMS_V_MAX_MS:
            resultados.append(
                ItemVerificacion(
                    parametro=f"Tramo {t.numero} - Validez Hazen-Williams (Velocidad)",
                    estado=EstadoSemaforo.ADVERTENCIA,
                    valor_obtenido=f"{_formatear_numero(t.velocidad_ms, 2)} m/s",
                    limite_referencia=f"Recomendado <= {_formatear_numero(HAZEN_WILLIAMS_V_MAX_MS, 0)} m/s",
                    mensaje="Velocidad superior al rango empírico usual de aplicación de Hazen-Williams (<= 3 m/s).",
                    nivel_clase_css="warning",
                )
            )

        # Pérdida unitaria J máxima si fue definida
        if j_max_limite_m_m is not None and j_max_limite_m_m > 0:
            if t.j_m_m > j_max_limite_m_m:
                resultados.append(
                    ItemVerificacion(
                        parametro=f"Tramo {t.numero} - Pérdida Unitaria (J)",
                        estado=EstadoSemaforo.NO_CUMPLE,
                        valor_obtenido=f"{_formatear_numero(t.j_m_100m, 2)} m/100m ({_formatear_numero(t.j_m_m, 5)} m/m)",
                        limite_referencia=f"<= {_formatear_numero(j_max_limite_m_m * 100.0, 2)} m/100m",
                        mensaje="Pérdida de carga unitaria superior al límite admisible fijado.",
                        nivel_clase_css="danger",
                    )
                )
            else:
                resultados.append(
                    ItemVerificacion(
                        parametro=f"Tramo {t.numero} - Pérdida Unitaria (J)",
                        estado=EstadoSemaforo.CUMPLE,
                        valor_obtenido=f"{_formatear_numero(t.j_m_100m, 2)} m/100m",
                        limite_referencia=f"<= {_formatear_numero(j_max_limite_m_m * 100.0, 2)} m/100m",
                        mensaje="Pérdida unitaria dentro del gradiente admisible.",
                        nivel_clase_css="success",
                    )
                )

    # 2. Verificaciones de Presión Residual
    if presion_residual_mca is not None:
        if presion_residual_mca < 0:
            resultados.append(
                ItemVerificacion(
                    parametro="Presión Residual en el extremo final",
                    estado=EstadoSemaforo.NO_CUMPLE,
                    valor_obtenido=f"{_formatear_numero(presion_residual_mca, 2)} m.c.a.",
                    limite_referencia=">= 0,00 m.c.a.",
                    mensaje=(
                        "¡PRESIÓN NEGATIVA! Condición no físicamente posible en conducción por gravedad "
                        "o presión continua. Indica que la energía disponible no vence las pérdidas y el desnivel. "
                        "Riesgo severo de cavitación, colapso de columna líquida y succión de contaminantes."
                    ),
                    nivel_clase_css="danger",
                )
            )
        elif presion_min_requerida_mca is not None and presion_residual_mca < presion_min_requerida_mca:
            resultados.append(
                ItemVerificacion(
                    parametro="Presión Residual de Servicio",
                    estado=EstadoSemaforo.NO_CUMPLE,
                    valor_obtenido=f"{_formatear_numero(presion_residual_mca, 2)} m.c.a.",
                    limite_referencia=f">= {_formatear_numero(presion_min_requerida_mca, 2)} m.c.a.",
                    mensaje="La presión residual disponible es inferior a la presión mínima de servicio exigida.",
                    nivel_clase_css="danger",
                )
            )
        elif presion_min_requerida_mca is not None:
            resultados.append(
                ItemVerificacion(
                    parametro="Presión Residual de Servicio",
                    estado=EstadoSemaforo.CUMPLE,
                    valor_obtenido=f"{_formatear_numero(presion_residual_mca, 2)} m.c.a.",
                    limite_referencia=f">= {_formatear_numero(presion_min_requerida_mca, 2)} m.c.a.",
                    mensaje="Presión residual suficiente para garantizar el servicio exigido.",
                    nivel_clase_css="success",
                )
            )

    return resultados


def verificar_modo_inverso(
    d_min_teorico_mm: float,
    velocidad_teorica_ms: float,
    sugerencia: Optional[DiametroSugeridoInfo],
    v_min_limite: float,
    v_max_limite: float,
) -> List[ItemVerificacion]:
    """Evalúa las verificaciones para el modo inverso (cálculo de diámetro mínimo)."""
    resultados: List[ItemVerificacion] = []

    # Validez Hazen-Williams diámetro
    if d_min_teorico_mm < HAZEN_WILLIAMS_D_MIN_MM:
        resultados.append(
            ItemVerificacion(
                parametro="Validez Hazen-Williams (Diámetro teórico)",
                estado=EstadoSemaforo.ADVERTENCIA,
                valor_obtenido=f"{_formatear_numero(d_min_teorico_mm, 2)} mm",
                limite_referencia=f">= {_formatear_numero(HAZEN_WILLIAMS_D_MIN_MM, 0)} mm",
                mensaje="El diámetro teórico calculado es menor a 50 mm; Hazen-Williams tiene menor precisión en este rango.",
                nivel_clase_css="warning",
            )
        )
    else:
        resultados.append(
            ItemVerificacion(
                parametro="Validez Hazen-Williams (Diámetro teórico)",
                estado=EstadoSemaforo.CUMPLE,
                valor_obtenido=f"{_formatear_numero(d_min_teorico_mm, 2)} mm",
                limite_referencia=f">= {_formatear_numero(HAZEN_WILLIAMS_D_MIN_MM, 0)} mm",
                mensaje="Diámetro dentro del rango válido de aplicación empírica.",
                nivel_clase_css="success",
            )
        )

    # Velocidad comercial sugerida
    if sugerencia:
        v_com = sugerencia.velocidad_ms
        if v_com < v_min_limite:
            resultados.append(
                ItemVerificacion(
                    parametro=f"Velocidad con Diámetro Comercial ({sugerencia.dn_nominal})",
                    estado=EstadoSemaforo.ADVERTENCIA,
                    valor_obtenido=f"{_formatear_numero(v_com, 2)} m/s",
                    limite_referencia=f"Mínimo: {_formatear_numero(v_min_limite, 2)} m/s",
                    mensaje="Con este diámetro la velocidad queda por debajo del mínimo de autolimpieza.",
                    nivel_clase_css="warning",
                )
            )
        elif v_com > v_max_limite:
            resultados.append(
                ItemVerificacion(
                    parametro=f"Velocidad con Diámetro Comercial ({sugerencia.dn_nominal})",
                    estado=EstadoSemaforo.NO_CUMPLE,
                    valor_obtenido=f"{_formatear_numero(v_com, 2)} m/s",
                    limite_referencia=f"Máximo: {_formatear_numero(v_max_limite, 2)} m/s",
                    mensaje="Con este diámetro la velocidad supera el límite máximo recomendado.",
                    nivel_clase_css="danger",
                )
            )
        else:
            resultados.append(
                ItemVerificacion(
                    parametro=f"Velocidad con Diámetro Comercial ({sugerencia.dn_nominal})",
                    estado=EstadoSemaforo.CUMPLE,
                    valor_obtenido=f"{_formatear_numero(v_com, 2)} m/s",
                    limite_referencia=f"[{_formatear_numero(v_min_limite, 2)} - {_formatear_numero(v_max_limite, 2)}] m/s",
                    mensaje="La velocidad en régimen comercial está dentro del rango óptimo.",
                    nivel_clase_css="success",
                )
            )

    return resultados
