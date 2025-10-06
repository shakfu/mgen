# Backend Selection Guide

**MGen** supports 6 production-ready backends, each with unique strengths and trade-offs. This guide helps you choose the right backend for your use case.

---

## Quick Decision Matrix

| **Priority** | **Recommended Backend** | **Why** |
|-------------|------------------------|---------|
| **Fastest execution** | Go | 3x faster than other backends (avg 45ms vs 140-270ms) |
| **Smallest binary** | C++ | 34-42KB (17x smaller than C, 65x smaller than Go) |
| **Fastest compilation** | Go | 5-8x faster compilation (63ms vs 200-500ms) |
| **Most compact code** | OCaml/Haskell | ~25 LOC average (vs 35-75 LOC) |
| **Memory safety** | Rust | Ownership system prevents use-after-free, data races |
| **Embedding in C** | C | Direct C interop, no runtime required |
| **Systems programming** | Rust or C++ | Low-level control, zero-cost abstractions |
| **Cloud/microservices** | Go | Fast builds, efficient concurrency primitives |
| **Functional paradigm** | Haskell or OCaml | Pure functions, immutability, type inference |
| **Cross-platform** | C++ or Rust | Best portability across architectures |

---

## Performance Comparison

Based on 7 real-world benchmarks (fibonacci, quicksort, matmul, wordcount, list_ops, dict_ops, set_ops):

### Compilation Time

| Backend | Avg Compile Time | Relative Speed | Notes |
|---------|-----------------|----------------|-------|
| **Go** | **63ms** | 1.0x (baseline) | Fastest - incremental compilation |
| **Rust** | 198ms | 3.1x slower | Moderate - LLVM backend |
| **OCaml** | 233ms | 3.7x slower | Fast - native code compiler |
| **C** | 375ms | 6.0x slower | Slower - large runtime library |
| **C++** | 402ms | 6.4x slower | Slower - template instantiation |
| **Haskell** | 504ms | 8.0x slower | Slowest - GHC optimization passes |

**Winner**: Go (63ms average, 51ms best case)

### Execution Time

| Backend | Avg Run Time | Relative Speed | Notes |
|---------|--------------|----------------|-------|
| **Go** | **46ms** | 1.0x (baseline) | Fastest - optimized runtime, GC |
| **C++** | 139ms | 3.0x slower | Fast - STL optimizations |
| **C** | 142ms | 3.1x slower | Fast - manual memory management |
| **Rust** | 153ms | 3.3x slower | Fast - LLVM optimizations |
| **OCaml** | 166ms | 3.6x slower | Moderate - functional overhead |
| **Haskell** | 274ms | 6.0x slower | Slower - lazy evaluation, purity |

**Winner**: Go (46ms average, 44ms best case)

### Binary Size

| Backend | Avg Binary Size | Relative Size | Notes |
|---------|----------------|---------------|-------|
| **C++** | **36KB** | 1.0x (baseline) | Smallest - header-only runtime |
| **C** | 66KB | 1.8x larger | Small - static linking |
| **Rust** | 446KB | 12.4x larger | Moderate - std library included |
| **OCaml** | 811KB | 22.5x larger | Large - runtime + bytecode |
| **Go** | 2.3MB | 64x larger | Largest - full runtime + GC |
| **Haskell** | 19.3MB | 536x larger | Very large - GHC runtime + libs |

**Winner**: C++ (36KB average, 34KB best case)

### Code Generation (Lines of Code)

| Backend | Avg LOC | Relative Verbosity | Code Style |
|---------|---------|-------------------|-----------|
| **OCaml** | **26** | 1.0x (baseline) | Functional, concise |
| **Haskell** | 27 | 1.04x | Functional, type inference |
| **Rust** | 36 | 1.38x | Imperative, ownership annotations |
| **Go** | 37 | 1.42x | Imperative, explicit |
| **C++** | 49 | 1.88x | OOP, template usage |
| **C** | 77 | 2.96x | Procedural, manual containers |

**Winner**: OCaml (26 LOC average, 15 LOC best case)

---

## Backend Profiles

### C++ - Balanced Performance & Size

**Status**: ✅ Production Ready (7/7 benchmarks)

