"""C code element factory using CGen's sophisticated factory system."""

import sys
from pathlib import Path
from typing import List, Optional

from ..base import AbstractFactory

# Add CGen to path for import
cgen_path = Path.home() / "projects" / "cgen" / "src"
if str(cgen_path) not in sys.path:
    sys.path.insert(0, str(cgen_path))

try:
    from cgen.generator.factory import CFactory as CGenFactory
    from cgen.generator import core
    from cgen.generator.writer import Writer
    from cgen.generator.style import StyleOptions
    CGEN_AVAILABLE = True
except ImportError:
    CGEN_AVAILABLE = False


class CFactory(AbstractFactory):
    """Factory for creating C code elements using CGen's sophisticated system."""

    def __init__(self):
        """Initialize factory with CGen components."""
        if CGEN_AVAILABLE:
            self.cgen_factory = CGenFactory()
            self.writer = Writer(StyleOptions())
            self.use_cgen = True
        else:
            self.use_cgen = False

    def create_variable(self, name: str, type_name: str, value: Optional[str] = None) -> str:
        """Create C variable declaration."""
        if self.use_cgen:
            try:
                var_type = core.Type(type_name)
                if value is not None:
                    var_decl = self.cgen_factory.variable_declaration(var_type, name, value)
                else:
                    var_decl = self.cgen_factory.variable_declaration(var_type, name)
                return self.writer.write_str(var_decl)
            except Exception:
                # Fallback to basic implementation
                pass

        # Basic implementation fallback
        if value is not None:
            return f"{type_name} {name} = {value};"
        return f"{type_name} {name};"

    def create_function_signature(self, name: str, params: List[tuple], return_type: str) -> str:
        """Create C function signature."""
        if self.use_cgen:
            try:
                # Create parameter list
                param_elements = []
                for param_name, param_type in params:
                    param_type_obj = core.Type(param_type)
                    param_elements.append(self.cgen_factory.variable_declaration(param_type_obj, param_name))

                # Create function declaration
                return_type_obj = core.Type(return_type)
                func_decl = self.cgen_factory.function_declaration(
                    return_type_obj, name, param_elements
                )
                return self.writer.write_str(func_decl)
            except Exception:
                # Fallback to basic implementation
                pass

        # Basic implementation fallback
        param_strs = []
        for param_name, param_type in params:
            param_strs.append(f"{param_type} {param_name}")

        params_str = ", ".join(param_strs) if param_strs else "void"
        return f"{return_type} {name}({params_str})"

    def create_comment(self, text: str) -> str:
        """Create C comment."""
        if self.use_cgen:
            try:
                if '\n' in text:
                    comment = self.cgen_factory.block_comment(text.split('\n'))
                else:
                    comment = self.cgen_factory.line_comment(text)
                return self.writer.write_str(comment)
            except Exception:
                # Fallback to basic implementation
                pass

        # Basic implementation fallback
        if '\n' in text:
            lines = text.split('\n')
            comment_lines = ["/*"] + [f" * {line}" for line in lines] + [" */"]
            return '\n'.join(comment_lines)
        return f"/* {text} */"

    def create_include(self, library: str) -> str:
        """Create C include statement."""
        if self.use_cgen:
            try:
                system_include = not (library.startswith('"') and library.endswith('"'))
                clean_library = library.strip('<>"')
                include = self.cgen_factory.include(clean_library, system=system_include)
                return self.writer.write_str(include)
            except Exception:
                # Fallback to basic implementation
                pass

        # Basic implementation fallback
        if library.startswith('<') and library.endswith('>'):
            return f"#include {library}"
        elif library.startswith('"') and library.endswith('"'):
            return f"#include {library}"
        else:
            # Assume system header
            return f"#include <{library}>"

    def create_function(self, name: str, params: List[str], return_type: str, body: str) -> str:
        """Create complete C function."""
        if self.use_cgen:
            try:
                # Parse parameters
                param_list = []
                for param in params:
                    if ' ' in param:
                        parts = param.split()
                        param_type = ' '.join(parts[:-1])
                        param_name = parts[-1]
                        param_type_obj = core.Type(param_type)
                        param_list.append(self.cgen_factory.variable_declaration(param_type_obj, param_name))

                # Create function
                return_type_obj = core.Type(return_type)
                func_decl = self.cgen_factory.function_declaration(return_type_obj, name, param_list)

                # Add body
                body_block = core.Block()
                body_block.extend([core.Statement(line) for line in body.split('\n') if line.strip()])

                func_def = self.cgen_factory.function_definition(func_decl, body_block)
                return self.writer.write_str(func_def)
            except Exception:
                # Fallback to basic implementation
                pass

        # Basic implementation fallback
        params_str = ", ".join(params) if params else "void"
        return f"{return_type} {name}({params_str}) {{\n{body}\n}}"

    def create_struct(self, name: str, fields: List[tuple]) -> str:
        """Create C struct definition."""
        if self.use_cgen:
            try:
                struct_fields = []
                for field_name, field_type in fields:
                    field_type_obj = core.Type(field_type)
                    struct_fields.append(self.cgen_factory.variable_declaration(field_type_obj, field_name))

                struct_def = self.cgen_factory.struct_definition(name, struct_fields)
                return self.writer.write_str(struct_def)
            except Exception:
                # Fallback to basic implementation
                pass

        # Basic implementation fallback
        field_strs = []
        for field_name, field_type in fields:
            field_strs.append(f"    {field_type} {field_name};")

        fields_str = "\n".join(field_strs)
        return f"struct {name} {{\n{fields_str}\n}};"

    def create_array_declaration(self, name: str, element_type: str, size: Optional[int] = None) -> str:
        """Create C array declaration."""
        if self.use_cgen:
            try:
                if size is not None:
                    array_type = core.ArrayType(core.Type(element_type), size)
                else:
                    array_type = core.PointerType(core.Type(element_type))
                array_decl = self.cgen_factory.variable_declaration(array_type, name)
                return self.writer.write_str(array_decl)
            except Exception:
                # Fallback to basic implementation
                pass

        # Basic implementation fallback
        if size is not None:
            return f"{element_type} {name}[{size}];"
        return f"{element_type} *{name};"