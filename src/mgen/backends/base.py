"""Abstract base classes for MGen language backends."""

import ast
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class LanguageBackend(ABC):
    """Abstract base for all language backends in MGen."""

    @abstractmethod
    def get_name(self) -> str:
        """Language name (e.g., 'rust', 'go', 'cpp', 'c')."""

    @abstractmethod
    def get_file_extension(self) -> str:
        """Source file extension (e.g., '.rs', '.go', '.cpp', '.c')."""

    @abstractmethod
    def get_factory(self) -> "AbstractFactory":
        """Get language-specific code element factory."""

    @abstractmethod
    def get_emitter(self) -> "AbstractEmitter":
        """Get language-specific code emitter."""

    @abstractmethod
    def get_builder(self) -> "AbstractBuilder":
        """Get language-specific build system."""

    @abstractmethod
    def get_container_system(self) -> "AbstractContainerSystem":
        """Get language-specific container library integration."""


class AbstractFactory(ABC):
    """Abstract factory for creating language-specific code elements."""

    @abstractmethod
    def create_variable(self, name: str, type_name: str, value: Optional[str] = None) -> str:
        """Create variable declaration."""

    @abstractmethod
    def create_function_signature(self, name: str, params: List[tuple], return_type: str) -> str:
        """Create function signature."""

    @abstractmethod
    def create_comment(self, text: str) -> str:
        """Create language-appropriate comment."""

    @abstractmethod
    def create_include(self, library: str) -> str:
        """Create import/include statement."""


class AbstractEmitter(ABC):
    """Abstract emitter for generating language-specific code."""

    @abstractmethod
    def emit_function(self, func_node: ast.FunctionDef, type_context: Dict[str, str]) -> str:
        """Generate complete function in target language."""

    @abstractmethod
    def emit_module(self, source_code: str, analysis_result: Any) -> str:
        """Generate complete module/file in target language."""

    @abstractmethod
    def map_python_type(self, python_type: str) -> str:
        """Map Python type to target language type."""

    @abstractmethod
    def can_use_simple_emission(self, func_node: ast.FunctionDef, type_context: Dict[str, str]) -> bool:
        """Determine if function can use simple emission strategy."""


class AbstractBuilder(ABC):
    """Abstract builder for language-specific build systems."""

    @abstractmethod
    def generate_build_file(self, source_files: List[str], target_name: str) -> str:
        """Generate build configuration (Makefile, Cargo.toml, etc.)."""

    @abstractmethod
    def get_build_filename(self) -> str:
        """Get build file name (Makefile, Cargo.toml, etc.)."""

    @abstractmethod
    def compile_direct(self, source_file: str, output_path: str) -> bool:
        """Compile source directly using language tools."""

    @abstractmethod
    def get_compile_flags(self) -> List[str]:
        """Get compilation flags for the language."""


class AbstractContainerSystem(ABC):
    """Abstract container system for language-specific collections."""

    @abstractmethod
    def get_list_type(self, element_type: str) -> str:
        """Get list/array type for element type."""

    @abstractmethod
    def get_dict_type(self, key_type: str, value_type: str) -> str:
        """Get dictionary/map type for key-value pair."""

    @abstractmethod
    def get_set_type(self, element_type: str) -> str:
        """Get set type for element type."""

    @abstractmethod
    def generate_container_operations(self, container_type: str, operations: List[str]) -> str:
        """Generate container-specific operations code."""

    @abstractmethod
    def get_required_imports(self) -> List[str]:
        """Get imports required for container operations."""