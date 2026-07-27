"""TypeScript build system for MultiGen (Deno toolchain)."""

import shutil
from typing import Any

from ..base import AbstractBuilder


class TypeScriptBuilder(AbstractBuilder):
    """TypeScript build system implementation using Deno.

    ``deno compile`` runs the ``.ts`` source directly (no separate emit step)
    and produces a standalone binary, so the compile-time / binary-size /
    execute-time model maps 1:1 onto the other backends.
    """

    def get_build_filename(self) -> str:
        """Return deno.json as the build file name."""
        return "deno.json"

    def generate_build_file(self, source_files: list[str], target_name: str) -> str:
        """Generate deno.json for the TypeScript project."""
        return '{\n  "compilerOptions": {\n    "strict": true\n  }\n}\n'

    def compile_direct(self, source_file: str, output_dir: str, **kwargs: Any) -> bool:
        """Compile TypeScript source directly using ``deno compile``."""
        paths = self._resolve_paths(source_file, output_dir)

        # Copy the runtime module next to the source so the relative
        # import ("./multigen_ts_runtime") resolves at compile time.
        runtime_dir = self._get_runtime_dir()
        if runtime_dir:
            runtime_src = runtime_dir / "multigen_ts_runtime.ts"
            if runtime_src.exists():
                shutil.copy2(runtime_src, paths.source_path.parent / "multigen_ts_runtime.ts")

        cmd = [
            "deno",
            "compile",
            "--no-check",
            "-o",
            str(paths.executable_path),
            str(paths.source_path),
        ]
        return self._run_command(cmd).success

    def get_compile_flags(self) -> list[str]:
        """Get TypeScript compilation flags."""
        return []
