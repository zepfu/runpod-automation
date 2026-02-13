"""Exception hierarchy for rpctl."""


class RpctlError(Exception):
    """Base exception for all rpctl errors."""

    exit_code: int = 1


class AuthenticationError(RpctlError):
    """API key missing or invalid."""

    exit_code: int = 2

    @property
    def is_transient(self) -> bool:
        return False


class ConfigError(RpctlError):
    """Configuration file missing or malformed."""

    exit_code: int = 3


class ApiError(RpctlError):
    """RunPod API returned an error."""

    exit_code: int = 4
    _TRANSIENT_STATUS_CODES = frozenset({408, 429, 500, 502, 503, 504})

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_body: dict | None = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body

    @property
    def is_transient(self) -> bool:
        """Whether this error is worth retrying."""
        if self.status_code is None:
            return False
        return self.status_code in self._TRANSIENT_STATUS_CODES


class ResourceNotFoundError(ApiError):
    """Requested resource (pod, endpoint, volume) not found."""

    exit_code: int = 5

    @property
    def is_transient(self) -> bool:
        return False


class PresetError(RpctlError):
    """Preset not found or malformed."""

    exit_code: int = 6


class ValidationError(RpctlError):
    """Input validation failed before making API call."""

    exit_code: int = 7
