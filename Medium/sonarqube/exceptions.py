class SonarQubeException(Exception):
    """Base exception for all SonarQube-related errors."""
    pass

class InsufficientPrivilegesException(SonarQubeException):
    """Exception raised for insufficient privileges."""
    pass

class GroupNotFoundException(SonarQubeException):
    """Exception raised when a group is not found."""
    pass

class GroupAlreadyExistsException(SonarQubeException):
    """Exception raised when a group already exists."""
    pass

class UnexpectedResponseException(SonarQubeException):
    """Exception raised for unexpected API response."""
    pass