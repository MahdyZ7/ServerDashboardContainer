# Custom exceptions for the Server Monitoring Dashboard


class DashboardException(Exception):
    """Base exception for all dashboard errors"""

    def __init__(self, message, details=None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class APIException(DashboardException):
    """Base exception for API-related errors"""

    pass


class APIConnectionError(APIException):
    """Raised when unable to connect to API"""

    def __init__(self, message="Unable to connect to API", details=None):
        super().__init__(message, details)


class APITimeoutError(APIException):
    """Raised when API request times out"""

    def __init__(self, message="API request timed out", details=None):
        super().__init__(message, details)


class APIResponseError(APIException):
    """Raised when API returns an error response"""

    def __init__(self, message="API returned an error", status_code=None, details=None):
        super().__init__(message, details)
        self.status_code = status_code


class APIDataError(APIException):
    """Raised when API returns invalid or unexpected data"""

    def __init__(self, message="API returned invalid data", details=None):
        super().__init__(message, details)


class DataProcessingError(DashboardException):
    """Raised when data processing fails"""

    pass


class ValidationError(DashboardException):
    """Raised when input validation fails"""

    pass


class ConfigurationError(DashboardException):
    """Raised when configuration is invalid"""

    pass
