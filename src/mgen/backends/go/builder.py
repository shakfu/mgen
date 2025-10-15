"""Go build system for MGen."""

import shutil
import subprocess
from pathlib import Path
from typing import Any

from ..base import AbstractBuilder


class GoBuilder(AbstractBuilder):
    """Go build system implementation."""

    def get_build_filename(self) -> str:
        """Return go.mod as the build file name."""
        return "go.mod"

    def generate_build_file(self, source_files: list[str], target_name: str) -> str:
        """Generate go.mod for Go project."""
        # Use a standard module name for all mgen projects
        go_mod_content = """module mgenproject

go 1.21
"""
        return go_mod_content

    def compile_direct(self, source_file: str, output_dir: str, **kwargs: Any) -> bool:
        """Compile Go source directly using go build."""
        try:
            source_path = Path(source_file)
            out_dir = Path(output_dir)
            executable_name = source_path.stem

            # Create go.mod file for module support
            go_mod_path = out_dir / "go.mod"
            go_mod_content = self.generate_build_file([str(source_path)], executable_name)
            go_mod_path.write_text(go_mod_content)

            # Copy runtime package if it exists
            runtime_src = Path(__file__).parent / "runtime" / "mgen_go_runtime.go"
            if runtime_src.exists():
                # Create mgen package directory
                mgen_pkg_dir = out_dir / "mgen"
                mgen_pkg_dir.mkdir(exist_ok=True)
                runtime_dst = mgen_pkg_dir / "mgen.go"
                shutil.copy2(runtime_src, runtime_dst)

            # Build go build command
            cmd = ["go", "build", "-o", str(out_dir / executable_name), str(source_path)]

            # Run compilation
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=output_dir)

            return result.returncode == 0

        except Exception:
            return False

    def get_compile_flags(self) -> list[str]:
        """Get Go compilation flags."""
        return ["-ldflags", "-s -w"]  # Strip debug info for smaller binaries
