"""C container system for MGen."""

from typing import List

from ..base import AbstractContainerSystem


class CContainerSystem(AbstractContainerSystem):
    """C container system using simple arrays and structs."""

    def get_list_type(self, element_type: str) -> str:
        """Get C array type for element type."""
        return f"{element_type}*"

    def get_dict_type(self, key_type: str, value_type: str) -> str:
        """Get C struct type for key-value storage."""
        # Simplified - in practice would use hash table or linked list
        return f"struct {{{key_type} key; {value_type} value;}}"

    def get_set_type(self, element_type: str) -> str:
        """Get C array type for set storage."""
        return f"{element_type}*"

    def generate_container_operations(self, container_type: str, operations: List[str]) -> str:
        """Generate C container operations."""
        # Simplified implementation
        operations_code = []

        for op in operations:
            if op == "append":
                operations_code.append("/* append operation */")
            elif op == "insert":
                operations_code.append("/* insert operation */")
            elif op == "remove":
                operations_code.append("/* remove operation */")

        return "\n".join(operations_code)

    def get_required_imports(self) -> List[str]:
        """Get C headers required for container operations."""
        return [
            "#include <stdlib.h>",
            "#include <string.h>",
        ]