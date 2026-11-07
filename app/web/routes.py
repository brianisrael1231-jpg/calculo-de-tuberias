"""Controlador web para el procedimiento simplificado de Hazen-Williams.

Maneja los datos de entrada:
- Uso previsto de la cañería (sugiere el material automáticamente)
- Longitud (m)
- Diámetro (mm o pulgadas)
- Caudal (L/s o m³/s)
- Material (precargado por el uso, editable por el usuario)

Arquitectura STATELESS: sin almacenamiento en disco, base de datos ni cookies.
"""

import os
from typing import Any, Dict, List, Optional
from flask import Blueprint, render_template, request

from app.config import DIAMETROS_COMERCIALES, MATERIALES_CATALOGO, RENDERS_MATERIAL, USOS_CATALOGO
from app.core.hydraulics import calcular_diametro_necesario, fmt_es, procesar_calculo_hidraulico
from app.core.models import DatosEntrada, DatosEntradaDiametro

web_bp = Blueprint("web", __name__, template_folder="templates", static_folder="static")

_STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")


def _renders_disponibles() -> Dict[str, Dict[str, Any]]:
    """Devuelve info de render por material, indicando si el archivo de imagen existe."""
    salida: Dict[str, Dict[str, Any]] = {}
    for mat_id, r in RENDERS_MATERIAL.items():
        existe = os.path.isfile(os.path.join(_STATIC_DIR, *r.archivo.split("/")))
        salida[mat_id] = {
            "archivo": r.archivo if existe else "img/pvc.jpg",
            "imagen_rel_path": r.archivo if existe else "img/pvc.jpg",
            "diametro_ilustrado": r.diametro_ilustrado,
            "suelo_ilustrado": r.suelo_ilustrado,
        }
    return salida


def _parsear_float_positivo(val: Optional[str], nombre_campo: str) -> float:
    if val is None or not str(val).strip():
        raise ValueError(f"El campo '{nombre_campo}' es obligatorio.")
    cadena = str(val).strip().replace(" ", "").replace(",", ".")
    try:
        numero = float(cadena)
    except ValueError:
        raise ValueError(f"El valor '{val}' ingresado en '{nombre_campo}' no es un número válido.")
    if numero <= 0:
        raise ValueError(f"El campo '{nombre_campo}' debe ser estrictamente mayor a cero.")
    return numero


@web_bp.app_template_filter("formato_es")
def filtro_formato_es(valor: Any, decimales: int = 2) -> str:
    if valor is None:
        return "-"
    try:
        return fmt_es(float(valor), decimales)
    except (ValueError, TypeError):
        return str(valor)


@web_bp.route("/", methods=["GET", "POST"])
def index():
    """Pantalla principal con formulario y presentación inmediata de resultados."""
    errores: List[str] = []
    resultado = None

    # Valores por defecto para precargar el formulario
    valores_form = {
        "uso_id": "red_domiciliaria",
        "longitud_m": "100",
        "diametro_valor": "75",
        "diametro_unidad": "mm",
        "caudal_valor": "5",
        "caudal_unidad": "l_s",
        "material_id": "pvc",
    }

    if request.method == "POST":
        try:
            uso_id = request.form.get("uso_id", "").strip()
            longitud_str = request.form.get("longitud_m", "")
            diametro_str = request.form.get("diametro_valor", "")
            diametro_uni = request.form.get("diametro_unidad", "mm").strip()
            caudal_str = request.form.get("caudal_valor", "")
            caudal_uni = request.form.get("caudal_unidad", "l_s").strip()
            material_id = request.form.get("material_id", "pvc").strip()

            # Guardar valores para mantener en el formulario tras el POST
            valores_form = {
                "uso_id": uso_id,
                "longitud_m": longitud_str,
                "diametro_valor": diametro_str,
                "diametro_unidad": diametro_uni,
                "caudal_valor": caudal_str,
                "caudal_unidad": caudal_uni,
                "material_id": material_id,
            }

            longitud_m = _parsear_float_positivo(longitud_str, "Longitud del tramo")
            diametro_val = _parsear_float_positivo(diametro_str, "Diámetro del caño")
            caudal_val = _parsear_float_positivo(caudal_str, "Caudal requerido")

            datos_in = DatosEntrada(
                longitud_m=longitud_m,
                diametro_valor=diametro_val,
                diametro_unidad=diametro_uni,
                caudal_valor=caudal_val,
                caudal_unidad=caudal_uni,
                material_id=material_id,
            )

            resultado = procesar_calculo_hidraulico(datos_in)

        except ValueError as ex:
            errores.append(str(ex))
        except Exception:
            errores.append("Ocurrió un error inesperado al procesar los cálculos.")

    else:
        # En GET inicial, calculamos con los valores por defecto
        try:
            datos_default = DatosEntrada(
                longitud_m=float(valores_form["longitud_m"]),
                diametro_valor=float(valores_form["diametro_valor"]),
                diametro_unidad=valores_form["diametro_unidad"],
                caudal_valor=float(valores_form["caudal_valor"]),
                caudal_unidad=valores_form["caudal_unidad"],
                material_id=valores_form["material_id"],
            )
            resultado = procesar_calculo_hidraulico(datos_default)
        except Exception:
            resultado = None

    return render_template(
        "index.html",
        materiales=MATERIALES_CATALOGO,
        usos=USOS_CATALOGO,
        renders=_renders_disponibles(),
        valores=valores_form,
        resultado=resultado,
        errores=errores,
    )


