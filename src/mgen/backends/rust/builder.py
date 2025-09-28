"""Rust build system for MGen."""

import subprocess
from pathlib import Path
from typing import List

from ..base import AbstractBuilder


class RustBuilder(AbstractBuilder):
    """Rust build system implementation using Cargo."""

    def get_build_filename(self) -> str:
        """Return Cargo.toml as the build file name."""
        return "Cargo.toml"

    def generate_build_file(self, source_files: List[str], target_name: str) -> str:
        """Generate Cargo.toml for Rust project."""
        cargo_content = f"""[package]
name = "{target_name}"
version = "0.1.0"
edition = "2021"

[dependencies]
"""
        return cargo_content

    def compile_direct(self, source_file: str, output_path: str) -> bool:
        """Compile Rust source directly using rustc."""
        try:
            source_path = Path(source_file)
            output_dir = Path(output_path)
            executable_name = source_path.stem

            # Build rustc command
            cmd = [
                "rustc",
                str(source_path),
                "-o", str(output_dir / executable_name),
                "--edition", "2021"
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
        """Get Rust compilation flags."""
        return ["--edition", "2021", "-O"]