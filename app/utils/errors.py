"""
errors.py

Custom error classes inheriting from BaseError for unified error handling.
"""

import logging
from .constants import (
    InternalServerErrorMessage,
    unprocessableEntityErrorMessage,
    operationForbiddenErrorMessage,
    notFoundErrorMessage,
    unauthorizedErrorMessage,
    badRequestErrorMessage,
    serviceUnavailableErrorMessage,
    statusCodes,
    errorTypes,
)


class BaseError(Exception):
    """
    BaseError with logging, carrying a message, verboseMessage, errorType, and httpCode.
    """

    def __init__(
        self, message: str, verboseMessage=None, errorType=None, httpCode=None
    ):
        self.message = message or InternalServerErrorMessage
        self.verboseMessage = verboseMessage
        self.errorType = errorType or errorTypes["INTERNAL_SERVER_ERROR"]
        self.httpCode = httpCode or statusCodes["500"]

        logging.error(self.message)
        super().__init__(self.message)


class UnprocessableEntityError(BaseError):
    def __init__(self, message=None, verboseMessage=None, errorType=None):
        super().__init__(
            message=message or unprocessableEntityErrorMessage,
            httpCode=statusCodes["422"],
            errorType=errorType or errorTypes["UNPROCESSABLE_ENTITY"],
            verboseMessage=verboseMessage,
        )


class OperationForbiddenError(BaseError):
    def __init__(self, message=None, verboseMessage=None, errorType=None):
        super().__init__(
            message=message or operationForbiddenErrorMessage,
            httpCode=statusCodes["403"],
            errorType=errorType or errorTypes["OPERATION_FORBIDDEN"],
            verboseMessage=verboseMessage,
        )


class NotFoundError(BaseError):
    def __init__(self, message=None, verboseMessage=None, errorType=None):
        super().__init__(
            message=message or notFoundErrorMessage,
            httpCode=statusCodes["404"],
            errorType=errorType or errorTypes["NOT_FOUND_ERROR"],
            verboseMessage=verboseMessage,
        )


class UnauthorizedError(BaseError):
    def __init__(self, message=None, verboseMessage=None):
        super().__init__(
            message=message or unauthorizedErrorMessage,
            verboseMessage=verboseMessage,
            httpCode=statusCodes["401"],
            errorType=errorTypes["UNAUTHORIZED_ACCESS"],
        )


class BadRequestError(BaseError):
    def __init__(self, message=None, verboseMessage=None):
        super().__init__(
            message=message or badRequestErrorMessage,
            verboseMessage=verboseMessage,
            httpCode=statusCodes["400"],
            errorType=errorTypes["BAD_REQUEST"],
        )


class ServiceUnavailableError(BaseError):
    def __init__(self, message=None, verboseMessage=None):
        super().__init__(
            message=message or serviceUnavailableErrorMessage,
            verboseMessage=verboseMessage,
            httpCode=statusCodes["503"],
            errorType=errorTypes["SERVICE_UNAVAILABLE"],
        )


class RateLimitExceededError(BaseError):
    """
    Specialized error for repeated 429 rate limit exhaustion.
    """

    def __init__(self, message=None, verboseMessage=None):
        super().__init__(
            message=message or "Rate limit exceeded. Please try again later.",
            verboseMessage=verboseMessage,
            httpCode=statusCodes["429"] if "429" in statusCodes else 429,
            errorType="RATE_LIMIT_EXCEEDED",
        )
