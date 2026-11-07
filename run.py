"""Punto de entrada para la aplicación web de cálculo Hazen-Williams.

Ejecución local:
  python run.py
"""

import os
import sys

# Asegurar que el directorio actual y cualquier subcarpeta que contenga 'app' estén en el sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Si se subió dentro de una subcarpeta por error (ej. FUNDAMENTOS DE LA INFORMATICA/app)
for root, dirs, _ in os.walk(BASE_DIR):
    if "app" in dirs and os.path.isfile(os.path.join(root, "app", "__init__.py")):
        if root not in sys.path:
            sys.path.insert(0, root)
        break

from app import create_app

app = create_app()

if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=puerto, debug=False)
