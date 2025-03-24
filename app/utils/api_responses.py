"""
api_responses.py

Standardized JSON response structures.
"""

from typing import Any, Dict


def success_response(
    data: Any, message: str = "Request successful", status_code: int = 200
) -> Dict[str, Any]:
    return {
        "success": True,
        "message": message,
        "data": data,
        "status_code": status_code,
    }


def error_response(
    error: Any, message: str = "An error occurred", status_code: int = 400
) -> Dict[str, Any]:
    return {
        "success": False,
        "message": message,
        "error": error,
        "status_code": status_code,
    }
