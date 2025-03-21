import pytest
from app import create_app
from app.extensions import db
from alembic import command
from alembic.config import Config as AlembicConfig
import time
import os


@pytest.fixture(scope="session")
def test_app():
    """
    Creates a Flask app in testing mode, configures DB, runs migrations.
    """
    os.environ["FLASK_ENV"] = "testing"
    app = create_app("testing")

    with app.app_context():
        # Pre-populate a valid token to bypass refresh during tests.
        app.config["HUBSPOT_ACCESS_TOKEN"] = "DUMMY_TOKEN"
        app.config["HUBSPOT_TOKEN_EXPIRES_AT"] = (
            int(time.time()) + 3600
        )  # valid for one hour
        # Run Alembic migrations
        alembic_cfg = AlembicConfig("alembic.ini")
        command.upgrade(alembic_cfg, "head")

        yield app

        # Optionally downgrade or drop tables after tests
        command.downgrade(alembic_cfg, "base")


@pytest.fixture(scope="function")
def test_client(test_app):
    """
    Returns a Flask test client.
    """
    with test_app.test_client() as client:
        yield client


@pytest.fixture(scope="function")
def db_session(test_app):
    """
    Returns a database session for the test. Rolls back after each test.
    """
    with test_app.app_context():
        connection = db.engine.connect()
        transaction = connection.begin()

        session = db.session

        yield session

        session.rollback()
        transaction.rollback()
        connection.close()