**Strengths**:
- **Smallest binaries** (34-42KB) - ideal for embedded systems
- **Fast execution** (139ms avg) - STL optimizations
- **Mature ecosystem** - extensive libraries, tooling
- **Zero-cost abstractions** - templates, inline functions
- **Cross-platform** - excellent portability

**Weaknesses**:
- Slower compilation (402ms avg)
- Manual memory management (potential leaks)
- Complex generated code (49 LOC avg)

**Best For**:
- Embedded systems (size-constrained environments)
- High-performance applications
- Integration with existing C++ codebases
- Cross-platform deployment

**Runtime**: 357-line header-only library, pure STL

**Example Use Cases**:
- Embedded device firmware
- Game engine components
- Real-time signal processing
- Plugin systems (small .so/.dll files)

---

### C - Maximum Compatibility

**Status**: ✅ Production Ready (7/7 benchmarks)

**Strengths**:
- **Universal compatibility** - works everywhere
- **Direct interop** - no FFI overhead
- **Fast execution** (142ms avg)
- **Small binaries** (66KB avg)
- **Predictable performance** - no hidden allocations

**Weaknesses**:
- Slowest compilation (375ms avg)
- Most verbose code (77 LOC avg)
- Manual memory management
- Large runtime library (~2,500 lines)

**Best For**:
- Embedding Python logic in C applications
- Legacy system integration
- Bare-metal programming
- Maximum portability requirements

**Runtime**: ~2,500 lines (16 files), STC containers + fallback system

**Example Use Cases**:
- Linux kernel modules
- Embedded systems (bare metal)
- C library extensions
- Hardware drivers

---

### Rust - Memory Safety Guarantee

**Status**: ✅ Production Ready (7/7 benchmarks)

**Strengths**:
- **Memory safety** - ownership prevents use-after-free, data races
- **Fast execution** (153ms avg)
- **Moderate compilation** (198ms avg)
- **Zero-cost abstractions** - generics, traits
- **Modern tooling** - cargo, clippy, rustfmt

**Weaknesses**:
- Larger binaries (446KB avg)
- Ownership learning curve
- Generated code complexity

**Best For**:
- Safety-critical systems
- Concurrent/parallel applications
- WebAssembly compilation
- Systems programming with safety guarantees

**Runtime**: 304 lines, pure std library

**Example Use Cases**:
- WebAssembly modules
- Network services (zero-downtime)
- Concurrent data processing
- Python extension modules (PyO3)

---

### Go - Speed Champion

**Status**: ✅ Production Ready (7/7 benchmarks)

**Strengths**:
- **Fastest compilation** (63ms avg) - 3-8x faster than others
- **Fastest execution** (46ms avg) - 3-6x faster than others
- **Built-in concurrency** - goroutines, channels
- **Simple deployment** - single static binary
- **Garbage collection** - automatic memory management

**Weaknesses**:
- **Largest binaries** (2.3MB avg) - 64x larger than C++
- Limited type system (no generics in older versions)
- GC pauses (non-deterministic)

**Best For**:
- Cloud services and microservices
- DevOps tooling (CLI utilities)
- Rapid prototyping and iteration
- Network-intensive applications

**Runtime**: 413 lines, pure std library

**Example Use Cases**:
- REST API servers
- CLI tools (mgen itself uses Go-style patterns)
- Container orchestration tools
- Log processing pipelines

---

### OCaml - Functional Elegance

**Status**: ✅ Production Ready (7/7 benchmarks)

**Strengths**:
- **Most compact code** (26 LOC avg)
- **Fast compilation** (233ms avg)
- **Strong type inference** - minimal annotations
- **Functional paradigm** - immutability, pattern matching
- **Mature compiler** - INRIA research backing

**Weaknesses**:
- Large binaries (811KB avg)
- Smaller ecosystem than C++/Rust/Go
- Functional learning curve

**Best For**:
- Functional programming projects
- Academic research
- Compiler/interpreter development
- Mathematical/symbolic computation

**Runtime**: 216 lines, pure std library

**Example Use Cases**:
- Domain-specific languages (DSLs)
- Theorem provers
- Financial modeling
- Compiler frontends

---

### Haskell - Pure Functional

**Status**: ✅ Functionally Complete (6/7 benchmarks)

