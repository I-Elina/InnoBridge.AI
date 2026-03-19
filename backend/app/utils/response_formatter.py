from typing import Any


def success_response(data: Any, message: str = "Success") -> dict:
    return {
        "status": "success",
        "message": message,
        "data": data,
    }


def error_response(message: str, code: int = 400) -> dict:
    return {
        "status": "error",
        "message": message,
        "code": code,
        "data": None,
    }