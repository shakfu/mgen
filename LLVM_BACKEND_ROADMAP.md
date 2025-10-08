# LLVM Backend Development Roadmap

## Current State (Updated: October 2025)

- **Benchmark Status**: 3/7 passing (43%) - fibonacci, list_ops, quicksort
- **Test Coverage**: 70 tests passing (100%, ~2s execution)
- **Runtime Library**: String operations C runtime implemented (split, lower, strip, concat)
- **Container Support**: vec_int (1D lists), vec_vec_int (2D lists), mgen_string_array_t
- **Features Working**:
  - Arithmetic, control flow, functions, loops, booleans
  - Recursion, list operations, list comprehensions
  - String literals, string concatenation, print
  - Global variables, type casting (int/float)
  - Nested loops, break/continue, multiple return paths
- **Architecture**: IR → LLVM IR conversion with C runtime linking

## Passing Benchmarks (3/7)

1. ✅ **fibonacci** - Recursion, loops, arithmetic (514229)
2. ✅ **list_ops** - List comprehensions, append, indexing, len (166750)
3. ✅ **quicksort** - Recursive list operations, slicing (5)

## Failing Benchmarks (4/7)

4. ❌ **matmul** - Type mismatch: `vec_vec_int* != vec_int*` in nested subscripts
5. ❌ **wordcount** - Needs `list[str]` support for split() results
6. ❌ **dict_ops** - No dict support (dict comprehensions, items(), values(), in-operator)
7. ❌ **set_ops** - No set support (set comprehensions, add, remove, membership)

## Recent Progress

### ✅ String Operations Runtime (Oct 2025)
- **Implemented**: `mgen_llvm_string.c/.h` with split(), lower(), strip(), concat()
- **Declared**: String functions in runtime_decls.py (mgen_string_array_t)
- **Integrated**: Builder compiles and links string runtime automatically
- **Limitation**: Needs `list[str]` type support for full functionality

### ✅ 2D List Support
- **Declared**: vec_vec_int struct with push/at/size/free operations
- **Issue**: Type mismatch in nested subscript operations (a[i][k])
- **Status**: Runtime exists but code generation needs fixing

## Next Development Priorities

### 1. Fix Nested Subscript Operations (matmul)

**Problem**: `a[i][k]` generates type mismatch when accessing 2D lists
**Solution**: Handle chained subscript operations in IRToLLVMConverter
**Impact**: Unlocks matmul benchmark (4/7)

**Files to modify:**
- `src/mgen/backends/llvm/ir_to_llvm.py` (visit_function_call for chained __getitem__)

### 2. Implement list[str] Support (wordcount partial)

**Problem**: split() returns string_array but needs list[str] type
**Solution**:
- Add vec_str container type for string lists
- Convert string_array ↔ vec_str in split() handler
- Support string iteration in for loops

**Impact**: Enables split() usage, but wordcount still needs dicts

**Files to modify:**
- `src/mgen/backends/llvm/runtime_decls.py` (vec_str declarations)
- `src/mgen/backends/llvm/runtime/mgen_llvm_list_str.c` (new file)
- `src/mgen/backends/llvm/ir_to_llvm.py` (string list operations)

### 3. Implement Dict Support (wordcount, dict_ops)

**Problem**: No dictionary data structure
**Solution**:
- Implement `map_str_int`, `map_int_int` C runtime
- Add dict comprehensions support
- Support dict.items(), dict.values(), in-operator

**Impact**: Unlocks wordcount + dict_ops (6/7)

**Files to modify:**
- `src/mgen/backends/llvm/runtime_decls.py`
- `src/mgen/backends/llvm/runtime/mgen_llvm_dict.c` (new file)
- `src/mgen/backends/llvm/ir_to_llvm.py`

### 4. Implement Set Support (set_ops)

**Problem**: No set data structure
**Solution**:
- Implement `set_int`, `set_str` C runtime
- Add set comprehensions, add(), remove()
- Support membership testing (in operator)

**Impact**: Unlocks set_ops (7/7)

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

### Phase 1: Quick Wins (1-2 days)
1. **Fix nested subscripts** → 4/7 benchmarks (matmul)
2. **Implement list[str]** → Better string support

### Phase 2: Data Structures (3-5 days)
3. **Dict support** → 6/7 benchmarks (wordcount + dict_ops)
4. **Set support** → 7/7 benchmarks (set_ops)

### Phase 3: Production Ready (Week 2+)
5. **Type inference improvements** (dict/set element types)
6. **Error handling** (better error messages)
7. **Performance optimization** (LLVM passes)
8. **Advanced features** (OOP, modules, file I/O)

## Success Metrics

- ✅ **100% test coverage maintained** (982/982 tests passing)
- ⏳ **Benchmarks**: 3/7 passing (43%) → Target: 7/7 (100%)
- ✅ **Zero external dependencies** (except LLVM tools: llc, clang)
- ✅ **Fast compilation**: 144-260ms (competitive with Go/Rust)
- ✅ **Small binaries**: 33-35KB (competitive with C++)
- ✅ **Type-safe code generation** (llvmlite validation)

## Performance Comparison

| Metric | LLVM | C++ | Go | Rust |
|--------|------|-----|-----|------|
| **Success Rate** | 3/7 (43%) | 7/7 (100%) | 7/7 (100%) | 7/7 (100%) |
| **Avg Compile Time** | 177ms | 422ms | 163ms | 221ms |
| **Avg Binary Size** | 34KB | 36KB | 2.3MB | 446KB |
| **Test Coverage** | 70 tests | - | - | - |

## Notes

- LLVM backend provides opportunities for advanced optimizations
- Can leverage LLVM's extensive optimization passes
- Potential for cross-platform portable binaries
- Foundation for future LLVM-based features (JIT compilation, etc.)
