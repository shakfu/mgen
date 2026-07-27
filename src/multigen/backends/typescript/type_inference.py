"""TypeScript-specific type inference strategies.

Extends the base type inference system with TypeScript-specific type
formatting (``T[]``, ``Map<K, V>``, ``Set<T>``) and ``any`` as the fallback.
Mirrors the Go strategy module; only the ``_format_*`` strings and defaults
differ.
"""

import ast
from typing import TYPE_CHECKING, Any, Callable, Optional

from ..type_inference_strategies import (
    CallInferenceStrategy,
    ComprehensionInferenceStrategy,
    DictInferenceStrategy,
    InferenceContext,
    ListInferenceStrategy,
    SetInferenceStrategy,
)

if TYPE_CHECKING:
    from ..type_inference_strategies import TypeInferenceEngine


class TypeScriptListInferenceStrategy(ListInferenceStrategy):
    """TypeScript list type inference with ``T[]`` formatting."""

    def _format_list_type(self, element_type: str, context: InferenceContext) -> str:
        """Format as T[]."""
        return f"{element_type}[]"

    def infer(self, value: ast.expr, context: InferenceContext) -> str:
        assert isinstance(value, ast.List), "Expected ast.List"

        if not value.elts:
            return "number[]"

        result = super().infer(value, context)
        if result == context.type_mapper("list"):
            return "number[]"
        return result


class TypeScriptDictInferenceStrategy(DictInferenceStrategy):
    """TypeScript dict type inference with ``Map<K, V>`` formatting."""

    def _format_dict_type(self, key_type: str, value_type: str, context: InferenceContext) -> str:
        """Format as Map<K, V>."""
        return f"Map<{key_type}, {value_type}>"

    def infer(self, value: ast.expr, context: InferenceContext) -> str:
        assert isinstance(value, ast.Dict), "Expected ast.Dict"

        if not value.keys or not value.values:
            return "Map<number, number>"

        result = super().infer(value, context)
        if result == context.type_mapper("dict"):
            return "Map<number, number>"
        return result


class TypeScriptSetInferenceStrategy(SetInferenceStrategy):
    """TypeScript set type inference with ``Set<T>`` formatting."""

    def _format_set_type(self, element_type: str, context: InferenceContext) -> str:
        """Format as Set<T>."""
        return f"Set<{element_type}>"

    def infer(self, value: ast.expr, context: InferenceContext) -> str:
        assert isinstance(value, ast.Set), "Expected ast.Set"

        if not value.elts:
            return "Set<number>"

        result = super().infer(value, context)
        if result == context.type_mapper("set"):
            return "Set<number>"
        return result


class TypeScriptComprehensionInferenceStrategy(ComprehensionInferenceStrategy):
    """TypeScript comprehension type inference with loop variable inference."""

    def __init__(
        self,
        loop_var_type_inferrer: Optional[Callable[[ast.comprehension], dict[str, str]]] = None,
        element_type_inferrer: Optional[Callable[[ast.expr, dict[str, str]], str]] = None,
    ) -> None:
        """Initialize with TypeScript-specific inference functions."""
        self.loop_var_type_inferrer = loop_var_type_inferrer
        self.element_type_inferrer = element_type_inferrer

    def _infer_list_comp(self, value: ast.ListComp, context: InferenceContext) -> str:
        if self.loop_var_type_inferrer and self.element_type_inferrer:
            loop_var_type = self.loop_var_type_inferrer(value.generators[0])
            element_type = self.element_type_inferrer(value.elt, loop_var_type)
            return f"{element_type}[]"
        return "number[]"

    def _infer_dict_comp(self, value: ast.DictComp, context: InferenceContext) -> str:
        if self.loop_var_type_inferrer and self.element_type_inferrer:
            loop_var_type = self.loop_var_type_inferrer(value.generators[0])
            key_type = self.element_type_inferrer(value.key, loop_var_type)
            value_type = self.element_type_inferrer(value.value, loop_var_type)
            return f"Map<{key_type}, {value_type}>"
        return "Map<number, number>"

    def _infer_set_comp(self, value: ast.SetComp, context: InferenceContext) -> str:
        if self.loop_var_type_inferrer and self.element_type_inferrer:
            loop_var_type = self.loop_var_type_inferrer(value.generators[0])
            element_type = self.element_type_inferrer(value.elt, loop_var_type)
            return f"Set<{element_type}>"
        return "Set<number>"


class TypeScriptCallInferenceStrategy(CallInferenceStrategy):
    """TypeScript call type inference with function return types and class info."""

    def __init__(
        self,
        function_return_types: Optional[dict[str, str]] = None,
        struct_info: Optional[dict[str, dict[str, Any]]] = None,
    ) -> None:
        """Initialize with TypeScript converter context."""
        self.function_return_types = function_return_types or {}
        self.struct_info = struct_info or {}

    def _infer_from_function(self, func_name: str, context: InferenceContext) -> str:
        if func_name in self.function_return_types:
            return self.function_return_types[func_name]
        if func_name in self.struct_info:
            return func_name
        if func_name == "sum":
            return "number"
        return "any"

    def _infer_from_method(self, method_name: str, context: InferenceContext) -> str:
        if method_name in ["upper", "lower", "strip", "replace", "join"]:
            return "string"
        elif method_name == "split":
            return "string[]"
        elif method_name == "find":
            return "number"
        return "any"


def create_typescript_type_inference_engine(
    converter: "MultiGenPythonToTypeScriptConverter",  # type: ignore[name-defined]  # noqa: F821
) -> "TypeInferenceEngine":
    """Create a TypeInferenceEngine configured for TypeScript."""
    from ..type_inference_strategies import ConstantInferenceStrategy, NameInferenceStrategy, TypeInferenceEngine

    strategies = [
        ConstantInferenceStrategy(),
        NameInferenceStrategy(),
        TypeScriptListInferenceStrategy(),
        TypeScriptDictInferenceStrategy(),
        TypeScriptSetInferenceStrategy(),
        TypeScriptComprehensionInferenceStrategy(
            loop_var_type_inferrer=converter._infer_loop_variable_type,
            element_type_inferrer=converter._infer_comprehension_element_type,
        ),
        TypeScriptCallInferenceStrategy(
            function_return_types=converter.function_return_types,
            struct_info=converter.struct_info,
        ),
    ]

    return TypeInferenceEngine(strategies)


__all__ = [
    "TypeScriptListInferenceStrategy",
    "TypeScriptDictInferenceStrategy",
    "TypeScriptSetInferenceStrategy",
    "TypeScriptComprehensionInferenceStrategy",
    "TypeScriptCallInferenceStrategy",
    "create_typescript_type_inference_engine",
]
