"""Common error classes for MGen backends.

This module provides shared exception classes used across all backend implementations
for consistent error handling and reporting.

For backward compatibility, this re-exports the enhanced error classes from mgen.errors.
New code should import from mgen.errors directly.
"""

# Re-export enhanced error classes for backward compatibility
from ..errors import (
    ErrorCode,
    MGenError,
    SourceLocation,
    TypeMappingError,
    UnsupportedFeatureError,
    create_unsupported_feature_error,
    suggest_fix,
)

__all__ = [
    "UnsupportedFeatureError",
    "TypeMappingError",
    "MGenError",
    "SourceLocation",
    "ErrorCode",
    "create_unsupported_feature_error",
    "suggest_fix",
]
