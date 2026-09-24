"""App-level errors. The API layer turns these into HTTP responses (see app/api/main.py)."""


class AppError(Exception):
    status_code = 400

    def __init__(self, message: str = ""):
        super().__init__(message)
        self.message = message


class NotFoundError(AppError):
    status_code = 404


class ConflictError(AppError):
    status_code = 409


class AuthError(AppError):
    status_code = 401


class ValidationError(AppError):
    status_code = 422

    def __init__(self, errors: dict):
        super().__init__("; ".join(f"{k}: {v}" for k, v in errors.items()))
        self.errors = errors


class ForbiddenError(AppError):
    status_code = 403
