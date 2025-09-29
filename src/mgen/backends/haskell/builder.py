"""Haskell build system for MGen."""

import subprocess
from pathlib import Path
from typing import List

from ..base import AbstractBuilder


class HaskellBuilder(AbstractBuilder):
    """Haskell build system implementation using Cabal."""

    def get_build_filename(self) -> str:
        """Return cabal project file name."""
        return "mgen-project.cabal"

    def generate_build_file(self, source_files: List[str], target_name: str) -> str:
        """Generate Cabal file for Haskell project."""
        cabal_content = f"""cabal-version: 2.4

name: {target_name}
version: 0.1.0.0
synopsis: Generated Haskell project from MGen
description: Automatically generated Haskell code from Python source using MGen
license: MIT
author: MGen
maintainer: mgen@example.com
build-type: Simple

executable {target_name}
    main-is: Main.hs
    default-language: Haskell2010
    default-extensions:
        OverloadedStrings
        FlexibleInstances
        TypeSynonymInstances
    build-depends:
        base ^>=4.16,
        containers,
        text
    ghc-options:
        -Wall
        -Wcompat
        -Widentities
        -Wincomplete-record-updates
        -Wincomplete-uni-patterns
        -Wmissing-export-lists
        -Wmissing-home-modules
        -Wpartial-fields
        -Wredundant-constraints
"""
        return cabal_content

    def compile_direct(self, source_file: str, output_path: str) -> bool:
        """Compile Haskell source directly using GHC."""
        try:
            source_path = Path(source_file)
            output_dir = Path(output_path)
            executable_name = source_path.stem

            # Check if runtime exists
            runtime_path = source_path.parent / "MGenRuntime.hs"

            # Build GHC command
            cmd = [
                "ghc",
                str(source_path),
                "-o", str(output_dir / executable_name),
                "-XOverloadedStrings",
                "-XFlexibleInstances",
                "-XTypeSynonymInstances"
            ]

            # Add runtime if it exists
            if runtime_path.exists():
                cmd.extend([str(runtime_path)])

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
        """Get Haskell compilation flags."""
        return [
            "-O2",  # Optimization
            "-XOverloadedStrings",
            "-XFlexibleInstances",
            "-XTypeSynonymInstances",
            "-Wall",  # Enable warnings
            "-fwarn-incomplete-patterns"
        ]