"""Backend registry system for MGen language backends."""

from typing import Dict, List, Type

from .base import LanguageBackend


class BackendRegistry:
    """Central registry for all language backends."""

    def __init__(self):
        """Initialize registry with empty backend collection."""
        self._backends: Dict[str, Type[LanguageBackend]] = {}
        self._register_built_in_backends()

    def register_backend(self, name: str, backend_class: Type[LanguageBackend]) -> None:
        """Register a new language backend."""
        self._backends[name] = backend_class

    def get_backend(self, name: str) -> LanguageBackend:
        """Get backend instance by name."""
        if name not in self._backends:
            available = ', '.join(self.list_backends())
            raise ValueError(f"Unknown backend: {name}. Available: {available}")
        return self._backends[name]()

    def list_backends(self) -> List[str]:
        """List all available backend names."""
        return list(self._backends.keys())

    def has_backend(self, name: str) -> bool:
        """Check if backend is registered."""
        return name in self._backends

    def _register_built_in_backends(self) -> None:
        """Register built-in backends as they become available."""
        # Try to register C backend
        try:
            from .c.backend import CBackend
            self.register_backend("c", CBackend)
        except ImportError:
            pass  # C backend not yet implemented

        # Try to register Rust backend
        try:
            from .rust.backend import RustBackend
            self.register_backend("rust", RustBackend)
        except ImportError:
            pass  # Rust backend not yet implemented

        # Try to register Go backend
        try:
            from .go.backend import GoBackend
            self.register_backend("go", GoBackend)
        except ImportError:
            pass  # Go backend not yet implemented

        # Try to register C++ backend
        try:
            from .cpp.backend import CppBackend
            self.register_backend("cpp", CppBackend)
        except ImportError:
            pass  # C++ backend not yet implemented


# Global registry instance
registry = BackendRegistry()