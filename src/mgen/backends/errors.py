"""Common error classes for MGen backends.

This module provides shared exception classes used across all backend implementations
for consistent error handling and reporting.
"""


class UnsupportedFeatureError(Exception):
    """Raised when encountering unsupported Python features during code generation."""

    pass


class TypeMappingError(Exception):
    """Raised when type annotation cannot be mapped to target language type."""

    pass
