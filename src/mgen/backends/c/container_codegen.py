"""
Container Code Generator - Prototype

This module generates type-specific container implementations directly into
the output C file, eliminating the need for external runtime libraries.

Philosophy: Code generators should produce self-contained, complete code.
Similar to C++ template monomorphization or Rust generic instantiation.

Status: Prototype - runs in parallel with existing runtime library approach
"""

from pathlib import Path
from typing import Optional


class ContainerCodeGenerator:
    """Generate type-specific container implementations inline."""

    def __init__(self) -> None:
        """Initialize code generator with templates from runtime library."""
        self.runtime_dir = Path(__file__).parent / "runtime"
        self._template_cache: dict[str, str] = {}

    def _load_template(self, filename: str) -> str:
        """Load a runtime library file as a code generation template.

        Args:
            filename: Runtime library filename (e.g., "mgen_str_int_map.c")

        Returns:
            Template content as string
        """
        if filename in self._template_cache:
            return self._template_cache[filename]

        template_path = self.runtime_dir / filename
        with open(template_path, encoding="utf-8") as f:
            content = f.read()

        self._template_cache[filename] = content
        return content

    def _strip_includes_and_headers(self, code: str) -> str:
        """Strip #include directives from template code.

        These will be generated separately in the main includes section.

        Args:
            code: Template code with includes

        Returns:
            Code with includes removed
        """
        lines = code.split("\n")
        filtered_lines = []

        for line in lines:
            stripped = line.strip()
            # Skip include directives
            if stripped.startswith("#include"):
                continue
            filtered_lines.append(line)

        return "\n".join(filtered_lines)

    def _remove_error_handling_macros(self, code: str) -> str:
        """Remove MGEN_SET_ERROR macro calls for self-contained code.

        For prototype: Replace error macros with simple returns.
        Future: Generate error handling inline or make it optional.

        Args:
            code: Code with MGEN_SET_ERROR calls

        Returns:
            Code with error handling removed
        """
        lines = code.split("\n")
        filtered_lines = []

        for line in lines:
            stripped = line.strip()
            # Skip lines with MGEN_SET_ERROR macro
            if "MGEN_SET_ERROR" in line:
                continue
            filtered_lines.append(line)

        return "\n".join(filtered_lines)

    def generate_str_int_map(self) -> str:
        """Generate complete implementation for string→int hash table.

        This is a prototype that uses the existing runtime library as a template.
        Future versions will support parameterized generation for any key/value types.

        Returns:
            Complete C code for string→int map implementation
        """
        # Load templates
        header = self._load_template("mgen_str_int_map.h")
        implementation = self._load_template("mgen_str_int_map.c")

        # Strip includes from implementation (we'll handle them separately)
        impl_code = self._strip_includes_and_headers(implementation)

        # Remove error handling macros for self-contained code
        impl_code = self._remove_error_handling_macros(impl_code)

        # Strip header guards and includes from header
        header_lines = []
        in_header_guard = False
        for line in header.split("\n"):
            stripped = line.strip()

            # Skip header guards
            if stripped.startswith("#ifndef") and "_H" in stripped:
                in_header_guard = True
                continue
            if stripped.startswith("#define") and "_H" in stripped:
                continue
            if stripped.startswith("#endif") and in_header_guard:
                in_header_guard = False
                continue

            # Skip includes, extern C
            if (stripped.startswith("#include")
                or stripped.startswith("#ifdef __cplusplus")
                or stripped.startswith("extern \"C\"")
                or stripped.startswith("#endif")
                or stripped == "}"):
                continue

            header_lines.append(line)

        header_code = "\n".join(header_lines)

        # Combine into generated implementation
        sections = [
            "// ========== Generated Container: str_int_map ==========",
            "// String → int hash table implementation",
            "// Generated inline for this program (no external dependencies)",
            "",
            "// Type definitions and API",
            header_code.strip(),
            "",
            "// Implementation",
            impl_code.strip(),
            "",
            "// ========== End of Generated Container ==========",
            "",
        ]

        return "\n".join(sections)

    def generate_vec_int(self) -> str:
        """Generate complete implementation for integer vector (dynamic array).

        Returns:
            Complete C code for integer vector implementation
        """
        # Load templates
        header = self._load_template("mgen_vec_int.h")
        implementation = self._load_template("mgen_vec_int.c")

        # Strip includes from implementation
        impl_code = self._strip_includes_and_headers(implementation)

        # Remove error handling macros for self-contained code
        impl_code = self._remove_error_handling_macros(impl_code)

        # Strip header guards and includes from header
        header_lines = []
        in_header_guard = False
        for line in header.split("\n"):
            stripped = line.strip()

            # Skip header guards
            if stripped.startswith("#ifndef") and "_H" in stripped:
                in_header_guard = True
                continue
            if stripped.startswith("#define") and "_H" in stripped:
                continue
            if stripped.startswith("#endif") and in_header_guard:
                in_header_guard = False
                continue

            # Skip includes, extern C
            if (stripped.startswith("#include")
                or stripped.startswith("#ifdef __cplusplus")
                or stripped.startswith("extern \"C\"")
                or stripped.startswith("#endif")
                or stripped == "}"):
                continue

            header_lines.append(line)

        header_code = "\n".join(header_lines)

        # Combine into generated implementation
        sections = [
            "// ========== Generated Container: vec_int ==========",
            "// Integer vector (dynamic array) implementation",
            "// Generated inline for this program (no external dependencies)",
            "",
            "// Type definitions and API",
            header_code.strip(),
            "",
            "// Implementation",
            impl_code.strip(),
            "",
            "// ========== End of Generated Container ==========",
            "",
        ]

        return "\n".join(sections)

    def generate_set_int(self) -> str:
        """Generate complete implementation for integer hash set.

        Returns:
            Complete C code for integer hash set implementation
        """
        # Load templates
        header = self._load_template("mgen_set_int.h")
        implementation = self._load_template("mgen_set_int.c")

        # Strip includes from implementation
        impl_code = self._strip_includes_and_headers(implementation)

        # Remove error handling macros for self-contained code
        impl_code = self._remove_error_handling_macros(impl_code)

        # Strip header guards and includes from header
        header_lines = []
        in_header_guard = False
        for line in header.split("\n"):
            stripped = line.strip()

            # Skip header guards
            if stripped.startswith("#ifndef") and "_H" in stripped:
                in_header_guard = True
                continue
            if stripped.startswith("#define") and "_H" in stripped:
                continue
            if stripped.startswith("#endif") and in_header_guard:
                in_header_guard = False
                continue

            # Skip includes, extern C
            if (stripped.startswith("#include")
                or stripped.startswith("#ifdef __cplusplus")
                or stripped.startswith("extern \"C\"")
                or stripped.startswith("#endif")
                or stripped == "}"):
                continue

            header_lines.append(line)

        header_code = "\n".join(header_lines)

        # Combine into generated implementation
        sections = [
            "// ========== Generated Container: set_int ==========",
            "// Integer hash set implementation",
            "// Generated inline for this program (no external dependencies)",
            "",
            "// Type definitions and API",
            header_code.strip(),
            "",
            "// Implementation",
            impl_code.strip(),
            "",
            "// ========== End of Generated Container ==========",
            "",
        ]

        return "\n".join(sections)

    def generate_map_int_int(self) -> str:
        """Generate complete implementation for int→int hash map.

        Returns:
            Complete C code for int→int map implementation
        """
        # Load templates
        header = self._load_template("mgen_map_int_int.h")
        implementation = self._load_template("mgen_map_int_int.c")

        # Strip includes from implementation
        impl_code = self._strip_includes_and_headers(implementation)

        # Remove error handling macros for self-contained code
        impl_code = self._remove_error_handling_macros(impl_code)

        # Strip header guards and includes from header
        header_lines = []
        in_header_guard = False
        for line in header.split("\n"):
            stripped = line.strip()

            # Skip header guards
            if stripped.startswith("#ifndef") and "_H" in stripped:
                in_header_guard = True
                continue
            if stripped.startswith("#define") and "_H" in stripped:
                continue
            if stripped.startswith("#endif") and in_header_guard:
                in_header_guard = False
                continue

            # Skip includes, extern C
            if (stripped.startswith("#include")
                or stripped.startswith("#ifdef __cplusplus")
                or stripped.startswith("extern \"C\"")
                or stripped.startswith("#endif")
                or stripped == "}"):
                continue

            header_lines.append(line)

        header_code = "\n".join(header_lines)

        # Combine into generated implementation
        sections = [
            "// ========== Generated Container: map_int_int ==========",
            "// Integer → Integer hash map implementation",
            "// Generated inline for this program (no external dependencies)",
            "",
            "// Type definitions and API",
            header_code.strip(),
            "",
            "// Implementation",
            impl_code.strip(),
            "",
            "// ========== End of Generated Container ==========",
            "",
        ]

        return "\n".join(sections)

    def generate_vec_vec_int(self) -> str:
        """Generate complete implementation for 2D integer arrays (vector of vectors).

        Returns:
            Complete C code for vec_vec_int implementation
        """
        # Load templates
        header = self._load_template("mgen_vec_vec_int.h")
        implementation = self._load_template("mgen_vec_vec_int.c")

        # Strip includes from implementation
        impl_code = self._strip_includes_and_headers(implementation)

        # Remove error handling macros for self-contained code
        impl_code = self._remove_error_handling_macros(impl_code)

        # Strip header guards and includes from header
        header_lines = []
        in_header_guard = False
        for line in header.split("\n"):
            stripped = line.strip()

            # Skip header guards
            if stripped.startswith("#ifndef") and "_H" in stripped:
                in_header_guard = True
                continue
            if stripped.startswith("#define") and "_H" in stripped:
                continue
            if stripped.startswith("#endif") and in_header_guard:
                in_header_guard = False
                continue

            # Skip includes, extern C
            if (stripped.startswith("#include")
                or stripped.startswith("#ifdef __cplusplus")
                or stripped.startswith("extern \"C\"")
                or stripped.startswith("#endif")
                or stripped == "}"):
                continue

            header_lines.append(line)

        header_code = "\n".join(header_lines)

        # Combine into generated implementation
        sections = [
            "// ========== Generated Container: vec_vec_int ==========",
            "// 2D integer array (vector of vectors) implementation",
            "// Generated inline for this program (no external dependencies)",
            "",
            "// Type definitions and API",
            header_code.strip(),
            "",
            "// Implementation",
            impl_code.strip(),
            "",
            "// ========== End of Generated Container ==========",
            "",
        ]

        return "\n".join(sections)

    def generate_vec_cstr(self) -> str:
        """Generate complete implementation for string arrays (vector of C strings).

        Returns:
            Complete C code for vec_cstr implementation
        """
        # Load templates
        header = self._load_template("mgen_vec_cstr.h")
        implementation = self._load_template("mgen_vec_cstr.c")

        # Strip includes from implementation
        impl_code = self._strip_includes_and_headers(implementation)

        # Remove error handling macros for self-contained code
        impl_code = self._remove_error_handling_macros(impl_code)

        # Strip header guards and includes from header
        header_lines = []
        in_header_guard = False
        for line in header.split("\n"):
            stripped = line.strip()

            # Skip header guards
            if stripped.startswith("#ifndef") and "_H" in stripped:
                in_header_guard = True
                continue
            if stripped.startswith("#define") and "_H" in stripped:
                continue
            if stripped.startswith("#endif") and in_header_guard:
                in_header_guard = False
                continue

            # Skip includes, extern C
            if (stripped.startswith("#include")
                or stripped.startswith("#ifdef __cplusplus")
                or stripped.startswith("extern \"C\"")
                or stripped.startswith("#endif")
                or stripped == "}"):
                continue

            header_lines.append(line)

        header_code = "\n".join(header_lines)

        # Combine into generated implementation
        sections = [
            "// ========== Generated Container: vec_cstr ==========",
            "// String array (vector of C strings) implementation",
            "// Generated inline for this program (no external dependencies)",
            "",
            "// Type definitions and API",
            header_code.strip(),
            "",
            "// Implementation",
            impl_code.strip(),
            "",
            "// ========== End of Generated Container ==========",
            "",
        ]

        return "\n".join(sections)

    def generate_container(self, container_type: str) -> Optional[str]:
        """Generate code for a specific container type.

        Args:
            container_type: Container type identifier (e.g., "map_str_int", "vec_int", "set_int", "map_int_int", "vec_vec_int", "vec_cstr")

        Returns:
            Generated C code, or None if type not supported
        """
        if container_type == "map_str_int":
            return self.generate_str_int_map()
        elif container_type == "vec_int":
            return self.generate_vec_int()
        elif container_type == "set_int":
            return self.generate_set_int()
        elif container_type == "map_int_int":
            return self.generate_map_int_int()
        elif container_type == "vec_vec_int":
            return self.generate_vec_vec_int()
        elif container_type == "vec_cstr":
            return self.generate_vec_cstr()

        return None

    def get_required_includes(self, container_type: str) -> list[str]:
        """Get required includes for a container type.

        Args:
            container_type: Container type identifier

        Returns:
            List of required #include directives
        """
        # str_int_map needs: stdlib.h (malloc/free), string.h (strcmp/strdup)
        # vec_int needs: stdlib.h (malloc/free), stdbool.h (bool)
        # set_int needs: stdlib.h (malloc/free), stdbool.h (bool)
        # map_int_int needs: stdlib.h (malloc/free), stdbool.h (bool)
        # vec_vec_int needs: stdlib.h (malloc/free), stdbool.h (bool)
        # vec_cstr needs: stdlib.h (malloc/free), string.h (strdup), stdbool.h (bool)
        # These are already in standard includes, but we track them for completeness
        if container_type in ["map_str_int", "vec_cstr"]:
            return ["<stdlib.h>", "<string.h>", "<stdbool.h>"]
        elif container_type in ["vec_int", "set_int", "map_int_int", "vec_vec_int"]:
            return ["<stdlib.h>", "<stdbool.h>"]

        return []


# Example usage and testing
if __name__ == "__main__":
    """Test the container code generator."""

    generator = ContainerCodeGenerator()

    # Generate str_int_map implementation
    print("=" * 80)
    print("Testing Container Code Generator - Prototype")
    print("=" * 80)
    print()

    code = generator.generate_str_int_map()

    # Print first 50 lines to verify
    lines = code.split("\n")
    for i, line in enumerate(lines[:50], 1):
        print(f"{i:3}: {line}")

    print(f"\n... ({len(lines) - 50} more lines)")
    print()
    print(f"Total lines generated: {len(lines)}")
    print(f"Total characters: {len(code)}")
    print()
    print("✅ Code generation successful!")
