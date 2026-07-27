"""TypeScript code element factory."""

from typing import Optional

from ..base import AbstractFactory


class TypeScriptFactory(AbstractFactory):
    """Factory for creating TypeScript code elements."""

    def create_variable(self, name: str, type_name: str, value: Optional[str] = None) -> str:
        """Create TypeScript variable declaration."""
        if value is not None:
            return f"let {name}: {type_name} = {value}"
        return f"let {name}: {type_name}"

    def create_function_signature(self, name: str, params: list[tuple[str, str]], return_type: str) -> str:
        """Create TypeScript function signature."""
        param_strs = [f"{param_name}: {param_type}" for param_name, param_type in params]
        params_str = ", ".join(param_strs)

        rt = return_type if return_type else "void"
        return f"function {name}({params_str}): {rt}"

    def create_comment(self, text: str) -> str:
        """Create TypeScript comment."""
        if "\n" in text:
            lines = text.split("\n")
            comment_lines = [f"// {line}" for line in lines]
            return "\n".join(comment_lines)
        return f"// {text}"

    def create_include(self, library: str) -> str:
        """Create TypeScript import statement from the runtime module."""
        return f'import {{ {library} }} from "./multigen_ts_runtime.ts";'
