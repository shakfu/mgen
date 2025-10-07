# LLVM Backend Development Roadmap

## Current State

- **Basic functionality working**: arithmetic, control flow, functions, loops, booleans
- **Runtime foundation started**: `vec_int` struct declared with basic operations
- **Test coverage**: 70 tests passing (100%)
- **Architecture**: IR → LLVM IR conversion using llvmlite library

## Next Development Priorities

### 1. Complete Runtime Library Declarations

The `runtime_decls.py` currently has only `vec_int` declarations. Need to add:

- `map_int_int`, `map_str_int`, `map_str_str` (hash maps)
- `set_int`, `set_str` (hash sets)
- String operations beyond literals
- File I/O functions

**Files to modify:**
- `src/mgen/backends/llvm/runtime_decls.py`

### 2. Implement Actual C Runtime

Currently only LLVM IR declarations exist. Need to create the actual C implementations:

- `src/mgen/backends/llvm/runtime/*.c` - C implementations of runtime functions
- Compilation/linking strategy to connect LLVM IR with C runtime
- Similar architecture to C backend's STC-based runtime (~2,500 lines)

**New directory structure:**
```
src/mgen/backends/llvm/runtime/
├── vec_int.c
├── map_int_int.c
├── set_int.c
└── string_ops.c
```

### 3. Data Structures Support

Implement Python data structures in LLVM backend:

- **Lists**: Comprehensions, append, indexing, slicing
- **Dicts**: Creation, get/set, iteration, dict literals
- **Sets**: Add, remove, membership testing, set literals
- Nested containers (2D arrays, list of dicts, etc.)

**Files to modify:**
- `src/mgen/backends/llvm/ir_to_llvm.py` (code generation)
- `src/mgen/backends/llvm/emitter.py` (emit support)

### 4. Advanced Python Features

- **Classes/OOP**: Constructors, methods, inheritance
- **String methods**: split, join, strip, format, replace, etc.
- **Module imports**: Cross-module calls, namespace handling
- **File I/O**: open, read, write, close, with statement

### 5. Benchmark Integration

Add LLVM to the 7-benchmark suite to track progress toward production readiness:

- fibonacci (recursion)
- quicksort (algorithms)
- matmul (2D arrays)
- wordcount (strings, dicts)
- list_ops (list operations)
- dict_ops (dict operations)
- set_ops (set operations)

**Target**: 7/7 benchmarks passing (100%)

**Files to modify:**
- `tests/benchmarks/*/test_*.py`
- `Makefile` (add LLVM benchmark targets)

### 6. Compilation Pipeline

Complete the end-to-end compilation flow:

- Integration with `llc` (LLVM IR → assembly/object files)
- Integration with `clang` for linking with C runtime
- Makefile generation like other backends
- Executable output with proper optimization flags

**Files to modify:**
- `src/mgen/backends/llvm/backend.py`
- `src/mgen/backends/llvm/builder.py`

### 7. Type Inference & Optimization

- Type inference for containers (list[int], dict[str, int])
- LLVM optimization passes integration
- Target-specific optimizations

## Recommended Development Order

1. **Phase 1: Runtime Foundation** (Weeks 1-2)
   - Complete runtime declarations (#1)
   - Implement C runtime library (#2)
   - Basic compilation pipeline (#6)

2. **Phase 2: Data Structures** (Weeks 3-4)
   - Lists implementation (#3)
   - Dicts implementation (#3)
   - Sets implementation (#3)

3. **Phase 3: Benchmarks** (Week 5)
   - Integrate with benchmark suite (#5)
   - Fix failing benchmarks
   - Performance tuning

4. **Phase 4: Advanced Features** (Week 6+)
   - String methods (#4)
   - Module imports (#4)
   - Classes/OOP (#4)

## Success Metrics

- **100% test coverage maintained**
- **7/7 benchmarks passing**
- **Zero external dependencies** (except LLVM tools)
- **Comparable performance** to C/C++ backends
- **Type-safe code generation**

## Notes

- LLVM backend provides opportunities for advanced optimizations
- Can leverage LLVM's extensive optimization passes
- Potential for cross-platform portable binaries
- Foundation for future LLVM-based features (JIT compilation, etc.)
