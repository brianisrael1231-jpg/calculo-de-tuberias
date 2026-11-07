"""Generador SVG para el perfil hidráulico (Línea Piezométrica y Línea de Energía).

Genera un SVG vectorial puro, responsivo y sin dependencias externas, completamente
stateless y optimizado para visualización web e impresión en alta resolución.
"""

from typing import List
from app.core.models import PuntoPerfilHidraulico
from app.core.hydraulics import fmt_es


def generar_svg_perfil_hidraulico(puntos: List[PuntoPerfilHidraulico]) -> str:
    """Construye un documento SVG en formato string para el perfil hidráulico."""
    if not puntos or len(puntos) < 2:
        return (
            "<svg viewBox='0 0 800 200' class='img-fluid border rounded bg-light p-3' "
            "xmlns='http://www.w3.org/2000/svg'>"
            "<text x='400' y='100' text-anchor='middle' fill='#6c757d' font-family='sans-serif'>"
            "Información insuficiente para trazar el perfil hidráulico."
            "</text></svg>"
        )

    # Dimensiones y márgenes del gráfico
    width = 850
    height = 420
    margin_left = 80
    margin_right = 50
    margin_top = 50
    margin_bottom = 60

    plot_w = width - margin_left - margin_right
    plot_h = height - margin_top - margin_bottom

    # Rango en X (Distancia)
    x_min = 0.0
    x_max = max(p.distancia_acumulada_m for p in puntos)
    if x_max <= 0:
        x_max = 100.0

    # Rango en Y (Cotas y Presiones)
    todos_y = []
    for p in puntos:
        todos_y.extend([p.cota_terreno_m, p.piezometrica_cota_m, p.energia_cota_m])

    y_min_val = min(todos_y)
    y_max_val = max(todos_y)

    # Añadir margen vertical de 10%
    delta_y = y_max_val - y_min_val
    if delta_y < 1.0:
        delta_y = 5.0
    y_min = y_min_val - (delta_y * 0.12)
    y_max = y_max_val + (delta_y * 0.15)

    def to_svg_x(val_x: float) -> float:
        return margin_left + ((val_x - x_min) / (x_max - x_min)) * plot_w

    def to_svg_y(val_y: float) -> float:
        return margin_top + plot_h - (((val_y - y_min) / (y_max - y_min)) * plot_h)

    # Generar rejilla horizontal (eje Y)
    lineas_grid = []
    num_divisiones_y = 5
    for i in range(num_divisiones_y + 1):
        vy = y_min + (i / num_divisiones_y) * (y_max - y_min)
        sy = to_svg_y(vy)
        lineas_grid.append(
            f"<line x1='{margin_left}' y1='{sy:.1f}' x2='{width - margin_right}' y2='{sy:.1f}' "
            f"stroke='#e9ecef' stroke-width='1' stroke-dasharray='4' />"
        )
        lineas_grid.append(
            f"<text x='{margin_left - 10}' y='{sy + 4:.1f}' text-anchor='end' "
            f"font-size='11' fill='#6c757d' font-family='sans-serif'>{fmt_es(vy, 1)} m</text>"
        )

    # Generar rejilla vertical (eje X)
    num_divisiones_x = 5
    for i in range(num_divisiones_x + 1):
        vx = x_min + (i / num_divisiones_x) * (x_max - x_min)
        sx = to_svg_x(vx)
        lineas_grid.append(
            f"<line x1='{sx:.1f}' y1='{margin_top}' x2='{sx:.1f}' y2='{margin_top + plot_h}' "
            f"stroke='#e9ecef' stroke-width='1' stroke-dasharray='4' />"
        )
        lineas_grid.append(
            f"<text x='{sx:.1f}' y='{margin_top + plot_h + 20}' text-anchor='middle' "
            f"font-size='11' fill='#6c757d' font-family='sans-serif'>{fmt_es(vx, 0)} m</text>"
        )

    # Polilíneas
    pts_energia = [f"{to_svg_x(p.distancia_acumulada_m):.1f},{to_svg_y(p.energia_cota_m):.1f}" for p in puntos]
    pts_piez = [f"{to_svg_x(p.distancia_acumulada_m):.1f},{to_svg_y(p.piezometrica_cota_m):.1f}" for p in puntos]
    pts_terreno = [f"{to_svg_x(p.distancia_acumulada_m):.1f},{to_svg_y(p.cota_terreno_m):.1f}" for p in puntos]

    # Área sombreada entre piezométrica y terreno (presión neta positiva)
    poly_presion_pts = list(pts_piez)
    for p in reversed(puntos):
        poly_presion_pts.append(f"{to_svg_x(p.distancia_acumulada_m):.1f},{to_svg_y(p.cota_terreno_m):.1f}")

    str_poly_presion = " ".join(poly_presion_pts)
    str_pts_energia = " ".join(pts_energia)
    str_pts_piez = " ".join(pts_piez)
    str_pts_terreno = " ".join(pts_terreno)

    # Nodos y marcas
    nodos_svg = []
    for p in puntos:
        sx = to_svg_x(p.distancia_acumulada_m)
        sy_piez = to_svg_y(p.piezometrica_cota_m)
        sy_ene = to_svg_y(p.energia_cota_m)
        sy_terr = to_svg_y(p.cota_terreno_m)

        # Círculo Piezométrica
        nodos_svg.append(
            f"<circle cx='{sx:.1f}' cy='{sy_piez:.1f}' r='4' fill='#0d6efd' stroke='#fff' stroke-width='1.5' />"
        )
        # Círculo Energía
        nodos_svg.append(
            f"<circle cx='{sx:.1f}' cy='{sy_ene:.1f}' r='3' fill='#dc3545' stroke='#fff' stroke-width='1' />"
        )
        # Círculo Terreno
        nodos_svg.append(
            f"<circle cx='{sx:.1f}' cy='{sy_terr:.1f}' r='3.5' fill='#198754' stroke='#fff' stroke-width='1' />"
        )

    grid_svg = "\n".join(lineas_grid)
    nodos_str = "\n".join(nodos_svg)

    svg = f"""<svg viewBox="0 0 {width} {height}" class="img-fluid border rounded bg-white shadow-sm" xmlns="http://www.w3.org/2000/svg" style="max-height: 480px; width: 100%;">
  <defs>
    <linearGradient id="gradPiez" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#0d6efd" stop-opacity="0.25"/>
      <stop offset="100%" stop-color="#0d6efd" stop-opacity="0.03"/>
    </linearGradient>
  </defs>

  <!-- Título y Ejes -->
  <text x="{width / 2}" y="25" text-anchor="middle" font-size="14" font-weight="bold" fill="#212529" font-family="sans-serif">
    Perfil Hidráulico: Línea de Energía (EGL) y Línea Piezométrica (HGL)
  </text>
  <text x="{margin_left}" y="38" text-anchor="start" font-size="11" font-weight="bold" fill="#495057" font-family="sans-serif">
    Cota / Energía [m.c.a.]
  </text>
  <text x="{width - margin_right}" y="{height - 15}" text-anchor="end" font-size="11" font-weight="bold" fill="#495057" font-family="sans-serif">
    Progresiva longitudinal [m]
  </text>

  <!-- Rejilla de Fondo -->
  {grid_svg}

  <!-- Ejes coordenados principales -->
  <line x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" y2="{margin_top + plot_h}" stroke="#495057" stroke-width="1.5" />
  <line x1="{margin_left}" y1="{margin_top + plot_h}" x2="{width - margin_right}" y2="{margin_top + plot_h}" stroke="#495057" stroke-width="1.5" />

  <!-- Relleno de Presión disponible entre Línea Piezométrica y Terreno -->
  <polygon points="{str_poly_presion}" fill="url(#gradPiez)" />

  <!-- Trazados -->
  <!-- 1. Terreno / Tubería -->
  <polyline points="{str_pts_terreno}" fill="none" stroke="#198754" stroke-width="2.5" stroke-dasharray="3,3" />

  <!-- 2. Línea Piezométrica (HGL) -->
  <polyline points="{str_pts_piez}" fill="none" stroke="#0d6efd" stroke-width="3" />

  <!-- 3. Línea de Energía (EGL) -->
  <polyline points="{str_pts_energia}" fill="none" stroke="#dc3545" stroke-width="2" stroke-dasharray="6,3" />

  <!-- Nodos -->
  {nodos_str}

  <!-- Leyenda Interactiva / Visual -->
  <g transform="translate({margin_left + 15}, {margin_top + 15})">
    <rect x="0" y="0" width="460" height="30" rx="4" fill="#ffffff" fill-opacity="0.9" stroke="#dee2e6" stroke-width="1" />
    <!-- Item Energía -->
    <line x1="12" y1="15" x2="35" y2="15" stroke="#dc3545" stroke-width="2.5" stroke-dasharray="6,3" />
    <circle cx="23.5" cy="15" r="3" fill="#dc3545" />
    <text x="42" y="19" font-size="11" fill="#212529" font-family="sans-serif">Línea de Energía (EGL)</text>

    <!-- Item Piezométrica -->
    <line x1="185" y1="15" x2="208" y2="15" stroke="#0d6efd" stroke-width="3" />
    <circle cx="196.5" cy="15" r="3.5" fill="#0d6efd" />
    <text x="215" y="19" font-size="11" fill="#212529" font-family="sans-serif">Línea Piezométrica (HGL)</text>

    <!-- Item Terreno/Tubería -->
    <line x1="365" y1="15" x2="388" y2="15" stroke="#198754" stroke-width="2.5" stroke-dasharray="3,3" />
    <circle cx="376.5" cy="15" r="3.5" fill="#198754" />
    <text x="395" y="19" font-size="11" fill="#212529" font-family="sans-serif">Tubería / Terreno</text>
  </g>
</svg>"""
    return svg
