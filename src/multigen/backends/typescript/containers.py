"""TypeScript container system for MultiGen."""

from ..base import AbstractContainerSystem


class TypeScriptContainerSystem(AbstractContainerSystem):
    """TypeScript container system using built-in types (Array, Map, Set)."""

    def get_list_type(self, element_type: str) -> str:
        """Get TypeScript array type for element type."""
        return f"{element_type}[]"

    def get_dict_type(self, key_type: str, value_type: str) -> str:
        """Get TypeScript Map type for key-value storage.

        Map (not object literal) preserves key types, insertion order, and
        non-string keys -- faithful to Python dict semantics.
        """
        return f"Map<{key_type}, {value_type}>"

    def get_set_type(self, element_type: str) -> str:
        """Get TypeScript Set type for set storage."""
        return f"Set<{element_type}>"

    def generate_container_operations(self, container_type: str, operations: list[str]) -> str:
        """Generate TypeScript container operations."""
        operations_code = []

        for op in operations:
            if op == "append" and container_type.endswith("[]"):
                operations_code.append("// arr.push(item)")
            elif op == "insert" and container_type.startswith("Map<"):
                operations_code.append("// m.set(key, value)")
            elif op == "remove":
                operations_code.append("// m.delete(key)")

        return "\n".join(operations_code)

    def get_required_imports(self) -> list[str]:
        """Get TypeScript imports required for container operations."""
        return []  # TypeScript's built-in containers don't require imports
