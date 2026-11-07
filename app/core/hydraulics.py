"""Motor de cálculo hidráulico puro según el procedimiento simplificado.

Procesa:
a) Asignación de Rugosidad (C) según el material.
b) Cálculo de la Velocidad del Agua: V = Q / A.
c) Cálculo de la Pérdida de Carga según Hazen-Williams: hf en m.c.a. y bar.
"""

import math
from typing import List

from app.config import (
    BAR_A_MCA,
    DIAMETROS_COMERCIALES,
    MATERIALES_CATALOGO,
    MCA_A_BAR,
    PULGADA_A_METROS,
    PULGADA_A_MM,
    VELOCIDAD_MAX_OPTIMA,
    VELOCIDAD_MIN_OPTIMA,
)
from app.core.models import (
    DatosEntrada,
    DatosEntradaDiametro,
    EstadoVelocidad,
    PasoMemoria,
    ResultadoCalculo,
    ResultadoCalculoDiametro,
)


def fmt_es(valor: float, decimales: int = 2) -> str:
    """Formatea números con coma decimal (estilo ES/AR)."""
    if math.isnan(valor) or math.isinf(valor):
        return str(valor)
    texto = f"{valor:.{decimales}f}"
    partes = texto.split(".")
    entera = partes[0]
    decimal = partes[1] if len(partes) > 1 else ""
    if len(entera) > 3:
        signo = "-" if entera.startswith("-") else ""
        entera_sin_signo = entera.lstrip("-")
        bloques = []
        while len(entera_sin_signo) > 3:
            bloques.insert(0, entera_sin_signo[-3:])
            entera_sin_signo = entera_sin_signo[:-3]
        bloques.insert(0, entera_sin_signo)
        entera = signo + ".".join(bloques)
    return f"{entera},{decimal}" if decimal else entera