**Strengths**:
- **Pure functional paradigm** - no side effects
- **Type safety** - strong static typing
- **Lazy evaluation** - infinite data structures
- **Expressive code** (27 LOC avg)
- **Academic rigor** - correctness proofs

**Weaknesses**:
- **Largest binaries** (19.3MB avg) - GHC runtime overhead
- **Slowest execution** (274ms avg) - lazy evaluation
- **Mutation limitations** - quicksort benchmark fails (purity constraint)
- Slower compilation (504ms avg)

**Best For**:
- Pure functional transformations
- Research and education
- Type-safe domain modeling
- Immutable data pipelines

**Runtime**: 214 lines, pure std library

**Example Use Cases**:
- Data transformation pipelines (ETL)
- Configuration DSLs
- Parsing and validation
- Academic projects

**Note**: Cannot compile code with mutations (quicksort fails). Best for immutable, pure functional code.

---

## Feature Matrix

| Feature | C | C++ | Rust | Go | OCaml | Haskell |
|---------|---|-----|------|----|----|---------|
| **Python Support** |
| Lists | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Dictionaries | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Sets | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Comprehensions | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Classes/OOP | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| File I/O | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Module imports | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Nested containers | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Language Features** |
| Memory safety | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| Garbage collection | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| Type inference | ⚠️ | ✅ | ✅ | ⚠️ | ✅ | ✅ |
| Generic containers | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Pattern matching | ❌ | ❌ | ✅ | ⚠️ | ✅ | ✅ |
| Immutability | ❌ | ❌ | ✅ | ❌ | ✅ | ✅ |
| **Ecosystem** |
| Package manager | ❌ | ⚠️ | ✅ | ✅ | ✅ | ✅ |
| Build system | Makefile | CMake | Cargo | Go | Dune | Cabal/Stack |
| Tooling maturity | ✅✅✅ | ✅✅✅ | ✅✅ | ✅✅✅ | ✅ | ✅ |
| Library ecosystem | ✅✅✅ | ✅✅✅ | ✅✅ | ✅✅ | ✅ | ✅ |
| **Production Readiness** |
| Benchmark success | 7/7 | 7/7 | 7/7 | 7/7 | 7/7 | 6/7 |
| External dependencies | 0 | 0 | 0 | 0 | 0 | 0 |
| Status | ✅ | ✅ | ✅ | ✅ | ✅ | ✅* |

Legend: ✅ Full support, ⚠️ Partial support, ❌ Not available, * = Functionally complete (mutation limitations)

---

## Decision Tree

### Start Here

```
Do you need the absolute SMALLEST binary size?
├─ YES → C++ (34KB avg)
└─ NO → Continue

Do you need the FASTEST compile times?
├─ YES → Go (63ms avg, 8x faster than others)
└─ NO → Continue

Do you need MEMORY SAFETY guarantees?
├─ YES → Rust (ownership system prevents bugs)
└─ NO → Continue

Are you embedding in an existing C codebase?
├─ YES → C (direct interop, no FFI)
└─ NO → Continue

Do you prefer FUNCTIONAL programming?
├─ YES → Do you need mutations (mutable state)?
│   ├─ YES → OCaml (refs for mutation)
│   └─ NO → Haskell (pure functions only)
└─ NO → Continue

Do you need FASTEST execution speed?
├─ YES → Go (46ms avg, 3-6x faster)
└─ NO → C++ or C (general purpose, mature)
```

### By Use Case

**Embedded Systems / IoT**:
1. C++ (smallest binaries)
2. C (universal compatibility)
3. Rust (safety critical)

**Cloud / Microservices**:
1. Go (fast builds, concurrency)
2. Rust (memory safety, no GC)
3. C++ (performance)

**Safety-Critical Systems**:
1. Rust (memory safety)
2. Haskell (type safety, purity)
3. OCaml (type safety)

**Rapid Development / Prototyping**:
1. Go (fastest iteration)
2. OCaml (concise code)
3. Haskell (expressive)

**Legacy Integration**:
1. C (universal FFI)
2. C++ (C++ interop)
3. Rust (safe FFI)

**Data Processing Pipelines**:
1. Haskell (pure transformations)
2. OCaml (functional)
3. Go (fast execution)

