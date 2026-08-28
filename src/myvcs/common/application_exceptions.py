"""Custom MyVCS exceptions."""


class MyVCSError(Exception):
    """Base exception for all MyVCS errors."""


class ConfigurationError(MyVCSError):
    """Raised when application configuration is invalid."""


class RepositoryError(MyVCSError):
    """Raised when repository operations fail."""


class ObjectStoreError(MyVCSError):
    """Raised when object storage operations fail."""


class ObjectSerializationError(MyVCSError):
    """Raised when an object cannot be serialized."""


class ReferenceError(MyVCSError):
    """Raised when reference operations fail."""


class StagingError(MyVCSError):
    """Raised when staging operations fail."""


class CommitError(MyVCSError):
    """Raised when commit operations fail."""


class CommandError(MyVCSError):
    """Raised when a CLI command fails."""


# New addtion
class ObjectError(MyVCSError):
    """Raised when a CLI command fails."""
