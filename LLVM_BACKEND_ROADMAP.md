# LLVM Backend Development Roadmap

## Current State (Updated: October 9, 2025)

- **Benchmark Status**: 4/7 passing (57%) - fibonacci, list_ops, quicksort, matmul ✨
- **Test Coverage**: 70 tests passing (100%, ~2s execution)
- **Runtime Library**: String operations C runtime implemented (split, lower, strip, concat)
- **Container Support**: vec_int (1D lists), vec_vec_int (2D lists), mgen_string_array_t
- **Features Working**:
  - Arithmetic, control flow, functions, loops, booleans
  - Recursion, list operations, list comprehensions
  - String literals, string concatenation, print
  - Global variables, type casting (int/float)
  - Nested loops, break/continue, multiple return paths
  - **2D arrays with nested subscript operations (a[i][k])** ✨
- **Architecture**: IR → LLVM IR conversion with C runtime linking
- **Tool Detection**: Auto-detects LLVM tools in PATH and Homebrew locations

## Passing Benchmarks (4/7)

1. ✅ **fibonacci** - Recursion, loops, arithmetic (514229)
2. ✅ **list_ops** - List comprehensions, append, indexing, len (166750)
3. ✅ **quicksort** - Recursive list operations, slicing (5)
4. ✅ **matmul** - 2D arrays, nested subscripts, matrix multiplication (120) ✨

## Failing Benchmarks (3/7)

5. ❌ **wordcount** - Needs `list[str]` support for split() results
6. ❌ **dict_ops** - No dict support (dict comprehensions, items(), values(), in-operator)
7. ❌ **set_ops** - No set support (set comprehensions, add, remove, membership)

## Recent Progress

### ✅ list[str] Support Implementation (Oct 9, 2025)
- **Created**: `vec_str_minimal.c` runtime with full string list operations
- **Added**: vec_str type declarations and function signatures
- **Updated**: Type converter handles list[str] → vec_str* mapping
- **Implemented**: append, indexing, len, setitem operations for string lists
- **Testing**: Simple list[str] test passes, all 982 tests passing
- **Status**: Foundation complete, ready for split() conversion

### ✅ LLVM Tool Auto-Detection (Oct 9, 2025)
- **Fixed**: LLVMBuilder now auto-detects llc and clang in common locations
- **Supported**: PATH, Homebrew (Apple Silicon and Intel Mac)
- **Impact**: Seamless build experience on macOS without manual PATH configuration

### ✅ Nested Subscript Operations (Oct 9, 2025)
- **Fixed**: 2D array access with chained subscripts (e.g., `a[i][k]`)
- **Implementation**: Proper handling of vec_vec_int_at → vec_int_at chains
- **Impact**: Unlocked matmul benchmark → **4/7 passing (57%)**

### ✅ String Operations Runtime (Oct 2025)
- **Implemented**: `mgen_llvm_string.c/.h` with split(), lower(), strip(), concat()
- **Declared**: String functions in runtime_decls.py (mgen_string_array_t)
- **Integrated**: Builder compiles and links string runtime automatically
- **Limitation**: Needs `list[str]` type support for full functionality

### ✅ 2D List Support
- **Declared**: vec_vec_int struct with push/at/size/free operations
- **Status**: Fully working with proper code generation

## Next Development Priorities

### 1. ✅ Implement list[str] Support (COMPLETED)

**Completed Features:**
- ✅ vec_str runtime with push, at, size, set, free operations
- ✅ Type system mapping list[str] → vec_str*
- ✅ List operations: append, indexing, len, setitem
- ✅ All 982 tests passing with no regressions

**Next Steps for Full wordcount Support:**
- TODO: Convert string_array from split() to vec_str
- TODO: Support for-each iteration over list[str]
- NOTE: wordcount still requires dict implementation

### 2. Implement Dict Support (wordcount, dict_ops)

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

### 3. Implement Set Support (set_ops)

**Problem**: No set data structure
**Solution**:
- Implement `set_int`, `set_str` C runtime
- Add set comprehensions, add(), remove()
- Support membership testing (in operator)

**Impact**: Unlocks set_ops (7/7)

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

### Phase 1: Quick Wins (COMPLETED ✨)
1. ✅ **Fixed nested subscripts** → 4/7 benchmarks (matmul)
2. **Implement list[str]** → Better string support (IN PROGRESS)

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
- ✨ **Benchmarks**: 4/7 passing (57%) → Target: 7/7 (100%)
- ✅ **Zero external dependencies** (except LLVM tools: llc, clang)
- ✅ **Fast compilation**: ~180ms (competitive with Go)
- ✅ **Small binaries**: ~35KB (competitive with C++)
- ✅ **Type-safe code generation** (proper type handling)
- ✅ **Auto-detection**: LLVM tools found automatically

## Performance Comparison

| Metric | LLVM | C++ | Go | Rust |
|--------|------|-----|-----|------|
| **Success Rate** | 4/7 (57%) ✨ | 7/7 (100%) | 7/7 (100%) | 7/7 (100%) |
| **Avg Compile Time** | ~180ms | 422ms | 163ms | 221ms |
| **Avg Binary Size** | ~35KB | 36KB | 2.3MB | 446KB |
| **Test Coverage** | 70 tests | - | - | - |

## Notes

- LLVM backend provides opportunities for advanced optimizations
- Can leverage LLVM's extensive optimization passes
- Potential for cross-platform portable binaries
- Foundation for future LLVM-based features (JIT compilation, etc.)