---

## Common Questions

### Which backend should I use for general-purpose programming?

**Go** or **C++** are the most versatile:
- **Go**: Fastest compile/run times, easiest iteration, but large binaries
- **C++**: Balanced performance, small binaries, mature ecosystem

### I need both speed and safety. Which backend?

**Rust** provides memory safety with near-C++ performance (153ms vs 139ms execution, only 10% slower).

### I'm deploying to size-constrained devices. Which backend?

**C++** generates the smallest binaries (34-42KB), followed by **C** (66KB). Avoid Go (2.3MB) and Haskell (19.3MB).

### I want the fastest development cycle. Which backend?

**Go** has the fastest compilation (63ms avg), allowing rapid iteration. **OCaml** is second (233ms).

### I'm writing a CLI tool. Which backend?

**Go** is ideal for CLI tools:
- Fast compilation for quick iteration
- Single static binary (easy distribution)
- Built-in flag parsing, concurrent I/O

### I need functional programming. OCaml or Haskell?

- **OCaml**: If you need some mutations (refs), faster execution, smaller binaries
- **Haskell**: If you want pure functions only, stronger type system, lazy evaluation

### Can I mix backends in one project?

Yes! Generate different modules with different backends and link via FFI:
- C/C++ can call each other directly
- Rust → C via `extern "C"`
- Go → C via cgo
- All languages can interface via C ABI

---

## Performance Tips by Backend

### C++
- Use `-O3` for maximum optimization
- Enable link-time optimization (LTO)
- Consider `-march=native` for CPU-specific optimizations

### C
- Use `-O3 -flto` for optimization
- Minimize container usage (overhead vs C++)
- Consider STC library directly for hand-tuned code

### Rust
- Use `--release` mode (default in MGen)
- Enable LTO in Cargo.toml for smaller binaries
- Profile with `perf` for bottlenecks

### Go
- Use `go build -ldflags="-s -w"` to strip debug info
- Profile with `pprof` for optimization
- Consider `-trimpath` for reproducible builds

### OCaml
- Use `ocamlopt` (native compiler, not bytecode)
- Enable `-O3` optimization
- Use `flambda` optimizer for advanced inlining

### Haskell
- Use `-O2` optimization
- Enable strictness annotations for hot loops
- Profile with `+RTS -p` for heap analysis

---

## Benchmarks Summary

**Test Configuration**:
- 7 benchmarks (fibonacci, quicksort, matmul, wordcount, list_ops, dict_ops, set_ops)
- Run on macOS (Darwin 24.6.0)
- Measured: compile time, execution time, binary size, LOC
- All backends use maximum optimization flags

**Raw Data** (from `build/benchmark_results/benchmark_report.md`):

| Backend | Success | Compile | Execute | Binary | LOC |
|---------|---------|---------|---------|--------|-----|
| C | 7/7 | 375ms | 142ms | 66KB | 77 |
| C++ | 7/7 | 402ms | 139ms | 36KB | 49 |
| Rust | 7/7 | 198ms | 153ms | 446KB | 36 |
| Go | 7/7 | 63ms | 46ms | 2.3MB | 37 |
| OCaml | 7/7 | 233ms | 166ms | 811KB | 26 |
| Haskell | 6/7 | 504ms | 274ms | 19.3MB | 27 |

**Updated**: October 5, 2025 (v0.1.61)

---

## Next Steps

After choosing a backend:

1. **Read the Getting Started Guide**: `docs/GETTING_STARTED.md`
2. **Review examples**: `examples/` directory for backend-specific patterns
3. **Check supported features**: Ensure your code uses MGen-compatible Python
4. **Run benchmarks**: `make benchmark` to verify performance on your hardware
5. **Join the community**: Report issues, contribute improvements

---

## Version History

- **v1.0** (October 2025) - Initial backend selection guide
  - Performance data from 7 benchmarks
  - All 6 backends production-ready (5 at 100%, Haskell functionally complete)
  - Decision tree and use case recommendations

---

**Need Help?**

- Getting Started: `docs/GETTING_STARTED.md`
- Error Messages: `docs/ERROR_HANDLING.md`
- Report Issues: https://github.com/anthropics/mgen/issues (update with actual repo)
