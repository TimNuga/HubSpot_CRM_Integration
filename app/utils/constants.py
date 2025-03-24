"""
constants.py

Contains global constants and enumerations used in error classes,
statuses, etc.
"""

# HTTP Status Codes
statusCodes = {
    "400": 400,
    "401": 401,
    "403": 403,
    "404": 404,
    "422": 422,
    "500": 500,
    "503": 503,
    # Not officially in standard but used for RateLimitExceededError:
    "429": 429,
}

errorTypes = {
    "BAD_REQUEST": "BAD_REQUEST",
    "UNAUTHORIZED_ACCESS": "UNAUTHORIZED_ACCESS",
    "OPERATION_FORBIDDEN": "OPERATION_FORBIDDEN",
    "NOT_FOUND_ERROR": "NOT_FOUND_ERROR",
    "UNPROCESSABLE_ENTITY": "UNPROCESSABLE_ENTITY",
    "INTERNAL_SERVER_ERROR": "INTERNAL_SERVER_ERROR",
    "SERVICE_UNAVAILABLE": "SERVICE_UNAVAILABLE",
}

# Default error messages
InternalServerErrorMessage = "An internal server error occurred."
unprocessableEntityErrorMessage = "Request is unprocessable."
operationForbiddenErrorMessage = "Operation forbidden."
notFoundErrorMessage = "Resource not found."
unauthorizedErrorMessage = "Unauthorized."
badRequestErrorMessage = "Bad request."
serviceUnavailableErrorMessage = "Service is currently unavailable."

VALID_CATEGORIES = [
    "general_inquiry",
    "technical_issue",
    "billing",
    "service_request",
    "meeting",
]
