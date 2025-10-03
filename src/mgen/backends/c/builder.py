"""C build system for MGen with integrated runtime libraries."""

import subprocess
from pathlib import Path

from ..base import AbstractBuilder


class CBuilder(AbstractBuilder):
    """C build system implementation with integrated runtime libraries."""

    def __init__(self) -> None:
        """Initialize builder with runtime support."""
        self.runtime_dir = Path(__file__).parent / "runtime"
        self.use_runtime = self.runtime_dir.exists()

    def get_build_filename(self) -> str:
        """Return Makefile as the build file name."""
        return "Makefile"

    def generate_build_file(self, source_files: list[str], target_name: str) -> str:
        """Generate Makefile for C project with MGen runtime support."""
        # Get source file basenames
        source_basenames = [Path(f).name for f in source_files]
        object_files = [f.replace(".c", ".o") for f in source_basenames]

        # Add MGen runtime sources if available
        runtime_sources = []
        runtime_objects = []
        include_flags = []

        if self.use_runtime:
            runtime_sources = self.get_runtime_sources()
            runtime_objects = [Path(src).name.replace(".c", ".o") for src in runtime_sources]
            include_flags.append(f"-I{self.runtime_dir}")
            # Add include path for STC headers
            stc_include_dir = Path(__file__).parent / "ext" / "stc" / "include"
            if stc_include_dir.exists():
                include_flags.append(f"-I{stc_include_dir}")

        all_sources = source_basenames + [Path(src).name for src in runtime_sources]
        all_objects = object_files + runtime_objects

        # Build compiler flags
        base_flags = "-Wall -Wextra -std=c11 -O2"
        if include_flags:
            base_flags += " " + " ".join(include_flags)

        makefile_content = f"""# Generated Makefile by MGen with runtime support
CC = gcc
CFLAGS = {base_flags}
TARGET = {target_name}
SOURCES = {' '.join(all_sources)}
OBJECTS = {' '.join(all_objects)}

all: $(TARGET)

$(TARGET): $(OBJECTS)
\t$(CC) $(OBJECTS) -o $(TARGET)

%.o: %.c
\t$(CC) $(CFLAGS) -c $< -o $@

clean:
\trm -f $(OBJECTS) $(TARGET)

.PHONY: all clean
"""

        # Add development targets
        if self.use_runtime:
            makefile_content += """
# Development targets
test: $(TARGET)
\t./$(TARGET)

debug: CFLAGS += -g -DDEBUG
debug: clean $(TARGET)

release: CFLAGS += -O3 -DNDEBUG
release: clean $(TARGET)

.PHONY: test debug release
"""

        return makefile_content

    def compile_direct(self, source_file: str, output_path: str) -> bool:
        """Compile C source directly using gcc with MGen runtime support."""
        try:
            source_path = Path(source_file)
            output_dir = Path(output_path)
            executable_name = source_path.stem

            # Build gcc command with base flags
            cmd = [
                "gcc",
                "-Wall", "-Wextra", "-std=c11", "-O2",
            ]

            # Add MGen runtime support if available
            if self.use_runtime:
                # Add include path for runtime
                cmd.append(f"-I{self.runtime_dir}")
                # Add include path for STC headers
                stc_include_dir = Path(__file__).parent / "ext" / "stc" / "include"
                if stc_include_dir.exists():
                    cmd.append(f"-I{stc_include_dir}")

                # Add runtime sources
                cmd.extend(self.get_runtime_sources())

            # Add main source file and output
            cmd.extend([
                str(source_path),
                "-o", str(output_dir / executable_name)
            ])

            # Run compilation
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=output_dir
            )

            return result.returncode == 0

        except Exception:
            return False

    def get_compile_flags(self) -> list[str]:
        """Get C compilation flags including MGen runtime support."""
        flags = ["-Wall", "-Wextra", "-std=c11", "-O2"]

        if self.use_runtime:
            # Add include path for runtime
            flags.append(f"-I{self.runtime_dir}")
            # Add include path for STC headers
            stc_include_dir = Path(__file__).parent / "ext" / "stc" / "include"
            if stc_include_dir.exists():
                flags.append(f"-I{stc_include_dir}")

        return flags

    def get_runtime_sources(self) -> list[str]:
        """Get MGen runtime source files for compilation."""
        if not self.use_runtime:
            return []

        runtime_sources = []
        for source_file in self.runtime_dir.glob("*.c"):
            runtime_sources.append(str(source_file))

        return runtime_sources

    def get_runtime_headers(self) -> list[str]:
        """Get MGen runtime header files for inclusion."""
        if not self.use_runtime:
            return []

        runtime_headers = []
        for header_file in self.runtime_dir.glob("*.h"):
            runtime_headers.append(header_file.name)

        return runtime_headers
