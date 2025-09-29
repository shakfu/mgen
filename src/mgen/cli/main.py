#!/usr/bin/env python3
"""MGen - Multi-Language Code Generator CLI.

A streamlined command-line interface that provides easy access to the complete
Python-to-multiple-languages translation pipeline with structured build directory management.

Usage:
    mgen convert input.py --target c      # Convert to C (generates build/src/input.c)
    mgen convert input.py --target rust   # Convert to Rust (generates build/src/input.rs)
    mgen build input.py --target cpp      # Convert to C++ and create Makefile
    mgen build input.py --target go       # Convert to Go and compile
    mgen backends                         # List available language backends
    mgen clean                            # Clean build directory
"""

import argparse
import shutil
import sys
from pathlib import Path
from typing import Optional, List

from ..common import log

# Import the pipeline and backends
from ..pipeline import BuildMode, MGenPipeline, OptimizationLevel, PipelineConfig
from ..backends.registry import registry
from ..backends.preferences import PreferencesRegistry

BUILD_DIR = "build"


class MGenCLI:
    """Multi-language CLI for MGen pipeline operations."""

    def __init__(self):
        """Initialize the CLI."""
        self.log = log.config(self.__class__.__name__)
        self.default_build_dir = Path(BUILD_DIR)

    def create_parser(self) -> argparse.ArgumentParser:
        """Create the argument parser."""
        available_backends = registry.list_backends()
        backends_str = ", ".join(available_backends) if available_backends else "none"

        parser = argparse.ArgumentParser(
            prog="mgen",
            description="MGen - Multi-Language Code Generator for Python",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=f"""
Examples:
  mgen convert my_module.py --target c     # Generate C code in build/src/
  mgen convert my_module.py --target haskell --prefer use_native_comprehensions=true
  mgen build example.py --target haskell --prefer use_native_comprehensions=true --prefer camel_case_conversion=false
  mgen convert my_module.py --target rust  # Generate Rust code in build/src/
  mgen build my_module.py --target go      # Generate Go code and compile
  mgen build my_module.py -m --target cpp  # Generate C++ code and Makefile
  mgen batch --target c                    # Batch translate all files to C
  mgen backends                            # List available language backends
  mgen clean                               # Clean build directory

Available backends: {backends_str}

Build Directory Structure:
  build/
  ├── src/                 # Generated source files
  ├── build_file           # Generated build system (if -m flag used)
  └── executable           # Compiled binary (if compilation enabled)
            """,
        )

        # Global options
        parser.add_argument("--build-dir", "-d", type=str, default="build", help="Build directory (default: build)")
        parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
        parser.add_argument("--target", "-t", type=str, default="c",
                          help=f"Target language (default: c, available: {backends_str})")
        parser.add_argument("--prefer", "-p", action="append", metavar="KEY=VALUE",
                          help="Set backend preferences (e.g., --prefer use_native_comprehensions=true)")

        # Subcommands
        subparsers = parser.add_subparsers(dest="command", help="Available commands")

        # Convert command
        convert_parser = subparsers.add_parser("convert", help="Convert Python to target language")
        convert_parser.add_argument("input_file", help="Python file to convert")
        convert_parser.add_argument(
            "-O",
            "--optimization",
            choices=["none", "basic", "moderate", "aggressive"],
            default="moderate",
            help="Optimization level (default: moderate)",
        )

        # Build command
        build_parser = subparsers.add_parser(
            "build", help="Convert Python to target language and build (compile directly or generate build file)"
        )
        build_parser.add_argument("input_file", help="Python file to convert")
        build_parser.add_argument(
            "-m", "--makefile", action="store_true", help="Generate Makefile instead of compiling directly"
        )
        build_parser.add_argument(
            "-O",
            "--optimization",
            choices=["none", "basic", "moderate", "aggressive"],
            default="moderate",
            help="Optimization level (default: moderate)",
        )
        build_parser.add_argument("--compiler", help="Compiler to use (uses backend default if not specified)")

        # Clean command
        subparsers.add_parser("clean", help="Clean build directory")

        # Backends command
        subparsers.add_parser("backends", help="List available language backends")

        # Batch command
        batch_parser = subparsers.add_parser(
            "batch",
            help="Batch translate all Python files in a directory",
            description="Translate all Python files in a directory to target language in build/src",
        )
        batch_parser.add_argument("-s", "--source-dir", default=".", help="Directory containing Python files to translate (default: current directory)")
        batch_parser.add_argument(
            "-o",
            "--output-dir",
            default="build/src",
            help="Output directory for generated files (default: build/src)",
        )
        batch_parser.add_argument(
            "-c", "--continue-on-error", action="store_true", help="Continue processing other files if one fails"
        )
        batch_parser.add_argument(
            "--summary-only", action="store_true", help="Show only summary statistics, not detailed output"
        )
        batch_parser.add_argument(
            "-O",
            "--optimization",
            choices=["none", "basic", "moderate", "aggressive"],
            default="moderate",
            help="Optimization level (default: moderate)",
        )
        batch_parser.add_argument(
            "-b", "--build", action="store_true", help="Build (compile) files after translation"
        )
        batch_parser.add_argument("--compiler", help="Compiler to use (uses backend default if not specified)")

        return parser

    def get_optimization_level(self, level_str: str) -> OptimizationLevel:
        """Convert string to OptimizationLevel."""
        mapping = {
            "none": OptimizationLevel.NONE,
            "basic": OptimizationLevel.BASIC,
            "moderate": OptimizationLevel.MODERATE,
            "aggressive": OptimizationLevel.AGGRESSIVE,
        }
        return mapping.get(level_str, OptimizationLevel.MODERATE)

    def parse_preferences(self, backend_name: str, preference_args: Optional[List[str]] = None):
        """Parse preference arguments and create backend preferences."""
        # Create default preferences for the backend
        preferences = PreferencesRegistry.create_preferences(backend_name)

        if preference_args:
            for pref_arg in preference_args:
                if "=" not in pref_arg:
                    self.log.warning(f"Ignoring invalid preference format: {pref_arg} (expected KEY=VALUE)")
                    continue

                key, value_str = pref_arg.split("=", 1)
                key = key.strip()
                value_str = value_str.strip()

                # Convert string values to appropriate types
                if value_str.lower() in ("true", "false"):
                    value = value_str.lower() == "true"
                elif value_str.isdigit():
                    value = int(value_str)
                elif "." in value_str and value_str.replace(".", "").isdigit():
                    value = float(value_str)
                else:
                    value = value_str

                preferences.set(key, value)
                self.log.debug(f"Set {backend_name} preference: {key} = {value}")

        return preferences

    def setup_build_directory(self, build_dir: Path) -> None:
        """Set up the build directory structure."""
        # Create build directory structure
        build_dir.mkdir(exist_ok=True)
        src_dir = build_dir / "src"
        src_dir.mkdir(exist_ok=True)

        self.log.debug(f"Build directory: {build_dir}")
        self.log.debug(f"Source directory: {src_dir}")

        if self.verbose:
            self.log.debug(f"Build directory: {build_dir}")
            self.log.debug(f"Source directory: {src_dir}")

    def copy_runtime_libraries(self, build_dir: Path, target_language: str) -> None:
        """Copy relevant runtime library components to build directory."""
        dest_base_dir = build_dir / "src"

        # Only copy C-specific libraries for C target
        if target_language == "c":
            # Copy STC library if available
            src_stc_include_dir = Path(__file__).parent.parent / "ext" / "stc" / "include"
            if src_stc_include_dir.exists():
                dest_stc_dir = dest_base_dir / "stc"
                if dest_stc_dir.exists():
                    shutil.rmtree(dest_stc_dir)

                src_stc_headers = src_stc_include_dir / "stc"
                if src_stc_headers.exists():
                    shutil.copytree(src_stc_headers, dest_stc_dir)
                    self.log.debug(f"Copied STC library to: {dest_stc_dir}")

                # Also copy c11 if it exists
                src_c11_headers = src_stc_include_dir / "c11"
                dest_c11_dir = dest_base_dir / "c11"
                if src_c11_headers.exists():
                    if dest_c11_dir.exists():
                        shutil.rmtree(dest_c11_dir)
                    shutil.copytree(src_c11_headers, dest_c11_dir)
                    self.log.debug(f"Copied C11 library to: {dest_c11_dir}")

            # Copy C runtime library files
            src_runtime_dir = Path(__file__).parent.parent / "runtime"
            if src_runtime_dir.exists():
                c_runtime_files = [
                    "cgen_string_ops.h", "cgen_string_ops.c",
                    "cgen_error_handling.h", "cgen_error_handling.c",
                    "cgen_python_ops.h", "cgen_python_ops.c",
                    "cgen_file_ops.h", "cgen_file_ops.c",
                    "cgen_stc_bridge.h", "cgen_stc_bridge.c",
                    "cgen_memory_ops.h", "cgen_memory_ops.c",
                    "cgen_container_ops.h", "cgen_container_ops.c",
                ]
                for filename in c_runtime_files:
                    src_file = src_runtime_dir / filename
                    if src_file.exists():
                        dest_file = dest_base_dir / filename
                        shutil.copy2(src_file, dest_file)
                        self.log.debug(f"Copied C runtime file: {filename}")

        # For other languages, runtime libraries are typically handled by the language ecosystem
        # (e.g., Cargo for Rust, go mod for Go, standard library for C++)

    def convert_command(self, args) -> int:
        """Execute convert command."""
        input_path = Path(args.input_file)
        if not input_path.exists():
            self.log.error(f"Input file not found: {input_path}")
            return 1

        # Validate target language
        target = args.target
        if not registry.has_backend(target):
            available = ', '.join(registry.list_backends())
            self.log.error(f"Unsupported target language '{target}'. Available: {available}")
            return 1

        # Parse backend preferences
        preferences = self.parse_preferences(target, args.prefer)

        build_dir = Path(args.build_dir)
        self.setup_build_directory(build_dir)

        # Configure pipeline
        config = PipelineConfig(
            optimization_level=self.get_optimization_level(args.optimization),
            output_dir=str(build_dir / "src"),
            build_mode=BuildMode.NONE,
            target_language=target,
            backend_preferences=preferences,
        )

        try:
            # Run multi-language pipeline
            pipeline = MGenPipeline(config)
            result = pipeline.convert(input_path)

            if not result.success:
                self.log.error("Conversion failed")
                for error in result.errors:
                    self.log.error(f"Error: {error}")
                return 1

            source_key = f"{target}_source"
            source_file = result.output_files.get(source_key, "N/A")
            self.log.info(f"Conversion successful! {target.upper()} source: {source_file}")
            if result.warnings:
                for warning in result.warnings:
                    self.log.warning(f"Warning: {warning}")
            return 0

        except Exception as e:
            self.log.error(f"Pipeline error: {e}")
            return 1

    def build_command(self, args) -> int:
        """Execute build command (compile directly or generate build file based on -m flag)."""
        input_path = Path(args.input_file)
        if not input_path.exists():
            self.log.error(f"Input file not found: {input_path}")
            return 1

        # Validate target language
        target = args.target
        if not registry.has_backend(target):
            available = ', '.join(registry.list_backends())
            self.log.error(f"Unsupported target language '{target}'. Available: {available}")
            return 1

        # Parse backend preferences
        preferences = self.parse_preferences(target, args.prefer)

        build_dir = Path(args.build_dir)
        self.setup_build_directory(build_dir)

        # Determine build mode based on -m flag
        if args.makefile:
            build_mode = BuildMode.MAKEFILE
        else:
            build_mode = BuildMode.DIRECT

        # Copy runtime libraries (language-specific)
        self.copy_runtime_libraries(build_dir, target)

        # Configure pipeline
        include_dirs = []
        if target == "c":
            include_dirs = [str(build_dir / "src")]  # Add runtime include path for C

        config = PipelineConfig(
            optimization_level=self.get_optimization_level(args.optimization),
            output_dir=str(build_dir / "src"),
            build_mode=build_mode,
            target_language=target,
            compiler=getattr(args, "compiler", None),  # Use backend default if not specified
            include_dirs=include_dirs,
            backend_preferences=preferences,
        )

        # Run MGen pipeline
        pipeline = MGenPipeline(config)
        result = pipeline.convert(input_path)

        if not result.success:
            error_msg = "Build failed:" if args.makefile else "Compilation failed:"
            self.log.error(error_msg)
            for error in result.errors:
                self.log.error(f"Error: {error}")
            return 1

        if args.makefile:
            # Build file generation mode
            build_file_key = "build_file"
            if build_file_key in result.output_files:
                build_file_src = Path(result.output_files[build_file_key])
                build_file_name = self._get_build_file_name(target)
                build_file_dest = build_dir / build_file_name
                if build_file_src != build_file_dest:
                    shutil.move(str(build_file_src), str(build_file_dest))
                    result.output_files[build_file_key] = str(build_file_dest)

            source_key = f"{target}_source"
            source_file = result.output_files.get(source_key, "N/A")
            build_file = result.output_files.get(build_file_key, "N/A")
            self.log.info(f"Build preparation successful! {target.upper()} source: {source_file}, Build file: {build_file}")
        else:
            # Direct compilation mode
            if result.executable_path:
                exe_src = Path(result.executable_path)
                exe_dest = build_dir / exe_src.name
                if exe_src != exe_dest:
                    shutil.move(str(exe_src), str(exe_dest))
                    result.executable_path = str(exe_dest)

            self.log.info(f"Compilation successful! Executable: {result.executable_path}")

        if result.warnings:
            for warning in result.warnings:
                self.log.warning(f"Warning: {warning}")

        return 0

    def _get_build_file_name(self, target_language: str) -> str:
        """Get the appropriate build file name for the target language."""
        build_file_names = {
            "c": "Makefile",
            "cpp": "Makefile",
            "rust": "Cargo.toml",
            "go": "go.mod",
        }
        return build_file_names.get(target_language, "Makefile")

    def clean_command(self, args) -> int:
        """Execute clean command."""
        build_dir = Path(args.build_dir)

        if build_dir.exists():
            shutil.rmtree(build_dir)
            self.log.info(f"Cleaned build directory: {build_dir}")
        else:
            self.log.info(f"Build directory doesn't exist: {build_dir}")

        return 0

    def batch_command(self, args) -> int:
        """Execute batch command."""
        import os

        # Validate target language
        target = args.target
        if not registry.has_backend(target):
            available = ', '.join(registry.list_backends())
            self.log.error(f"Unsupported target language '{target}'. Available: {available}")
            return 1

        # Parse backend preferences
        preferences = self.parse_preferences(target, args.prefer)

        source_dir = args.source_dir
        output_dir = args.output_dir
        continue_on_error = args.continue_on_error
        summary_only = args.summary_only
        build_after_translation = args.build

        if build_after_translation:
            self.log.info(f"Starting MGen batch translation to {target.upper()} with build")
        else:
            self.log.info(f"Starting MGen batch translation to {target.upper()}")

        # Check if source_dir directory exists
        if not os.path.exists(source_dir):
            self.log.error(f"Source directory not found: {source_dir}")
            return 1

        # Create output directory
        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
            self.log.error(f"Failed to create output directory {output_dir}: {e}")
            return 1

        # If building, set up build directory and copy runtime libraries
        if build_after_translation:
            build_dir = Path(args.build_dir)
            self.setup_build_directory(build_dir)
            self.copy_runtime_libraries(build_dir, target)

        # Find all Python files in source_dir directory
        python_files = []
        for filename in os.listdir(source_dir):
            if filename.endswith(".py"):
                filepath = os.path.join(source_dir, filename)
                python_files.append(filepath)

        if not python_files:
            self.log.warning(f"No Python files found in {source_dir}")
            return 1

        python_files.sort()  # Process in alphabetical order

        self.log.info(f"Batch processing {len(python_files)} files from {source_dir} to {output_dir}")

        # Process each file
        successful_translations = 0
        failed_translations = 0
        successful_builds = 0
        failed_builds = 0
        translation_results = []

        for i, input_file in enumerate(python_files, 1):
            filename = os.path.basename(input_file)
            backend = registry.get_backend(target, preferences)
            output_filename = filename.replace(".py", backend.get_file_extension())
            output_file = os.path.join(output_dir, output_filename)

            if not summary_only:
                self.log.info(f"[{i}/{len(python_files)}] Processing {filename}")

            try:
                # Use the pipeline to convert the file
                if build_after_translation:
                    # Use DIRECT build mode to compile after translation
                    build_dir = Path(args.build_dir)
                    include_dirs = []
                    if target == "c":
                        include_dirs = [str(build_dir / "src")]  # Add runtime include path for C

                    config = PipelineConfig(
                        optimization_level=self.get_optimization_level(args.optimization),
                        output_dir=str(build_dir / "src"),
                        build_mode=BuildMode.DIRECT,
                        target_language=target,
                        compiler=getattr(args, "compiler", None),
                        include_dirs=include_dirs,
                    )
                else:
                    # Translation only mode
                    config = PipelineConfig(
                        optimization_level=self.get_optimization_level(args.optimization),
                        output_dir=output_dir,
                        build_mode=BuildMode.NONE,
                        target_language=target,
                    )

                pipeline = MGenPipeline(config)
                result = pipeline.convert(Path(input_file))

                if result.success:
                    successful_translations += 1

                    # Count lines in generated file
                    generated_file_path = output_file if not build_after_translation else str(build_dir / "src" / output_filename)
                    try:
                        with open(generated_file_path) as f:
                            lines_generated = len(f.readlines())
                    except Exception:
                        lines_generated = 0

                    result_data = {"input": filename, "output": output_filename, "status": "SUCCESS", "lines": lines_generated}

                    # If building, check for executable and track build success
                    if build_after_translation:
                        if result.executable_path:
                            successful_builds += 1
                            result_data["executable"] = Path(result.executable_path).name
                            result_data["status"] = "SUCCESS (BUILT)"
                        else:
                            failed_builds += 1
                            result_data["status"] = "TRANSLATED (BUILD FAILED)"

                    translation_results.append(result_data)

                    if not summary_only:
                        if build_after_translation and result.executable_path:
                            self.log.info(f"{output_filename} ({lines_generated} lines) -> {Path(result.executable_path).name}")
                        else:
                            self.log.info(f"{output_filename} ({lines_generated} lines)")
                else:
                    failed_translations += 1
                    error_msg = "; ".join(result.errors) if result.errors else "Unknown error"
                    translation_results.append(
                        {"input": filename, "output": output_filename, "status": "FAILED", "error": error_msg}
                    )

                    if not summary_only:
                        self.log.error(f"Failed: {error_msg}")

                    if not continue_on_error:
                        self.log.info(
                            f"Stopping due to error in {filename}. Use --continue-on-error to continue processing."
                        )
                        break

            except Exception as e:
                failed_translations += 1
                error_msg = str(e)
                translation_results.append(
                    {"input": filename, "output": output_filename, "status": "FAILED", "error": error_msg}
                )

                if not summary_only:
                    self.log.error(f"Failed: {error_msg}")

                if not continue_on_error:
                    self.log.warn(
                        f"Stopping due to error in {filename}. Use --continue-on-error to continue processing."
                    )
                    break

        # Print summary
        self.log.info(f"Total files processed: {len(translation_results)}")
        self.log.info(f"Successful translations: {successful_translations}")
        self.log.info(f"Failed translations: {failed_translations}")

        if build_after_translation:
            self.log.info(f"Successful builds: {successful_builds}")
            self.log.info(f"Failed builds: {failed_builds}")

        # if failed_translations > 0:
        #     print()
        #     print("Failed translations:")
        #     for result in translation_results:
        #         if result['status'] == 'FAILED':
        #             print(f"  {result['input']}: {result['error']}")

        # if successful_translations > 0:
        #     total_lines = sum(result['lines'] for result in translation_results if result['status'] == 'SUCCESS')
        #     print(f"Total {target.upper()} code lines generated: {total_lines}")

        return 0 if failed_translations == 0 else 1

    def backends_command(self, args) -> int:
        """Execute backends command."""
        available_backends = registry.list_backends()

        if not available_backends:
            self.log.info("No language backends are currently available.")
            return 1

        self.log.info("Available language backends:")
        for backend_name in sorted(available_backends):
            try:
                backend = registry.get_backend(backend_name)  # Use default preferences for listing
                extension = backend.get_file_extension()
                self.log.info(f"  {backend_name:8} - generates {extension} files")
            except Exception as e:
                self.log.warning(f"  {backend_name:8} - error loading: {e}")

        return 0

    def run(self, argv: Optional[list] = None) -> int:
        """Run the CLI."""
        parser = self.create_parser()
        args = parser.parse_args(argv)

        # Set verbose flag
        self.verbose = args.verbose

        # Handle no command
        if not args.command:
            parser.print_help()
            return 1

        # Dispatch to command handlers
        if args.command == "convert":
            return self.convert_command(args)
        elif args.command == "build":
            return self.build_command(args)
        elif args.command == "clean":
            return self.clean_command(args)
        elif args.command == "batch":
            return self.batch_command(args)
        elif args.command == "backends":
            return self.backends_command(args)
        else:
            self.log.error(f"Unknown command: {args.command}")
            return 1


def main(argv: Optional[list] = None) -> int:
    """Main entry point for the CLI."""
    try:
        cli = MGenCLI()
        return cli.run(argv)
    except KeyboardInterrupt:
        try:
            cli.log.error("Interrupted")
        except:
            print("Interrupted")
        return 1
    except Exception as e:
        try:
            cli.log.error(f"Error: {e}")
        except:
            print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
