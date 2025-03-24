from flask import Blueprint
from .controllers.hubspot_controller import hubspot_bp


def register_routes(app):
    """
    Register application Blueprints here.
    """
    app.register_blueprint(hubspot_bp, url_prefix="/api")