def procesar_calculo_hidraulico(datos: DatosEntrada) -> ResultadoCalculo:
    """Ejecuta los cálculos hidráulicos y diagnósticos de acuerdo con el procedimiento solicitado."""
    if datos.longitud_m <= 0:
        raise ValueError("La longitud del tramo debe ser estrictamente mayor a cero.")
    if datos.diametro_valor <= 0:
        raise ValueError("El diámetro del caño debe ser estrictamente mayor a cero.")
    if datos.caudal_valor <= 0:
        raise ValueError("El caudal requerido debe ser estrictamente mayor a cero.")

    # a) ASIGNACIÓN DE RUGOSIDAD (C)
    material_info = MATERIALES_CATALOGO.get(datos.material_id)
    if not material_info:
        raise ValueError(f"Material no reconocido: {datos.material_id}")
    c_hazen = material_info.c_hazen_williams

    # Conversión de Diámetro a metros y milímetros
    if datos.diametro_unidad.lower() in ("pulgadas", "pulg", "in", '"'):
        d_m = datos.diametro_valor * PULGADA_A_METROS
        d_mm = datos.diametro_valor * PULGADA_A_MM
        d_pulg = datos.diametro_valor
    else:  # 'mm'
        d_m = datos.diametro_valor / 1000.0
        d_mm = datos.diametro_valor
        d_pulg = datos.diametro_valor / PULGADA_A_MM

    # Conversión de Caudal a m³/s y L/s
    if datos.caudal_unidad.lower() in ("m3_s", "m³/s", "m3/s"):
        q_m3_s = datos.caudal_valor
        q_l_s = datos.caudal_valor * 1000.0
    else:  # 'l_s'
        q_m3_s = datos.caudal_valor / 1000.0
        q_l_s = datos.caudal_valor

    # b) CÁLCULO DE LA VELOCIDAD DEL AGUA
    # Área transversal: A = π · D² / 4
    area_m2 = math.pi * (d_m ** 2) / 4.0
    # Velocidad: V = Q / A
    velocidad_ms = q_m3_s / area_m2

    # Diagnóstico de rango óptimo de diseño vs erosión / sedimentación
    if velocidad_ms < VELOCIDAD_MIN_OPTIMA:
        estado_v = EstadoVelocidad.SEDIMENTACION
        mensaje_v = (
            f"Baja velocidad ({fmt_es(velocidad_ms, 2)} m/s < {fmt_es(VELOCIDAD_MIN_OPTIMA, 2)} m/s). "
            "Riesgo de sedimentación y acumulación de partículas en la cañería."
        )
        css_v = "warning"
    elif velocidad_ms > VELOCIDAD_MAX_OPTIMA:
        estado_v = EstadoVelocidad.EROSION
        mensaje_v = (
            f"Exceso de velocidad ({fmt_es(velocidad_ms, 2)} m/s > {fmt_es(VELOCIDAD_MAX_OPTIMA, 2)} m/s). "
            "Riesgo de erosión interna, ruidos y sobrepresiones por golpe de ariete."
        )
        css_v = "danger"
    else:
        estado_v = EstadoVelocidad.OPTIMO
        mensaje_v = (
            f"Rango óptimo de diseño ({fmt_es(velocidad_ms, 2)} m/s). "
            "Velocidad adecuada: previene sedimentaciones y evita desgaste por erosión."
        )
        css_v = "success"

    # c) CÁLCULO DE LA PÉRDIDA DE CARGA (Hazen-Williams)
    # J = 10,67 · Q^1,852 / (C^1,852 · D^4,87) [m/m]
    j_unitaria_m_m = 10.67 * (q_m3_s ** 1.852) / ((c_hazen ** 1.852) * (d_m ** 4.87))
    j_unitaria_m_100m = j_unitaria_m_m * 100.0

    # Pérdida total acumulada: hf = J · L [m.c.a.]
    perdida_mca = j_unitaria_m_m * datos.longitud_m
    # Conversión a bar: 1 m.c.a. = 0,0980665 bar
    perdida_bar = perdida_mca * MCA_A_BAR

    # Memoria técnica paso a paso
    pasos: List[PasoMemoria] = [
        PasoMemoria(
            titulo="a) Asignación de Coeficiente de Rugosidad (C)",
            formula="C = f(Material)",
            sustitucion=f"Material: {material_info.nombre}",
            resultado=fmt_es(c_hazen, 0),
            unidad="",
        ),
        PasoMemoria(
            titulo="b) Área de la sección transversal del caño",
            formula="A = π · D² / 4",
            sustitucion=f"A = π · ({fmt_es(d_m, 4)} m)² / 4",
            resultado=fmt_es(area_m2, 6),
            unidad="m²",
        ),
        PasoMemoria(
            titulo="c) Cálculo de la Velocidad del Agua",
            formula="V = Q / A",
            sustitucion=f"V = {fmt_es(q_m3_s, 6)} m³/s / {fmt_es(area_m2, 6)} m²",
            resultado=fmt_es(velocidad_ms, 2),
            unidad="m/s",
        ),
        PasoMemoria(
            titulo="d) Pérdida de carga unitaria (Hazen-Williams)",
            formula="J = 10,67 · Q^1,852 / (C^1,852 · D^4,87)",
            sustitucion=(
                f"J = 10,67 · ({fmt_es(q_m3_s, 6)})^1,852 / "
                f"(({fmt_es(c_hazen, 0)})^1,852 · ({fmt_es(d_m, 4)})^4,87)"
            ),
            resultado=f"{fmt_es(j_unitaria_m_m, 5)} m/m ({fmt_es(j_unitaria_m_100m, 2)} m/100m)",
            unidad="m/m",
        ),
        PasoMemoria(
            titulo="e) Pérdida de carga total acumulada en el tramo",
            formula="hf = J · L",
            sustitucion=f"hf = {fmt_es(j_unitaria_m_m, 5)} m/m · {fmt_es(datos.longitud_m, 2)} m",
            resultado=f"{fmt_es(perdida_mca, 2)} m.c.a. ({fmt_es(perdida_bar, 3)} bar)",
            unidad="m.c.a.",
        ),
    ]

    return ResultadoCalculo(
        material_nombre=material_info.nombre,
        c_rugosidad=c_hazen,
        longitud_m=datos.longitud_m,
        diametro_mm=d_mm,
        diametro_pulgadas=d_pulg,
        diametro_m=d_m,
        caudal_l_s=q_l_s,
        caudal_m3_s=q_m3_s,
        area_m2=area_m2,
        velocidad_ms=velocidad_ms,
        estado_velocidad=estado_v,
        mensaje_velocidad=mensaje_v,
        clase_css_velocidad=css_v,
        j_unitaria_m_m=j_unitaria_m_m,
        j_unitaria_m_100m=j_unitaria_m_100m,
        perdida_carga_mca=perdida_mca,
        perdida_carga_bar=perdida_bar,
        pasos_memoria=pasos,
    )


