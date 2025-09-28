"""Go backend implementation for MGen."""

from ..base import LanguageBackend, AbstractFactory, AbstractEmitter, AbstractBuilder, AbstractContainerSystem
from .factory import GoFactory
from .emitter import GoEmitter
from .builder import GoBuilder
from .containers import GoContainerSystem


class GoBackend(LanguageBackend):
    """Go backend implementation for MGen."""

    def get_name(self) -> str:
        """Return backend name."""
        return "go"

    def get_file_extension(self) -> str:
        """Return Go source file extension."""
        return ".go"

    def get_factory(self) -> AbstractFactory:
        """Get Go code element factory."""
        return GoFactory()

    def get_emitter(self) -> AbstractEmitter:
        """Get Go code emitter."""
        return GoEmitter()

    def get_builder(self) -> AbstractBuilder:
        """Get Go build system."""
        return GoBuilder()

    def get_container_system(self) -> AbstractContainerSystem:
        """Get Go container system."""
        return GoContainerSystem()