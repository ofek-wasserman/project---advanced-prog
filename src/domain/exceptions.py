class DomainError(Exception):
    """Base class for domain/service errors."""


class InvalidInputError(DomainError):
    pass


class NotFoundError(DomainError):
    pass


class ConflictError(DomainError):
    pass
