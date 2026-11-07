"""Punto de entrada para la aplicación web de cálculo Hazen-Williams.

Ejecución local:
  python run.py
"""

import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=puerto, debug=False)
