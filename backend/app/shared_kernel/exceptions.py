"""Exceptions for the cross-app ports in `shared_kernel/ports.py`.

Subclass core's HTTP-mapped DomainError types directly so a use case can
call a port method and let failures propagate to the global exception
handlers without an explicit try/except translating them — see ADR-007.
"""

from app.core.exceptions import BadGatewayError, ServiceUnavailableError


class PaymentGatewayNotConfiguredError(ServiceUnavailableError):
    """Raised when no (or an incomplete) payment gateway config exists yet."""


class PaymentGatewayRequestError(BadGatewayError):
    """Raised when a payment gateway collection request fails or returns an
    unexpected shape."""