def calcular_diametro_necesario(datos: DatosEntradaDiametro) -> ResultadoCalculoDiametro:
    """Calcula el diámetro interior mínimo necesario y propone el caño comercial inmediato superior.

    Permite dimensionar:
    1. Por pérdida de carga máxima admisible (m.c.a. o bar) usando Hazen-Williams inverso:
       D = [ (10.67 · L · Q^1.852) / (C^1.852 · hf_adm) ]^(1 / 4.87)
    2. Por velocidad económica recomendada de diseño:
       D = sqrt( 4 · Q / (π · V) )
    """
    if datos.longitud_m <= 0:
        raise ValueError("La longitud del tramo debe ser estrictamente mayor a cero.")
    if datos.caudal_valor <= 0:
        raise ValueError("El caudal requerido debe ser estrictamente mayor a cero.")
    if datos.criterio_valor <= 0:
        raise ValueError("El valor límite del criterio debe ser estrictamente mayor a cero.")

    # 1. Caudal normalizado a m³/s y L/s
    uni_q = datos.caudal_unidad.lower().strip()
    if uni_q in ("m3_s", "m³/s", "m3s"):
        q_m3_s = datos.caudal_valor
        q_l_s = datos.caudal_valor * 1000.0
    elif uni_q in ("m3_h", "m³/h", "m3h"):
        q_m3_s = datos.caudal_valor / 3600.0
        q_l_s = q_m3_s * 1000.0
    else:  # 'l_s'
        q_m3_s = datos.caudal_valor / 1000.0
        q_l_s = datos.caudal_valor

    # 2. Material y rugosidad C
    material_info = MATERIALES_CATALOGO.get(datos.material_id)
    if not material_info:
        raise ValueError(f"Material no reconocido: {datos.material_id}")
    c_hazen = material_info.c_hazen_williams

    pasos: List[PasoMemoria] = []
    pasos.append(
        PasoMemoria(
            titulo="1. Caudal de diseño en unidades SI",
            formula="Q [m³/s]",
            sustitucion=f"{fmt_es(datos.caudal_valor, 3)} {datos.caudal_unidad}",
            resultado=f"{fmt_es(q_m3_s, 6)} m³/s ({fmt_es(q_l_s, 2)} L/s)",
            unidad="m³/s",
        )
    )

    # 3. Cálculo de D teórico según el criterio elegido
    crit_tipo = datos.criterio_tipo.lower().strip()

    if crit_tipo in ("perdida_mca", "hf_mca", "mca"):
        hf_adm_mca = datos.criterio_valor
        criterio_desc = f"Pérdida máxima admisible: {fmt_es(hf_adm_mca, 2)} m.c.a."
        # Hazen-Williams inverso
        num = 10.67 * datos.longitud_m * (q_m3_s ** 1.852)
        den = (c_hazen ** 1.852) * hf_adm_mca
        d_m = (num / den) ** (1.0 / 4.87)

        pasos.append(
            PasoMemoria(
                titulo="2. Diámetro mínimo teórico por Hazen-Williams",
                formula="D = [ 10,67 · L · Q^1,852 / (C^1,852 · hf_adm) ]^(1 / 4,87)",
                sustitucion=(
                    f"D = [ 10,67 · {fmt_es(datos.longitud_m, 2)} · ({fmt_es(q_m3_s, 6)})^1,852 / "
                    f"(({fmt_es(c_hazen, 0)})^1,852 · {fmt_es(hf_adm_mca, 2)}) ]^(0,20534)"
                ),
                resultado=f"{fmt_es(d_m * 1000.0, 2)} mm",
                unidad="mm",
            )
        )

    elif crit_tipo in ("perdida_bar", "hf_bar", "bar"):
        hf_bar = datos.criterio_valor
        hf_adm_mca = hf_bar * BAR_A_MCA
        criterio_desc = f"Pérdida máxima admisible: {fmt_es(hf_bar, 3)} bar ({fmt_es(hf_adm_mca, 2)} m.c.a.)"
        num = 10.67 * datos.longitud_m * (q_m3_s ** 1.852)
        den = (c_hazen ** 1.852) * hf_adm_mca
        d_m = (num / den) ** (1.0 / 4.87)

        pasos.append(
            PasoMemoria(
                titulo="2. Conversión de pérdida y diámetro por Hazen-Williams",
                formula="hf_adm [m.c.a.] = hf [bar] · 10,197 -> D = [ 10,67 · L · Q^1,852 / (C^1,852 · hf_adm) ]^(1 / 4,87)",
                sustitucion=f"hf = {fmt_es(hf_bar, 3)} bar = {fmt_es(hf_adm_mca, 2)} m.c.a.",
                resultado=f"{fmt_es(d_m * 1000.0, 2)} mm",
                unidad="mm",
            )
        )

    else:  # 'velocidad'
        v_target = datos.criterio_valor
        criterio_desc = f"Velocidad económica de diseño fijada: {fmt_es(v_target, 2)} m/s"
        # A = Q / V -> D = sqrt(4Q / (pi * V))
        d_m = math.sqrt((4.0 * q_m3_s) / (math.pi * v_target))

        pasos.append(
            PasoMemoria(
                titulo="2. Diámetro teórico por velocidad económica de diseño",
                formula="D = √ ( 4 · Q / ( π · V_diseño ) )",
                sustitucion=f"D = √ ( 4 · {fmt_es(q_m3_s, 6)} / ( π · {fmt_es(v_target, 2)} ) )",
                resultado=f"{fmt_es(d_m * 1000.0, 2)} mm",
                unidad="mm",
            )
        )

    d_mm_teorico = d_m * 1000.0
    d_pulg_teorico = d_mm_teorico / PULGADA_A_MM
    v_teorica = q_m3_s / (math.pi * (d_m ** 2) / 4.0)

    # 4. Búsqueda del diámetro comercial estándar inmediato superior
    sugerido = None
    for cand in DIAMETROS_COMERCIALES:
        if cand.d_interior_mm >= d_mm_teorico:
            sugerido = cand
            break

    if not sugerido:
        # Si sobrepasa el catálogo, sugerir el mayor
        sugerido = DIAMETROS_COMERCIALES[-1]

    d_com_m = sugerido.d_interior_mm / 1000.0
    area_com = math.pi * (d_com_m ** 2) / 4.0
    v_com = q_m3_s / area_com

    # Pérdida de carga real resultante con el diámetro comercial
    j_com_m_m = 10.67 * (q_m3_s ** 1.852) / ((c_hazen ** 1.852) * (d_com_m ** 4.87))
    hf_com_mca = j_com_m_m * datos.longitud_m
    hf_com_bar = hf_com_mca * MCA_A_BAR

    # Diagnóstico de velocidad con caño comercial
    if v_com < VELOCIDAD_MIN_OPTIMA:
        est_v = EstadoVelocidad.SEDIMENTACION
        msg_v = f"Velocidad baja ({fmt_es(v_com, 2)} m/s). Riesgo leve de sedimentación."
        css_v = "warning"
    elif v_com > VELOCIDAD_MAX_OPTIMA:
        est_v = EstadoVelocidad.EROSION
        msg_v = f"Velocidad alta ({fmt_es(v_com, 2)} m/s). Supera el límite de 2 m/s."
        css_v = "danger"
    else:
        est_v = EstadoVelocidad.OPTIMO
        msg_v = f"Velocidad óptima ({fmt_es(v_com, 2)} m/s). Dentro del rango recomendado [0,6 - 2,0] m/s."
        css_v = "success"

    pasos.append(
        PasoMemoria(
            titulo=f"3. Selección comercial inmediata: {sugerido.dn_nominal} ({sugerido.d_interior_mm} mm)",
            formula="V_real = 4·Q / (π·D_com²) | hf_real = 10,67·L·Q^1,852 / (C^1,852·D_com^4,87)",
            sustitucion=f"D_com = {sugerido.d_interior_mm} mm -> V_real = {fmt_es(v_com, 2)} m/s",
            resultado=f"hf = {fmt_es(hf_com_mca, 2)} m.c.a. ({fmt_es(hf_com_bar, 3)} bar)",
            unidad="m.c.a.",
        )
    )

    return ResultadoCalculoDiametro(
        material_nombre=material_info.nombre,
        c_rugosidad=c_hazen,
        longitud_m=datos.longitud_m,
        caudal_l_s=q_l_s,
        caudal_m3_s=q_m3_s,
        criterio_descripcion=criterio_desc,
        d_min_teorico_mm=d_mm_teorico,
        d_min_teorico_pulg=d_pulg_teorico,
        d_min_teorico_m=d_m,
        v_teorica_ms=v_teorica,
        dn_comercial_sugerido=sugerido.dn_nominal,
        d_comercial_mm=sugerido.d_interior_mm,
        d_comercial_pulg=sugerido.pulgadas_aprox,
        v_comercial_ms=v_com,
        estado_v_comercial=est_v,
        mensaje_v_comercial=msg_v,
        clase_css_v_comercial=css_v,
        hf_comercial_mca=hf_com_mca,
        hf_comercial_bar=hf_com_bar,
        j_comercial_m_100m=j_com_m_m * 100.0,
        pasos_memoria=pasos,
    )
