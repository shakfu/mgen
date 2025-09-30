"""C++ builder for compilation and build file generation."""

import subprocess
from pathlib import Path
from typing import List, Optional

from ..base import AbstractBuilder


class CppBuilder(AbstractBuilder):
    """Builder for C++ projects."""

    def __init__(self) -> None:
        """Initialize the C++ builder."""
        self.compiler = "g++"
        self.default_flags = ["-std=c++17", "-Wall", "-O2"]
        self.runtime_sources: List[str] = []
        self.runtime_headers_dir: Optional[str] = None

    def get_build_filename(self) -> str:
        """Get the build file name (Makefile for C++)."""
        return "Makefile"

    def generate_build_file(self, source_files: List[str], target_name: str) -> str:
        """Generate a Makefile for the C++ project."""
        sources = " ".join(Path(f).name for f in source_files)

        makefile_content = f"""# Generated Makefile for {target_name}

CXX = {self.compiler}
CXXFLAGS = {' '.join(self.default_flags)}
TARGET = {target_name}
SOURCES = {sources}
OBJECTS = $(SOURCES:.cpp=.o)

# Default target
all: $(TARGET)

# Build the target executable
$(TARGET): $(OBJECTS)
\t$(CXX) $(OBJECTS) -o $(TARGET)

# Compile source files to object files
%.o: %.cpp
\t$(CXX) $(CXXFLAGS) -c $< -o $@

# Clean build artifacts
clean:
\trm -f $(OBJECTS) $(TARGET)

# Force rebuild
rebuild: clean all

# Install (copy to /usr/local/bin)
install: $(TARGET)
\tcp $(TARGET) /usr/local/bin/

# Run the program
run: $(TARGET)
\t./$(TARGET)

# Debug build
debug: CXXFLAGS += -g -DDEBUG
debug: $(TARGET)

# Release build with optimization
release: CXXFLAGS += -O3 -DNDEBUG
release: $(TARGET)

# Show help
help:
\t@echo "Available targets:"
\t@echo "  all      - Build the program (default)"
\t@echo "  clean    - Remove build artifacts"
\t@echo "  rebuild  - Clean and build"
\t@echo "  install  - Install to /usr/local/bin"
\t@echo "  run      - Build and run the program"
\t@echo "  debug    - Build with debug information"
\t@echo "  release  - Build optimized release version"
\t@echo "  help     - Show this help message"

.PHONY: all clean rebuild install run debug release help
"""
        return makefile_content

    def compile_direct(self, source_file: str, output_dir: str) -> bool:
        """Compile C++ source directly to executable."""
        try:
            source_path = Path(source_file)
            output_path = Path(output_dir) / source_path.stem

            # Build the compilation command
            cmd = [self.compiler] + self.default_flags + [str(source_path), "-o", str(output_path)]

            # Execute compilation
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=output_dir)

            if result.returncode == 0:
                return True
            else:
                print(f"C++ compilation failed: {result.stderr}")
                return False

        except Exception as e:
            print(f"C++ compilation error: {e}")
            return False

    def get_executable_name(self, source_file: str) -> str:
        """Get the executable name for a source file."""
        return Path(source_file).stem

    def get_compiler_flags(self) -> List[str]:
        """Get default compiler flags."""
        return self.default_flags.copy()

    def set_compiler(self, compiler: str) -> None:
        """Set the compiler to use."""
        self.compiler = compiler

    def add_flag(self, flag: str) -> None:
        """Add a compiler flag."""
        if flag not in self.default_flags:
            self.default_flags.append(flag)

    def remove_flag(self, flag: str) -> None:
        """Remove a compiler flag."""
        if flag in self.default_flags:
            self.default_flags.remove(flag)

    def set_standard(self, standard: str) -> None:
        """Set the C++ standard (e.g., 'c++11', 'c++14', 'c++17', 'c++20')."""
        # Remove existing standard flags
        self.default_flags = [f for f in self.default_flags if not f.startswith("-std=")]
        # Add new standard
        self.default_flags.append(f"-std={standard}")

    def enable_debug(self) -> None:
        """Enable debug mode."""
        self.add_flag("-g")
        self.add_flag("-DDEBUG")
        # Remove optimization flags
        self.default_flags = [f for f in self.default_flags if not f.startswith("-O")]

    def enable_optimization(self, level: str = "2") -> None:
        """Enable optimization."""
        # Remove existing optimization flags
        self.default_flags = [f for f in self.default_flags if not f.startswith("-O")]
        self.add_flag(f"-O{level}")

    def add_include_directory(self, directory: str) -> None:
        """Add an include directory."""
        self.add_flag(f"-I{directory}")

    def add_library(self, library: str) -> None:
        """Add a library to link."""
        self.add_flag(f"-l{library}")

    def add_library_directory(self, directory: str) -> None:
        """Add a library directory."""
        self.add_flag(f"-L{directory}")

    def generate_cmake_file(self, source_files: List[str], target_name: str) -> str:
        """Generate a CMakeLists.txt file as an alternative to Makefile."""
        sources = "\n    ".join(Path(f).name for f in source_files)

        cmake_content = f"""# Generated CMakeLists.txt for {target_name}

cmake_minimum_required(VERSION 3.10)
project({target_name})

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Add compiler flags
set(CMAKE_CXX_FLAGS "${{CMAKE_CXX_FLAGS}} -Wall")

# Add the executable
add_executable({target_name}
    {sources}
)

# Set output directory
set_target_properties({target_name} PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${{CMAKE_BINARY_DIR}}"
)

# Installation
install(TARGETS {target_name} DESTINATION bin)
"""
        return cmake_content

    def get_compile_flags(self) -> List[str]:
        """Get default compilation flags with runtime includes."""
        flags = self.default_flags.copy()
        if self.runtime_headers_dir:
            flags.append(f"-I{self.runtime_headers_dir}")
        return flags

    def _detect_runtime_sources(self, source_files: List[str]) -> List[str]:
        """Detect if runtime sources are needed based on generated code analysis."""
        runtime_sources: List[str] = []

        # Check if any source files use MGen runtime features
        for source_file in source_files:
            try:
                with open(source_file) as f:
                    content = f.read()
                    # Check for MGen runtime usage patterns
                    if ("mgen_cpp_runtime.hpp" in content or
                        "mgen::" in content or
                        "StringOps::" in content or
                        "Range(" in content or
                        "list_comprehension" in content or
                        "dict_comprehension" in content or
                        "set_comprehension" in content):
                        # Runtime is needed, but it's header-only for C++
                        # Just ensure the include path is set
                        source_dir = Path(source_file).parent
                        runtime_dir = source_dir / "runtime"
                        if runtime_dir.exists():
                            self.runtime_headers_dir = str(runtime_dir)
                        break
            except FileNotFoundError:
                continue

        return runtime_sources

    def _setup_runtime_environment(self, output_dir: str) -> None:
        """Setup runtime environment in the output directory."""
        output_path = Path(output_dir)
        runtime_dir = output_path / "runtime"

        # Create runtime directory if it doesn't exist
        runtime_dir.mkdir(exist_ok=True)

        # Check if we need to copy runtime headers from the backend
        backend_runtime = Path(__file__).parent / "runtime"
        if backend_runtime.exists():
            # Copy runtime headers to build directory
            import shutil
            for header_file in backend_runtime.glob("*.hpp"):
                target_file = runtime_dir / header_file.name
                if not target_file.exists():
                    shutil.copy2(header_file, target_file)

        self.runtime_headers_dir = str(runtime_dir)

    def set_runtime_directory(self, runtime_dir: str) -> None:
        """Set the runtime headers directory."""
        self.runtime_headers_dir = runtime_dir

    def get_runtime_sources(self) -> List[str]:
        """Get list of runtime source files (empty for header-only C++ runtime)."""
        return self.runtime_sources.copy()

    def requires_runtime_library(self, source_files: List[str]) -> bool:
        """Check if the project requires MGen C++ runtime library."""
        runtime_sources = self._detect_runtime_sources(source_files)
        return len(runtime_sources) > 0 or self.runtime_headers_dir is not None
