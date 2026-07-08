class SentinelError(Exception):
    code = "SENTINEL_ERROR"
    status_code = 500

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class NotFoundError(SentinelError):
    code = "NOT_FOUND"
    status_code = 404


class ValidationError(SentinelError):
    code = "VALIDATION_ERROR"
    status_code = 400
