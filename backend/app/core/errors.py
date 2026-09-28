class AppError(Exception):
    """Base class for errors that should surface a friendly message to the UI."""

    status_code: int = 400

    def __init__(self, message: str, *, detail: str | None = None):
        super().__init__(message)
        self.message = message
        self.detail = detail


class NotFoundError(AppError):
    status_code = 404


class ValidationAppError(AppError):
    status_code = 422


class ConflictError(AppError):
    status_code = 409


class StorageError(AppError):
    status_code = 502


class ModelNotConfiguredError(AppError):
    status_code = 400


class VisionProviderError(AppError):
    """Raised by a VisionModelProvider for auth/rate-limit/timeout/bad-response cases."""

    status_code = 502

    def __init__(self, message: str, *, detail: str | None = None, status_code: int | None = None):
        super().__init__(message, detail=detail)
        if status_code is not None:
            self.status_code = status_code
