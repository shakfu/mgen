"""Go build system for MGen."""

import subprocess
from pathlib import Path
from typing import List

from ..base import AbstractBuilder


class GoBuilder(AbstractBuilder):
    """Go build system implementation."""

    def get_build_filename(self) -> str:
        """Return go.mod as the build file name."""
        return "go.mod"

    def generate_build_file(self, source_files: List[str], target_name: str) -> str:
        """Generate go.mod for Go project."""
        go_mod_content = f"""module {target_name}

go 1.21
"""
        return go_mod_content

    def compile_direct(self, source_file: str, output_path: str) -> bool:
        """Compile Go source directly using go build."""
        try:
            source_path = Path(source_file)
            output_dir = Path(output_path)
            executable_name = source_path.stem

            # Build go build command
            cmd = [
                "go",
                "build",
                "-o", str(output_dir / executable_name),
                str(source_path)
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
        """Get Go compilation flags."""
        return ["-ldflags", "-s -w"]  # Strip debug info for smaller binaries