@web_bp.route("/diametro", methods=["GET", "POST"])
def diametro():
    """Pantalla para calcular y dimensionar el diámetro necesario de una cañería."""
    errores: List[str] = []
    resultado = None

    valores_form = {
        "uso_id": "red_domiciliaria",
        "caudal_valor": "10",
        "caudal_unidad": "l_s",
        "longitud_m": "150",
        "material_id": "pvc",
        "criterio_tipo": "perdida_mca",
        "criterio_valor": "3.0",
    }

    if request.method == "POST":
        try:
            uso_id = request.form.get("uso_id", "").strip()
            caudal_str = request.form.get("caudal_valor", "")
            caudal_uni = request.form.get("caudal_unidad", "l_s").strip()
            longitud_str = request.form.get("longitud_m", "")
            material_id = request.form.get("material_id", "pvc").strip()
            criterio_tipo = request.form.get("criterio_tipo", "perdida_mca").strip()
            criterio_str = request.form.get("criterio_valor", "")

            valores_form = {
                "uso_id": uso_id,
                "caudal_valor": caudal_str,
                "caudal_unidad": caudal_uni,
                "longitud_m": longitud_str,
                "material_id": material_id,
                "criterio_tipo": criterio_tipo,
                "criterio_valor": criterio_str,
            }

            caudal_val = _parsear_float_positivo(caudal_str, "Caudal de diseño")
            longitud_m = _parsear_float_positivo(longitud_str, "Longitud del tramo")
            criterio_val = _parsear_float_positivo(criterio_str, "Valor límite del criterio")

            datos_in = DatosEntradaDiametro(
                caudal_valor=caudal_val,
                caudal_unidad=caudal_uni,
                longitud_m=longitud_m,
                material_id=material_id,
                criterio_tipo=criterio_tipo,
                criterio_valor=criterio_val,
            )

            resultado = calcular_diametro_necesario(datos_in)

        except ValueError as ex:
            errores.append(str(ex))
        except Exception:
            errores.append("Ocurrió un error inesperado al procesar el dimensionamiento del diámetro.")

    else:
        # En GET inicial, calculamos con los valores por defecto
        try:
            datos_default = DatosEntradaDiametro(
                caudal_valor=float(valores_form["caudal_valor"]),
                caudal_unidad=valores_form["caudal_unidad"],
                longitud_m=float(valores_form["longitud_m"]),
                material_id=valores_form["material_id"],
                criterio_tipo=valores_form["criterio_tipo"],
                criterio_valor=float(valores_form["criterio_valor"]),
            )
            resultado = calcular_diametro_necesario(datos_default)
        except Exception:
            resultado = None

    return render_template(
        "diametro.html",
        materiales=MATERIALES_CATALOGO,
        usos=USOS_CATALOGO,
        diametros_comerciales=DIAMETROS_COMERCIALES,
        renders=_renders_disponibles(),
        valores=valores_form,
        resultado=resultado,
        errores=errores,
    )
