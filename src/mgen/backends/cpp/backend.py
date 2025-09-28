"""C++ backend implementation."""

from typing import TYPE_CHECKING

from ..base import LanguageBackend

if TYPE_CHECKING:
    from ..base import AbstractBuilder, AbstractEmitter, AbstractFactory, AbstractContainerSystem


class CppBackend(LanguageBackend):
    """C++ language backend."""

    def get_name(self) -> str:
        """Get the backend name."""
        return "cpp"

    def get_file_extension(self) -> str:
        """Get the file extension for C++ files."""
        return ".cpp"

    def get_factory(self) -> "AbstractFactory":
        """Get the C++ code element factory."""
        from .factory import CppFactory
        return CppFactory()

    def get_emitter(self) -> "AbstractEmitter":
        """Get the C++ code emitter."""
        from .emitter import CppEmitter
        return CppEmitter()

    def get_builder(self) -> "AbstractBuilder":
        """Get the C++ builder."""
        from .builder import CppBuilder
        return CppBuilder()

    def get_container_system(self) -> "AbstractContainerSystem":
        """Get the C++ container system."""
        from .containers import CppContainerSystem
        return CppContainerSystem()