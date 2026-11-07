"""Módulo de configuración y constantes para el cálculo de Hazen-Williams.

Incluye la tabla de materiales con coeficientes C y la tabla de usos típicos
que permite al programa sugerir automáticamente el material más adecuado.
"""

from dataclasses import dataclass
from typing import Dict, List

# Factores de conversión físicos
PULGADA_A_METROS: float = 0.0254  # 1 pulgada = 25.4 mm = 0.0254 m
PULGADA_A_MM: float = 25.4
BAR_A_MCA: float = 10.19716  # 1 bar = 10.19716 m.c.a. (100 kPa / 9.80665)
MCA_A_BAR: float = 0.0980665  # 1 m.c.a. = 0.0980665 bar


@dataclass(frozen=True)
class MaterialConfig:
    id: str
    nombre: str
    c_hazen_williams: float
    c_rango: str  # Texto descriptivo del rango (ej. "140 - 150")
    descripcion: str


@dataclass(frozen=True)
class UsoConfig:
    """Mapeo de un uso típico de cañería al material recomendado."""
    id: str
    nombre_uso: str
    material_recomendado_id: str
    explicacion: str


# ──────────────────────────────────────────────────────────────────────
# TABLA DE MATERIALES Y COEFICIENTES C DE HAZEN-WILLIAMS
# ──────────────────────────────────────────────────────────────────────
MATERIALES_CATALOGO: Dict[str, MaterialConfig] = {
    "pvc": MaterialConfig(
        id="pvc",
        nombre="PVC (Policloruro de Vinilo)",
        c_hazen_williams=150.0,
        c_rango="150",
        descripcion="Muy utilizado en redes domiciliarias y urbanas modernas.",
    ),
    "polietileno": MaterialConfig(
        id="polietileno",
        nombre="Polietileno de Alta Densidad (PEAD)",
        c_hazen_williams=140.0,
        c_rango="140 - 150",
        descripcion="Usado en acueductos y conexiones flexibles.",
    ),
    "acero": MaterialConfig(
        id="acero",
        nombre="Acero / Hierro Galvanizado",
        c_hazen_williams=120.0,
        c_rango="120 - 130",
        descripcion="Conducciones metálicas de alta presión.",
    ),
    "hierro_fundido": MaterialConfig(
        id="hierro_fundido",
        nombre="Hierro Fundido (Dúctil)",
        c_hazen_williams=130.0,
        c_rango="130",
        descripcion="Redes de distribución troncal de agua potable.",
    ),
    "hormigon": MaterialConfig(
        id="hormigon",
        nombre="Hormigón / Cemento",
        c_hazen_williams=120.0,
        c_rango="120",
        descripcion="Grandes colectores, desagües o acueductos antiguos.",
    ),
}


# ──────────────────────────────────────────────────────────────────────
# TABLA DE USOS TÍPICOS → MATERIAL RECOMENDADO
# El usuario elige el uso y el programa le propone el material adecuado.
# ──────────────────────────────────────────────────────────────────────
USOS_CATALOGO: List[UsoConfig] = [
    UsoConfig(
        id="red_domiciliaria",
        nombre_uso="Redes domiciliarias y urbanas modernas",
        material_recomendado_id="pvc",
        explicacion="El PVC (C = 150) es el material más utilizado por su baja rugosidad, resistencia química y costo accesible.",
    ),
    UsoConfig(
        id="acueducto_flexible",
        nombre_uso="Acueductos y conexiones flexibles",
        material_recomendado_id="polietileno",
        explicacion="El PEAD (C = 140 - 150) ofrece flexibilidad, resistencia a la corrosión y facilidad de instalación en terrenos irregulares.",
    ),
    UsoConfig(
        id="alta_presion",
        nombre_uso="Conducciones metálicas de alta presión",
        material_recomendado_id="acero",
        explicacion="El Acero / Hierro Galvanizado (C = 120 - 130) soporta altas presiones de trabajo y es ideal para conducciones industriales.",
    ),
    UsoConfig(
        id="red_troncal",
        nombre_uso="Redes de distribución troncal de agua potable",
        material_recomendado_id="hierro_fundido",
        explicacion="El Hierro Fundido Dúctil (C = 130) es la opción clásica para redes principales urbanas de agua potable por su durabilidad.",
    ),
    UsoConfig(
        id="colector_desague",
        nombre_uso="Grandes colectores, desagües o acueductos antiguos",
        material_recomendado_id="hormigon",
        explicacion="El Hormigón / Cemento (C = 120) se emplea en conducciones de gran diámetro y en infraestructura existente de larga vida útil.",
    ),
]


