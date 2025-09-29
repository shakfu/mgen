"""C backend implementation for MGen."""

from typing import Optional

from ..base import LanguageBackend, AbstractFactory, AbstractEmitter, AbstractBuilder, AbstractContainerSystem
from ..preferences import BackendPreferences, CPreferences
from .factory import CFactory
from .emitter import CEmitter
from .builder import CBuilder
from .containers import CContainerSystem


class CBackend(LanguageBackend):
    """Clean C backend implementation for MGen."""

    def __init__(self, preferences: Optional[BackendPreferences] = None):
        """Initialize C backend with preferences."""
        if preferences is None:
            preferences = CPreferences()
        super().__init__(preferences)

    def get_name(self) -> str:
        """Return backend name."""
        return "c"

    def get_file_extension(self) -> str:
        """Return C source file extension."""
        return ".c"

    def get_factory(self) -> AbstractFactory:
        """Get C code element factory."""
        return CFactory()

    def get_emitter(self) -> AbstractEmitter:
        """Get C code emitter."""
        return CEmitter(self.preferences)

    def get_builder(self) -> AbstractBuilder:
        """Get C build system."""
        return CBuilder()

    def get_container_system(self) -> AbstractContainerSystem:
        """Get C container system."""
        return CContainerSystem()