"""LLVM builder for compilation and execution."""

import subprocess
import tempfile
from pathlib import Path

from ..base import AbstractBuilder


class LLVMBuilder(AbstractBuilder):
    """Builder for compiling LLVM IR to native binaries."""

    def __init__(self) -> None:
        """Initialize the LLVM builder."""
        self.llc_path = "llc"  # LLVM static compiler
        self.clang_path = "clang"  # Clang for linking

    def get_build_filename(self) -> str:
        """Get the build file name.

        Returns:
            Name of build file (Makefile)
        """
        return "Makefile"

    def generate_build_file(self, source_files: list[str], target_name: str) -> str:
        """Generate a Makefile for LLVM IR compilation.

        Args:
            source_files: List of LLVM IR (.ll) files
            target_name: Name of output executable

        Returns:
            Makefile content as string
        """
        ll_files = " ".join(Path(f).name for f in source_files if f.endswith(".ll"))

        makefile = f"""# Generated Makefile for LLVM IR compilation
# Target: {target_name}

LLC = llc
CLANG = clang
TARGET = {target_name}
LLVM_IR = {ll_files}
OBJECT_FILES = $(LLVM_IR:.ll=.o)

# Default target
all: $(TARGET)

# Compile LLVM IR to object files
%.o: %.ll
\t$(LLC) -filetype=obj $< -o $@

# Link object files to create executable
$(TARGET): $(OBJECT_FILES)
\t$(CLANG) $(OBJECT_FILES) -o $(TARGET)

# Clean build artifacts
clean:
\trm -f $(OBJECT_FILES) $(TARGET)

# Run the program
run: $(TARGET)
\t./$(TARGET)

.PHONY: all clean run
"""
        return makefile

    def compile_direct(self, source_file: str, output_dir: str) -> bool:
        """Compile LLVM IR directly to native binary.

        Args:
            source_file: Path to LLVM IR (.ll) file
            output_dir: Directory for output files

        Returns:
            True if compilation succeeded
        """
        try:
            source_path = Path(source_file)
            output_path = Path(output_dir)
            executable_name = source_path.stem

            # Step 1: Compile LLVM IR to object file using llc
            object_file = output_path / f"{executable_name}.o"
            llc_cmd = [
                self.llc_path,
                "-filetype=obj",
                str(source_path),
                "-o",
                str(object_file),
            ]

            result = subprocess.run(llc_cmd, capture_output=True, text=True, cwd=output_path)
            if result.returncode != 0:
                print(f"LLC compilation failed: {result.stderr}")
                return False

            # Step 2: Link object file to create executable using clang
            executable_path = output_path / executable_name
            clang_cmd = [
                self.clang_path,
                str(object_file),
                "-o",
                str(executable_path),
            ]

            result = subprocess.run(clang_cmd, capture_output=True, text=True, cwd=output_path)
            if result.returncode != 0:
                print(f"Linking failed: {result.stderr}")
                return False

            return True

        except FileNotFoundError as e:
            print(f"Tool not found: {e}. Make sure LLVM tools (llc, clang) are installed.")
            return False
        except Exception as e:
            print(f"Compilation error: {e}")
            return False

    def get_compile_flags(self) -> list[str]:
        """Get LLVM compilation flags.

        Returns:
            List of compilation flags
        """
        return [
            "-filetype=obj",  # Generate object file
        ]

    def get_optimization_level(self, level: int = 2) -> list[str]:
        """Get optimization flags for specified level.

        Args:
            level: Optimization level (0-3)

        Returns:
            List of optimization flags
        """
        return [f"-O{level}"]