# ──────────────────────────────────────────────────────────────────────
# RENDERS ILUSTRATIVOS DE INSTALACIÓN EN ZANJA (uno por material)
# Imágenes estáticas en app/web/static/img/. Son ilustrativas: el diámetro
# y el tipo de suelo representados son los típicos de cada material.
# ──────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class RenderConfig:
    archivo: str
    diametro_ilustrado: str
    suelo_ilustrado: str

    @property
    def imagen_rel_path(self) -> str:
        """Alias para compatibilidad con plantillas web."""
        return self.archivo


RENDERS_MATERIAL: Dict[str, RenderConfig] = {
    "pvc": RenderConfig("img/pvc.jpg", "110 mm", "Arcilloso / tierra común"),
    "polietileno": RenderConfig("img/polietileno.jpg", "160 mm", "Arenoso"),
    "acero": RenderConfig("img/acero.jpg", "100 mm (4\")", "Rocoso / grava"),
    "hierro_fundido": RenderConfig("img/hierro_fundido.jpg", "200 mm", "Arcilloso compacto (bajo calzada)"),
    "hormigon": RenderConfig("img/hormigon.jpg", "600 mm", "Limoso / húmedo"),
}


# Rangos recomendados de velocidad de flujo en tuberías de agua
VELOCIDAD_MIN_OPTIMA: float = 0.60  # m/s (evita sedimentación de sólidos)
VELOCIDAD_MAX_OPTIMA: float = 2.00  # m/s (evita erosión interna, ruidos y sobrepresiones)


# ──────────────────────────────────────────────────────────────────────
# DIÁMETROS COMERCIALES ESTÁNDAR
# Catálogo de diámetros nominales comunes para sugerir el caño comercial
# inmediatamente superior al diámetro teórico requerido.
# ──────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class DiametroComercial:
    dn_nominal: str
    d_interior_mm: float
    pulgadas_aprox: str


DIAMETROS_COMERCIALES: List[DiametroComercial] = [
    DiametroComercial("DN 25", 25.0, "1\""),
    DiametroComercial("DN 32", 32.0, "1 1/4\""),
    DiametroComercial("DN 40", 40.0, "1 1/2\""),
    DiametroComercial("DN 50", 50.0, "2\""),
    DiametroComercial("DN 63", 63.0, "2 1/2\""),
    DiametroComercial("DN 75", 75.0, "3\""),
    DiametroComercial("DN 90", 90.0, "3 1/2\""),
    DiametroComercial("DN 110", 110.0, "4\""),
    DiametroComercial("DN 125", 125.0, "5\""),
    DiametroComercial("DN 140", 140.0, "5 1/2\""),
    DiametroComercial("DN 160", 160.0, "6\""),
    DiametroComercial("DN 200", 200.0, "8\""),
    DiametroComercial("DN 250", 250.0, "10\""),
    DiametroComercial("DN 315", 315.0, "12\""),
    DiametroComercial("DN 400", 400.0, "16\""),
    DiametroComercial("DN 500", 500.0, "20\""),
    DiametroComercial("DN 600", 600.0, "24\""),
    DiametroComercial("DN 800", 800.0, "32\""),
]
