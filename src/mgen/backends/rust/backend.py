"""Rust backend implementation for MGen."""

from typing import Optional

from ..base import LanguageBackend, AbstractFactory, AbstractEmitter, AbstractBuilder, AbstractContainerSystem
from ..preferences import BackendPreferences, RustPreferences
from .factory import RustFactory
from .emitter import RustEmitter
from .builder import RustBuilder
from .containers import RustContainerSystem


class RustBackend(LanguageBackend):
    """Rust backend implementation for MGen."""

    def __init__(self, preferences: Optional[BackendPreferences] = None):
        """Initialize Rust backend with preferences."""
        if preferences is None:
            preferences = RustPreferences()
        super().__init__(preferences)

    def get_name(self) -> str:
        """Return backend name."""
        return "rust"

    def get_file_extension(self) -> str:
        """Return Rust source file extension."""
        return ".rs"

    def get_factory(self) -> AbstractFactory:
        """Get Rust code element factory."""
        return RustFactory()

    def get_emitter(self) -> AbstractEmitter:
        """Get Rust code emitter."""
        return RustEmitter(self.preferences)

    def get_builder(self) -> AbstractBuilder:
        """Get Rust build system."""
        return RustBuilder()

    def get_container_system(self) -> AbstractContainerSystem:
        """Get Rust container system."""
        return RustContainerSystem()