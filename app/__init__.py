"""Aplicación Web para Cálculo y Verificación de Pérdidas de Carga con Hazen-Williams.

Arquitectura Stateless sin almacenamiento persistente, cookies de sesión ni telemetría.
"""

from flask import Flask


def create_app() -> Flask:
    """Fábrica de la aplicación Flask."""
    app = Flask(__name__, static_folder="web/static", static_url_path="/static")

    # Configuración estricta de seguridad y sin persistencia de sesiones
    app.config["SESSION_COOKIE_SECURE"] = True
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Strict"
    app.config["SECRET_KEY"] = "ephemeral-stateless-key"

    # Registrar Blueprint web
    from app.web.routes import web_bp
    app.register_blueprint(web_bp)

    @app.after_request
    def set_security_and_stateless_headers(response):
        """Asegura que el navegador no almacene en caché datos de cálculo y aplica cabeceras de seguridad."""
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "img-src 'self' data:; "
            "font-src 'self' https://cdn.jsdelivr.net;"
        )
        return response

    return app
