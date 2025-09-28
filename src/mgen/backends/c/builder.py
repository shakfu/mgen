"""C build system for MGen."""

import subprocess
from pathlib import Path
from typing import List

from ..base import AbstractBuilder


class CBuilder(AbstractBuilder):
    """C build system implementation."""

    def get_build_filename(self) -> str:
        """Return Makefile as the build file name."""
        return "Makefile"

    def generate_build_file(self, source_files: List[str], target_name: str) -> str:
        """Generate Makefile for C project."""
        # Get source file basenames
        source_basenames = [Path(f).name for f in source_files]
        object_files = [f.replace('.c', '.o') for f in source_basenames]

        makefile_content = f"""# Generated Makefile by MGen
CC = gcc
CFLAGS = -Wall -Wextra -std=c99 -O2
TARGET = {target_name}
SOURCES = {' '.join(source_basenames)}
OBJECTS = {' '.join(object_files)}

all: $(TARGET)

$(TARGET): $(OBJECTS)
\t$(CC) $(OBJECTS) -o $(TARGET)

%.o: %.c
\t$(CC) $(CFLAGS) -c $< -o $@

clean:
\trm -f $(OBJECTS) $(TARGET)

.PHONY: all clean
"""
        return makefile_content

    def compile_direct(self, source_file: str, output_path: str) -> bool:
        """Compile C source directly using gcc."""
        try:
            source_path = Path(source_file)
            output_dir = Path(output_path)
            executable_name = source_path.stem

            # Build gcc command
            cmd = [
                "gcc",
                "-Wall", "-Wextra", "-std=c99", "-O2",
                str(source_path),
                "-o", str(output_dir / executable_name)
            ]

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

    def get_compile_flags(self) -> List[str]:
        """Get C compilation flags."""
        return ["-Wall", "-Wextra", "-std=c99", "-O2"]