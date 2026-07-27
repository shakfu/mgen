"""TypeScript backend implementation for MultiGen."""

from typing import Optional

from ..base import AbstractBuilder, AbstractContainerSystem, AbstractEmitter, AbstractFactory, LanguageBackend
from ..optimizer import AbstractOptimizer, NoOpOptimizer
from ..preferences import BackendPreferences, TypeScriptPreferences
from .builder import TypeScriptBuilder
from .containers import TypeScriptContainerSystem
from .emitter import TypeScriptEmitter
from .factory import TypeScriptFactory


class TypeScriptBackend(LanguageBackend):
    """TypeScript backend implementation for MultiGen."""

    def __init__(self, preferences: Optional[BackendPreferences] = None):
        """Initialize TypeScript backend with preferences."""
        if preferences is None:
            preferences = TypeScriptPreferences()
        super().__init__(preferences)
        self._optimizer: Optional[NoOpOptimizer] = None

    def get_name(self) -> str:
        """Return backend name."""
        return "typescript"

    def get_file_extension(self) -> str:
        """Return TypeScript source file extension."""
        return ".ts"

    def get_factory(self) -> AbstractFactory:
        """Get TypeScript code element factory."""
        return TypeScriptFactory()

    def get_emitter(self) -> AbstractEmitter:
        """Get TypeScript code emitter."""
        return TypeScriptEmitter(self.preferences)

    def get_builder(self) -> AbstractBuilder:
        """Get TypeScript build system."""
        return TypeScriptBuilder()

    def get_container_system(self) -> AbstractContainerSystem:
        """Get TypeScript container system."""
        return TypeScriptContainerSystem()

    def get_optimizer(self) -> AbstractOptimizer:
        """Get TypeScript optimizer (delegates to compiler).

        TypeScript optimization is handled by the Deno/tsc toolchain
        rather than at the code generation level.

        Returns:
            NoOpOptimizer instance
        """
        if self._optimizer is None:
            self._optimizer = NoOpOptimizer()
        return self._optimizer
