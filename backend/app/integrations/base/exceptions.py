class ConnectorError(Exception):
    """Raised when a connector encounters a recoverable error (e.g., connection failure)."""
    pass

class IntegrationValidationError(Exception):
    """Raised when data validation fails before upserting to MongoDB."""
    pass
