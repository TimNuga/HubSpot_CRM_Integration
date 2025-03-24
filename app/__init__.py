import logging
from flask import Flask, jsonify
from flask_swagger_ui import get_swaggerui_blueprint

from .config import load_config
from .routes import register_routes
from .utils.errors import (
    BaseError,
    NotFoundError,
    UnauthorizedError,
    OperationForbiddenError,
    BadRequestError,
    ServiceUnavailableError,
    UnprocessableEntityError,
)
from .utils.api_responses import error_response
from .extensions import db, migrate


def create_app(env_name=None):
    """
    Application factory pattern:
    - Loads configuration from environment
    - Initializes Flask extensions
    - Registers blueprints
    """
    app = Flask(__name__)
    config_obj = load_config(env_name)
    app.config.from_object(config_obj)

    # Initialize DB + Migrations
    db.init_app(app)
    migrate.init_app(app, db)

    # Configure global logging
    logging.basicConfig(
        level=app.config["LOG_LEVEL"].upper(),
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )

    # Register all routes
    register_routes(app)

    SWAGGER_URL = "/api/docs"
    API_URL = "/static/openapi.yaml"
    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL, API_URL, config={"app_name": "HubSpot CRM Integration API"}
    )
    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

    @app.errorhandler(BaseError)
    def handle_base_error(error):
        """
        Catch any custom BaseError and return a standard error response.
        """
        app.logger.error(
            f"BaseError: {error.message} (type={error.errorType}, http={error.httpCode})"
        )
        resp = error_response(
            error=error.message,
            message=error.verboseMessage or error.message,
            status_code=error.httpCode,
        )
        return jsonify(resp), error.httpCode

    @app.errorhandler(Exception)
    def handle_unexpected_exception(error):
        """
        Catch any unexpected exceptions (e.g., unhandled).
        """
        app.logger.exception("Unhandled exception occurred.")
        resp = error_response(
            error="Internal Server Error",
            message="An unexpected error occurred. Please try again later.",
            status_code=500,
        )
        return jsonify(resp), 500

    return app
