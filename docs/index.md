# MultiGen Documentation

**MultiGen** (Multi-Language Generator) translates Python code to C, C++, Rust, Go, Haskell, OCaml, LLVM IR, and TypeScript with zero external runtime dependencies.

## Features

- **8 Backends**: C, C++, Rust, Go, Haskell, OCaml, LLVM, TypeScript
- **Formal Verification**: Optional Z3-based memory safety proofs
- **Type Inference**: Automatic type detection for containers and functions
- **Zero Dependencies**: Self-contained runtime libraries
- **1559 Tests**: Comprehensive test suite. The benchmark harness compares generated output
  against CPython's; current pass rates per backend are in the README, and open defects in TODO.md

## Quick Start

Installation:

```bash
pip install multigen
```

Basic Usage:

```bash
# Convert Python to C
multigen convert -t c example.py

# Validate without converting
multigen check example.py

# Build with Makefile generation
multigen build -t c example.py -m
```
