"""C backend implementation for MGen."""

from ..base import LanguageBackend, AbstractFactory, AbstractEmitter, AbstractBuilder, AbstractContainerSystem
from .factory import CFactory
from .emitter import CEmitter
from .builder import CBuilder
from .containers import CContainerSystem


class CBackend(LanguageBackend):
    """Clean C backend implementation for MGen."""

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
        return CEmitter()

    def get_builder(self) -> AbstractBuilder:
        """Get C build system."""
        return CBuilder()

    def get_container_system(self) -> AbstractContainerSystem:
        """Get C container system."""
        return CContainerSystem()