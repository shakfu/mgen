"""Haskell backend implementation for MGen."""

from ..base import LanguageBackend, AbstractFactory, AbstractEmitter, AbstractBuilder, AbstractContainerSystem
from .factory import HaskellFactory
from .emitter import HaskellEmitter
from .builder import HaskellBuilder
from .containers import HaskellContainerSystem


class HaskellBackend(LanguageBackend):
    """Haskell backend implementation for MGen."""

    def get_name(self) -> str:
        """Return backend name."""
        return "haskell"

    def get_file_extension(self) -> str:
        """Return Haskell source file extension."""
        return ".hs"

    def get_factory(self) -> AbstractFactory:
        """Get Haskell code element factory."""
        return HaskellFactory()

    def get_emitter(self) -> AbstractEmitter:
        """Get Haskell code emitter."""
        return HaskellEmitter()

    def get_builder(self) -> AbstractBuilder:
        """Get Haskell build system."""
        return HaskellBuilder()

    def get_container_system(self) -> AbstractContainerSystem:
        """Get Haskell container system."""
        return HaskellContainerSystem()