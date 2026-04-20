class SentinelProxyError(Exception):
    """Base application exception."""


class ProviderError(SentinelProxyError):
    """Raised when upstream model provider fails."""


class ValidationError(SentinelProxyError):
    """Raised when request validation fails."""