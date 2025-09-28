"""C code element factory."""

from typing import List, Optional

from ..base import AbstractFactory


class CFactory(AbstractFactory):
    """Factory for creating C code elements."""

    def create_variable(self, name: str, type_name: str, value: Optional[str] = None) -> str:
        """Create C variable declaration."""
        if value is not None:
            return f"{type_name} {name} = {value};"
        return f"{type_name} {name};"

    def create_function_signature(self, name: str, params: List[tuple], return_type: str) -> str:
        """Create C function signature."""
        param_strs = []
        for param_name, param_type in params:
            param_strs.append(f"{param_type} {param_name}")

        params_str = ", ".join(param_strs) if param_strs else "void"
        return f"{return_type} {name}({params_str})"

    def create_comment(self, text: str) -> str:
        """Create C comment."""
        if '\n' in text:
            lines = text.split('\n')
            comment_lines = ["/*"] + [f" * {line}" for line in lines] + [" */"]
            return '\n'.join(comment_lines)
        return f"/* {text} */"

    def create_include(self, library: str) -> str:
        """Create C include statement."""
        if library.startswith('<') and library.endswith('>'):
            return f"#include {library}"
        elif library.startswith('"') and library.endswith('"'):
            return f"#include {library}"
        else:
            # Assume system header
            return f"#include <{library}>"