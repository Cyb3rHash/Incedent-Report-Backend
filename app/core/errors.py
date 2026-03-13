from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class ApiErrorPayload:
    """Structured error payload returned to API clients."""

    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class AppError(Exception):
    """Base class for application errors (domain/service level)."""

    def __init__(self, code: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details


class NotFoundError(AppError):
    """Raised when an entity cannot be found."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(code="NOT_FOUND", message=message, details=details)


class ConflictError(AppError):
    """Raised when an operation conflicts with current state."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(code="CONFLICT", message=message, details=details)


class DatabaseError(AppError):
    """Raised when database operations fail in a known way."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(code="DATABASE_ERROR", message=message, details=details)
