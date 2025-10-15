# MGen LLVM Backend - Complete User Guide

**Last Updated**: October 15, 2025
**Version**: v0.1.83
**Status**: Production Ready

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Features & Capabilities](#features--capabilities)
4. [Compilation Modes](#compilation-modes)
5. [String Operations](#string-operations)
6. [Memory Safety](#memory-safety)
7. [Performance](#performance)
8. [Error Handling](#error-handling)
9. [Advanced Usage](#advanced-usage)
10. [Troubleshooting](#troubleshooting)
11. [Architecture](#architecture)

---

## Overview

The LLVM backend is MGen's **6th production-ready backend**, generating native executables via LLVM IR. It offers unique advantages:

### Key Strengths

- **2nd fastest execution** (152.9ms average)
- **2nd smallest binaries** (37KB average)
- **Most complete string API** (9 methods)
- **Memory-safe** (ASAN verified, 0 leaks)
- **Dual compilation modes** (AOT + JIT)
- **Platform-independent** (via LLVM)
- **Better error messages** (descriptive runtime errors)

### Production Status

[x] **7/7 benchmarks passing** (100% coverage)
[x] **107 comprehensive tests** (100% pass rate)
[x] **0 memory leaks** (ASAN verified)
[x] **0 memory errors** (use-after-free, overflow, etc.)
[x] **~8,300 lines** runtime library (verified)

---

## Quick Start

### Prerequisites

```bash
# Install LLVM tools (required for AOT mode)
# macOS (Homebrew)
brew install llvm

# Ubuntu/Debian
sudo apt-get install llvm clang

# The tools needed are:
# - llc (LLVM static compiler)
# - clang (C compiler for linking)
```

### Basic Usage

```bash
# Convert Python to LLVM IR
mgen convert --target llvm program.py

# Build executable (AOT mode)
mgen build --target llvm program.py

# Generated files:
# - program.ll      (LLVM IR)
# - program.o       (object file)
# - program         (executable)
```

### Hello World Example

```python
# hello.py
def main() -> int:
    print("Hello from LLVM!")
    return 0
```

```bash
# Compile and run
mgen build --target llvm hello.py
./build/hello
```

---

## Features & Capabilities

### Supported Python Features

**Core Language**:
- [x] Functions and recursion
- [x] Control flow (if/elif/else, while, for)
- [x] Type annotations
- [x] Global variables
- [x] Arithmetic operations
- [x] Boolean operations
- [x] Comparison operations

**Data Structures**:
- [x] Lists (`vec_int`, `vec_str`, `vec_vec_int`)
- [x] Dicts (`map_int_int`, `map_str_int`)
- [x] Sets (`set_int`)
- [x] Strings (full support)
- [x] 2D arrays (nested lists)

**String Operations** (9 methods - most complete):
- [x] `split()` - split by delimiter
- [x] `lower()` - lowercase conversion
- [x] `strip()` - remove whitespace
- [x] `upper()` - uppercase conversion
- [x] `join()` - join string array
- [x] `replace()` - replace substring
- [x] `startswith()` - prefix check
- [x] `endswith()` - suffix check
- [x] Concatenation with `+`

**Built-in Functions**:
- [x] `len()` - length of containers/strings
- [x] `range()` - iteration ranges
- [x] `print()` - formatted output
- [x] `min()`, `max()`, `sum()` - aggregations
- [x] `abs()` - absolute value

**Advanced Features**:
- [x] List comprehensions
- [x] Dict comprehensions
- [x] Set comprehensions
- [x] Nested containers
- [x] Container methods (append, get, contains)

### Current Limitations

- [X] Classes/OOP (limited support)
- [X] File I/O operations
- [X] Module imports
- [X] Exception handling
- [X] Generators
- [X] Dict methods (keys, values, items)

---

## Compilation Modes

The LLVM backend supports two compilation modes with different trade-offs:

### AOT (Ahead-of-Time) Mode - Default

**Best for**: Production deployments

```bash
# Standard compilation
mgen build --target llvm program.py

# With optimization
export LLVM_OPTIMIZATION_LEVEL=3  # O0, O1, O2, O3
mgen build --target llvm program.py
```

**Characteristics**:
- Generates standalone executable
- Small binary size (37KB average)
- Fast execution (152.9ms average)
- No runtime dependencies
- Slower compilation (330ms average)

**Pipeline**: Python → Static IR → LLVM IR → Object File → Executable

### JIT (Just-in-Time) Mode

**Best for**: Development and testing

```python
from mgen.backends.llvm.jit_executor import jit_compile_and_run

# Execute LLVM IR directly
result = jit_compile_and_run("program.ll", verbose=True)
print(f"Result: {result}")
```

**Characteristics**:
- **7.7x faster** total time
- No intermediate files
- In-memory execution
- Great for rapid iteration
- Requires llvmlite runtime

**Performance Comparison**:

| Metric | AOT Mode | JIT Mode |
|--------|----------|----------|
| Compilation | 330.7ms | ~50ms |
| Execution | 152.9ms | Similar |
| Total | 483.6ms | ~200ms |
| Speedup | 1.0x | **2.4x** |
| Binary | Yes | No |

---

## String Operations

The LLVM backend has the **most complete string API** among all MGen backends:

### Basic Operations

```python
def string_demo() -> int:
    # Concatenation
    s1: str = "Hello"
    s2: str = "World"
    result: str = s1 + " " + s2  # "Hello World"

    # Length
    length: int = len(result)  # 11

    # Case conversion
    upper: str = result.upper()  # "HELLO WORLD"
    lower: str = result.lower()  # "hello world"

    # Whitespace removal
    padded: str = "  hello  "
    clean: str = padded.strip()  # "hello"

    return 0
```

### String Methods (v0.1.83)

```python
def advanced_strings() -> int:
    text: str = "hello,world,python"

    # Split by delimiter
    parts: list[str] = text.split(",")  # ["hello", "world", "python"]

    # Join with separator
    joined: str = "-".join(parts)  # "hello-world-python"

    # Replace substring
    replaced: str = text.replace("hello", "goodbye")  # "goodbye,world,python"

    # Prefix/suffix checking
    starts: bool = text.startswith("hello")  # True
    ends: bool = text.endswith("python")     # True

    return 0
```

### String Array Operations

```python
def string_arrays() -> int:
    # Create string list
    words: list[str] = ["apple", "banana", "cherry"]

    # Iterate and process
    for word in words:
        upper_word: str = word.upper()
        print(upper_word)

    # Join into single string
    result: str = ", ".join(words)  # "apple, banana, cherry"

    return 0
```

---

## Memory Safety

The LLVM backend is **memory-safe** with comprehensive verification:

### ASAN Verification (v0.1.82)

All benchmarks pass with zero issues:

```bash
# Run memory tests
make test-memory-llvm

# Results:
# [x] fibonacci      - 0 leaks, 0 errors
# [x] matmul         - 0 leaks, 0 errors
# [x] quicksort      - 0 leaks, 0 errors
# [x] wordcount      - 0 leaks, 0 errors
# [x] list_ops       - 0 leaks, 0 errors
# [x] dict_ops       - 0 leaks, 0 errors
# [x] set_ops        - 0 leaks, 0 errors
```

### Runtime Library

- **~8,300 lines** of C runtime code
- **Zero external dependencies** (except libc)
- **Verified memory-safe** via AddressSanitizer
- **Manual memory management** with proper cleanup

### Memory Model

```c
// All containers use explicit allocation/deallocation
vec_int* list = vec_int_init_ptr();
vec_int_push(list, 42);
vec_int_free(list);  // Must call to avoid leaks

// Strings are allocated and must be freed
char* result = mgen_str_upper("hello");
free(result);  // Generated code handles this
```

---

## Performance

### Execution Speed

**2nd fastest** among all backends:

| Rank | Backend | Avg Time | vs LLVM |
|------|---------|----------|---------|
| 1 | Go | 64.5ms | 2.4x faster |
| **2** | **LLVM** | **152.9ms** | **baseline** |
| 3 | Rust | 249.3ms | 1.6x slower |
| 4 | C++ | 254.9ms | 1.7x slower |
| 5 | C | 256.2ms | 1.7x slower |

### Binary Size

**2nd smallest** binaries:

| Rank | Backend | Avg Size |
|------|---------|----------|
| 1 | C++ | 36.1KB |
| **2** | **LLVM** | **37.0KB** |
| 3 | C | 65.6KB |
| 4 | Rust | 446.1KB |
| 5 | OCaml | 811.2KB |

### Compilation Speed

| Backend | Avg Time |
|---------|----------|
| Go | 82.0ms (fastest) |
| Rust | 218.8ms |
| OCaml | 258.1ms |
| **LLVM** | **330.7ms** |
| C | 384.1ms |
| C++ | 396.4ms |

### Optimization Levels

```bash
# Set optimization level (O0, O1, O2, O3)
export LLVM_OPTIMIZATION_LEVEL=3
mgen build --target llvm program.py

# O0: No optimization (fastest compile)
# O1: Basic optimization
# O2: Moderate optimization (default)
# O3: Aggressive optimization (best runtime)
```

**Optimization Impact**:
- O0 → O3: 10-30% faster execution
- O0 → O3: 20-40% longer compilation
- Binary size: mostly unchanged

---

## Error Handling

The LLVM backend provides **descriptive error messages** (v0.1.83):

### Runtime Errors

**Before (v0.1.82)**:
```
exit(1)  // Silent crash, no information
```

**After (v0.1.83)**:
```
vec_int error: Index 5 out of bounds (size = 3)
map_int_int error: NULL pointer passed to map_int_int_set
set_int error: Failed to allocate entry for value 42
```

### Error Message Format

All runtime errors follow this pattern:
```
{container_type} error: {specific_message}
```

### Common Error Types

1. **NULL Pointer Errors**:
```
vec_int error: NULL pointer passed to vec_int_push
```

2. **Index Out of Bounds**:
```
vec_int error: Index 10 out of bounds (size = 5)
```

3. **Memory Allocation Failures**:
```
map_str_int error: Failed to allocate memory for capacity 1024
```

4. **Container Full Errors**:
```
map_int_int error: Failed to find entry slot (map full)
```

### Debugging Tips

```bash
# Enable AddressSanitizer for detailed error reports
export ASAN_OPTIONS=detect_leaks=1:symbolize=1
mgen build --target llvm --enable-asan program.py

# Run with verbose output
./build/program 2>&1 | tee error.log
```

---

## Advanced Usage

### Container Operations

```python
def container_demo() -> int:
    # Lists
    numbers: list[int] = [1, 2, 3, 4, 5]
    numbers.append(6)
    first: int = numbers[0]
    length: int = len(numbers)

    # 2D arrays
    matrix: list[list[int]] = [[1, 2], [3, 4]]
    value: int = matrix[0][1]  # 2

    # Dicts
    scores: dict[str, int] = {"alice": 95, "bob": 87}
    scores["charlie"] = 92
    alice_score: int = scores["alice"]

    # Sets
    unique: set[int] = {1, 2, 3, 2, 1}  # {1, 2, 3}
    unique.add(4)
    has_two: bool = 2 in unique

    return 0
```

### Comprehensions

```python
def comprehension_demo() -> int:
    # List comprehension
    squares: list[int] = [x * x for x in range(10)]

    # Dict comprehension
    square_map: dict[int, int] = {x: x * x for x in range(5)}

    # Set comprehension
    even_set: set[int] = {x for x in range(10) if x % 2 == 0}

    # Nested comprehension
    matrix: list[list[int]] = [[i + j for j in range(3)] for i in range(3)]

    return 0
```

### Recursion

```python
def fibonacci(n: int) -> int:
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

def main() -> int:
    result: int = fibonacci(10)  # 55
    print(result)
    return 0
```

---

## Troubleshooting

### Common Issues

#### 1. LLVM Tools Not Found

**Error**: `llc: command not found`

**Solution**:
```bash
# macOS - add Homebrew LLVM to PATH
export PATH="/opt/homebrew/opt/llvm/bin:$PATH"

# Or set explicitly
export LLVM_LLC_PATH=/opt/homebrew/opt/llvm/bin/llc
export LLVM_CLANG_PATH=/opt/homebrew/opt/llvm/bin/clang
```

#### 2. Compilation Fails

**Error**: IR verification failed

**Solution**:
```bash
# Check LLVM IR syntax
cat build/program.ll | llc -verify-machineinstrs

# Enable verbose output
mgen build --target llvm --verbose program.py
```

#### 3. Runtime Crashes

**Error**: Segmentation fault

**Solution**:
```bash
# Enable AddressSanitizer
mgen build --target llvm --enable-asan program.py

# Run and check output
./build/program 2>&1 | grep "ERROR:"
```

#### 4. Performance Issues

**Problem**: Slow execution

**Solution**:
```bash
# Use O3 optimization
export LLVM_OPTIMIZATION_LEVEL=3
mgen build --target llvm program.py

# Or switch to JIT mode for development
python -m mgen.backends.llvm.jit_executor program.ll
```

### Getting Help

1. Check error messages (v0.1.83+) for specific issues
2. Enable verbose mode: `--verbose`
3. Run memory tests: `make test-memory-llvm`
4. Review generated IR: `cat build/program.ll`
5. File issues: [GitHub Issues](https://github.com/anthropics/mgen/issues)

---

## Architecture

### Compilation Pipeline

```
Python Source Code
       ↓
   AST Parsing
       ↓
  Static IR (type-checked, optimized)
       ↓
  LLVM IR Generation
       ↓
     llc (LLVM Static Compiler)
       ↓
  Object File (.o)
       ↓
    clang (Linker)
       ↓
Native Executable
```

### Runtime Library Structure

```
src/mgen/backends/llvm/runtime/
├── vec_int_minimal.c          # List[int] operations
├── vec_str_minimal.c          # List[str] operations
├── vec_vec_int_minimal.c      # List[List[int]] operations
├── map_int_int_minimal.c      # Dict[int, int] operations
├── map_str_int_minimal.c      # Dict[str, int] operations
├── set_int_minimal.c          # Set[int] operations
├── mgen_llvm_string.c         # String operations (9 methods)
└── mgen_llvm_string.h         # String API declarations
```

### Key Components

1. **IRToLLVMConverter** (`ir_to_llvm.py`)
   - Converts Static IR to LLVM IR
   - ~4,000 lines of Python code
   - Handles all language features

2. **Runtime Declarations** (`runtime_decls.py`)
   - LLVM IR function declarations
   - Type definitions for containers
   - Links to C runtime

3. **LLVM Compiler** (`compiler.py`)
   - Compiles IR to native code
   - Handles llc/clang invocation
   - Manages optimization levels

4. **LLVM Builder** (`builder.py`)
   - Build system integration
   - Makefile generation
   - Dependency tracking

5. **JIT Executor** (`jit_executor.py`)
   - In-memory execution
   - llvmlite integration
   - Fast development cycles

### Type System

```
Python Type          LLVM Type           C Runtime Type
-----------          ---------           --------------
int                  i64                 long long
float                double              double
bool                 i1                  bool
str                  i8*                 char*
list[int]            %struct.vec_int*    vec_int*
dict[int, int]       %struct.map_int*    map_int_int*
set[int]             %struct.set_int*    set_int*
```

---

## Additional Resources

### Documentation

- [Backend Comparison](backend_comparison.md) - Compare all 7 backends
- [Memory Testing Guide](dev/llvm_memory_testing.md) - ASAN usage
- [JIT Mode Details](dev/llvm_jit.md) - JIT compilation
- [Production Roadmap](../PRODUCTION_ROADMAP.md) - Future plans

### Development

- [Architecture Overview](dev/ir_to_llvm_ir.md) - Design decisions
- [Runtime Implementation](../src/mgen/backends/llvm/runtime/) - C code
- [Test Suite](../tests/test_backend_llvm*.py) - 107 tests
- [String Method Tests](../tests/test_llvm_string_methods.py) - 20 tests

### Examples

See `tests/benchmarks/algorithms/` for working examples:
- `fibonacci.py` - Recursion
- `matmul.py` - 2D arrays
- `quicksort.py` - List operations
- `wordcount.py` - String processing
- `list_ops.py` - List comprehensions
- `dict_ops.py` - Dictionary operations
- `set_ops.py` - Set operations

---

## Changelog

### v0.1.83 (October 15, 2025)

- [x] **5 new string methods** (join, replace, upper, startswith, endswith)
- [x] **Better error messages** (descriptive runtime errors)
- [x] **107 comprehensive tests** (723% increase)
- [x] **Most complete string API** among all backends

### v0.1.82 (October 15, 2025)

- [x] **Memory safety verification** (ASAN integration)
- [x] **0 memory leaks** across all benchmarks
- [x] **Automated memory testing** infrastructure
- [x] **Production-ready status** achieved

### v0.1.80 (October 2025)

- [x] **7/7 benchmarks passing** (100% coverage)
- [x] **Container runtime complete** (~8,300 lines)
- [x] **JIT compilation mode** (7.7x faster dev cycle)
- [x] **Production-ready** backend

---

**Last Updated**: October 15, 2025
**Maintained By**: MGen Team
**Status**: Production Ready
