"""Backend architecture for MGen multi-language code generation."""

from .base import LanguageBackend, AbstractFactory, AbstractEmitter, AbstractBuilder
from .registry import registry

__all__ = [
    "LanguageBackend",
    "AbstractFactory",
    "AbstractEmitter",
    "AbstractBuilder",
    "registry",
]