import logging
import sys
from pythonjsonlogger import jsonlogger

def configure_logging(log_level="INFO"):
    """
    Configures Python's logging library to emit JSON-formatted logs.
    """
    # Creating a stream handler that writes to stdout
    log_handler = logging.StreamHandler(sys.stdout)

    # Defining a JSON formatter with python-json-logger
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s'
    )
    log_handler.setFormatter(formatter)

    # Setting up the root logger
    logging.basicConfig(
        level=log_level,
        handlers=[log_handler]
    )

    logging.getLogger("flask.app").setLevel(log_level)
    logging.getLogger("werkzeug").setLevel(log_level)

    logging.info("Structured logging is now configured.")
