class SentinelProxyError(Exception):
    """Base application exception."""


class ProviderError(SentinelProxyError):
    """Raised when upstream model provider fails."""


class ValidationError(SentinelProxyError):
    """Raised when request validation fails."""

class MappingStoreError(SentinelProxyError):
    """Raised when secure placeholder mapping storage fails."""

class RateLimitExceededError(SentinelProxyError):
    """Raised when an API key exceeds the allowed request rate."""