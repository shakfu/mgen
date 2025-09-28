"""C container system for MGen with STC support."""

from typing import List

from ..base import AbstractContainerSystem


class CContainerSystem(AbstractContainerSystem):
    """C container system using STC (Smart Template Containers) with fallback."""

    def __init__(self):
        """Initialize container system with STC preference."""
        self.use_stc = True  # Default to STC, fallback available

    def get_list_type(self, element_type: str) -> str:
        """Get C vector type for element type."""
        if self.use_stc:
            # Use STC vector template
            sanitized_type = self._sanitize_type_name(element_type)
            return f"vec_{sanitized_type}"
        else:
            # Fallback to basic array
            return f"{element_type}*"

    def get_dict_type(self, key_type: str, value_type: str) -> str:
        """Get C map type for key-value storage."""
        if self.use_stc:
            # Use STC map template
            sanitized_key = self._sanitize_type_name(key_type)
            sanitized_value = self._sanitize_type_name(value_type)
            return f"map_{sanitized_key}_{sanitized_value}"
        else:
            # Fallback to basic struct
            return f"struct {{{key_type} key; {value_type} value;}}"

    def get_set_type(self, element_type: str) -> str:
        """Get C set type for set storage."""
        if self.use_stc:
            # Use STC set template
            sanitized_type = self._sanitize_type_name(element_type)
            return f"set_{sanitized_type}"
        else:
            # Fallback to basic array
            return f"{element_type}*"

    def generate_container_operations(self, container_type: str, operations: List[str]) -> str:
        """Generate C container operations using STC or fallback."""
        if self.use_stc:
            return self._generate_stc_operations(container_type, operations)
        else:
            return self._generate_basic_operations(container_type, operations)

    def get_required_imports(self) -> List[str]:
        """Get C headers required for container operations."""
        imports = [
            "#include <stdlib.h>",
            "#include <string.h>",
        ]

        if self.use_stc:
            imports.extend([
                "#include \"mgen_stc_bridge.h\"",
                "#include \"mgen_error_handling.h\"",
                "#include \"mgen_python_ops.h\"",
                "// STC template headers will be included as needed",
            ])
        else:
            imports.extend([
                "#include \"mgen_error_handling.h\"",
                "#include \"mgen_memory_ops.h\"",
            ])

        return imports

    def generate_container_declarations(self, containers: List[tuple]) -> str:
        """Generate STC container template declarations."""
        if not self.use_stc:
            return "// Basic array-based containers - no declarations needed"

        declarations = []
        declarations.append("// STC container template declarations")
        declarations.append("#define STC_ENABLED")
        declarations.append("")

        # Generate STC template declarations for each container type
        seen_types = set()
        for container_name, element_type in containers:
            if element_type not in seen_types:
                sanitized_type = self._sanitize_type_name(element_type)

                # Vector declaration
                declarations.append(f"#define i_type vec_{sanitized_type}")
                declarations.append(f"#define i_val {element_type}")
                declarations.append("#include \"stc/vec.h\"")
                declarations.append("")

                # Map declaration (for string keys)
                declarations.append(f"#define i_type map_str_{sanitized_type}")
                declarations.append("#define i_key_str")
                declarations.append(f"#define i_val {element_type}")
                declarations.append("#include \"stc/map.h\"")
                declarations.append("")

                # Set declaration
                declarations.append(f"#define i_type set_{sanitized_type}")
                declarations.append(f"#define i_key {element_type}")
                declarations.append("#include \"stc/set.h\"")
                declarations.append("")

                seen_types.add(element_type)

        # Special string container
        if "str" not in seen_types:
            declarations.append("// String containers")
            declarations.append("#define i_type vec_cstr")
            declarations.append("#define i_val_str")
            declarations.append("#include \"stc/vec.h\"")
            declarations.append("")

        # Include STC bridge implementation
        declarations.append("// Include MGen STC bridge helpers")
        declarations.append("MGEN_IMPLEMENT_STRING_SPLIT_HELPERS()")
        declarations.append("")

        return "\n".join(declarations)

    def _sanitize_type_name(self, type_name: str) -> str:
        """Sanitize type name for use in STC template names."""
        # Convert C types to safe identifier names
        type_map = {
            "int": "int",
            "char": "char",
            "float": "float",
            "double": "double",
            "char*": "str",
            "const char*": "cstr",
            "string": "str",
            "bool": "bool",
        }
        return type_map.get(type_name, type_name.replace("*", "ptr").replace(" ", "_"))

    def _generate_stc_operations(self, container_type: str, operations: List[str]) -> str:
        """Generate STC-based container operations."""
        operations_code = []
        operations_code.append(f"// STC operations for {container_type}")

        for op in operations:
            if op == "append":
                operations_code.append(f"// {container_type}_push(&container, element);")
            elif op == "insert":
                operations_code.append(f"// {container_type}_insert_at(&container, index, element);")
            elif op == "remove":
                operations_code.append(f"// {container_type}_erase_at(&container, index);")
            elif op == "get":
                operations_code.append(f"// element = *{container_type}_at(&container, index);")
            elif op == "set":
                operations_code.append(f"// *{container_type}_at(&container, index) = element;")
            elif op == "size":
                operations_code.append(f"// size = {container_type}_size(&container);")
            elif op == "clear":
                operations_code.append(f"// {container_type}_clear(&container);")
            elif op == "contains":
                operations_code.append(f"// found = {container_type}_contains(&container, element);")

        operations_code.append("")
        operations_code.append("// Use MGEN_VEC_AT_SAFE for bounds checking")
        operations_code.append("// Use MGEN_IN_VEC for 'in' operator")
        operations_code.append("// Use MGEN_VEC_ENUMERATE for iteration")

        return "\n".join(operations_code)

    def _generate_basic_operations(self, container_type: str, operations: List[str]) -> str:
        """Generate basic fallback container operations."""
        operations_code = []
        operations_code.append(f"// Basic operations for {container_type}")

        for op in operations:
            if op == "append":
                operations_code.append("/* TODO: Implement append with realloc */")
            elif op == "insert":
                operations_code.append("/* TODO: Implement insert with memmove */")
            elif op == "remove":
                operations_code.append("/* TODO: Implement remove with memmove */")
            elif op == "get":
                operations_code.append("/* TODO: Implement bounds-checked get */")
            elif op == "set":
                operations_code.append("/* TODO: Implement bounds-checked set */")
            elif op == "size":
                operations_code.append("/* TODO: Track array size separately */")
            elif op == "clear":
                operations_code.append("/* TODO: Free array and reset size */")
            elif op == "contains":
                operations_code.append("/* TODO: Linear search implementation */")

        return "\n".join(operations_code)

    def generate_container_includes(self) -> str:
        """Generate includes needed for containers."""
        if self.use_stc:
            return """// MGen runtime includes
#include "mgen_error_handling.h"
#include "mgen_python_ops.h"
#include "mgen_memory_ops.h"
#include "mgen_stc_bridge.h"

// STC will be included via template declarations
"""
        else:
            return """// MGen runtime includes (basic fallback)
#include "mgen_error_handling.h"
#include "mgen_memory_ops.h"
"""