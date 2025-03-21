import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from .config import load_config
from .logging_config import configure_logging
from flask_swagger_ui import get_swaggerui_blueprint
from .routes.crm import crm_blueprint
from .extensions import db

def create_app(env_name=None):
    """
    Application factory pattern:
    - Loads configuration from environment
    - Initializes Flask extensions
    - Registers blueprints
    """
    app = Flask(__name__)

    # Load config from environment
    config_obj = load_config(env_name)
    app.config.from_object(config_obj)

    # Setup logging
    log_level = app.config.get("LOG_LEVEL", "INFO")
    configure_logging(log_level)

    logging.info("Creating Flask app with environment: %s", env_name)

    # Initialize DB
    db.init_app(app)

    app.register_blueprint(crm_blueprint, url_prefix="/crm")

    SWAGGER_URL = '/api/docs'  
    API_URL = '/openapi.yaml'  
    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={
            'app_name': "HubSpot CRM Integration API"
        }
    )
    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

    return app
