# app/config.py

import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_FILE = os.path.join(BASE_DIR, ".env")

load_dotenv(ENV_FILE)  # Load variables from .env if present


class BaseConfig:
    DEBUG = False
    TESTING = False
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

    # Database
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = os.environ.get("DB_PORT", "5432")
    DB_USER = os.environ.get("DB_USER", "postgres")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "postgres")
    DB_NAME = os.environ.get("DB_NAME", "hubspot_crm_db")
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Hubspot Rate Limit
    HUBSPOT_MAX_RETRIES = int(os.environ.get("HUBSPOT_MAX_RETRIES", 3))
    HUBSPOT_BACKOFF_FACTOR = float(os.environ.get("HUBSPOT_BACKOFF_FACTOR", 2.0))
    HUBSPOT_BACKOFF_MULTIPLIER = float(
        os.environ.get("HUBSPOT_BACKOFF_MULTIPLIER", 1.0)
    )

    # HubSpot OAuth
    HUBSPOT_CLIENT_ID = os.environ.get("HUBSPOT_CLIENT_ID", "")
    HUBSPOT_CLIENT_SECRET = os.environ.get("HUBSPOT_CLIENT_SECRET", "")
    HUBSPOT_REFRESH_TOKEN = os.environ.get("HUBSPOT_REFRESH_TOKEN", "")
    HUBSPOT_OAUTH_TOKEN_URL = "https://api.hubapi.com/oauth/v1/token"
    HUBSPOT_API_BASE_URL = "https://api.hubapi.com"

    # Local in-memory store of the currently valid access token
    HUBSPOT_ACCESS_TOKEN = None
    HUBSPOT_TOKEN_EXPIRES_AT = float(os.environ.get("HUBSPOT_TOKEN_EXPIRES_AT", 0))
    TOKEN_REFRESH_BUFFER = float(os.environ.get("TOKEN_REFRESH_BUFFER", 60))


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class TestingConfig(BaseConfig):
    TESTING = True
    TEST_DB_NAME = os.environ.get("TEST_DB_NAME", "hubspot_crm_db_test")
    SQLALCHEMY_DATABASE_URI = f"postgresql://{BaseConfig.DB_USER}:{BaseConfig.DB_PASSWORD}@{BaseConfig.DB_HOST}:{BaseConfig.DB_PORT}/{TEST_DB_NAME}"


class ProductionConfig(BaseConfig):
    # Potentially override with production DB credentials
    pass


def load_config(env_name=None):
    env = env_name or os.environ.get("FLASK_ENV", "development")
    if env == "production":
        return ProductionConfig()
    elif env == "testing":
        return TestingConfig()
    else:
        return DevelopmentConfig()
