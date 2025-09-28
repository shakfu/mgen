# CHANGELOG

All notable project-wide changes will be documented in this file. Note that each subproject has its own CHANGELOG.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and [Commons Changelog](https://common-changelog.org). This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Types of Changes

- Added: for new features.
- Changed: for changes in existing functionality.
- Deprecated: for soon-to-be removed features.
- Removed: for now removed features.
- Fixed: for any bug fixes.
- Security: in case of vulnerabilities.

---

## [0.1.x]

## [0.1.3]

### Added
- **Enhanced C Backend**: Direct integration of CGen's sophisticated C translation capabilities
  - Integrated CGen runtime libraries (50KB+ of C code) directly into MGen C backend
  - MGen runtime system with error handling, memory management, and Python operations
  - Smart Template Containers (STC) support with Python-semantic container operations
  - Enhanced code generation with proper function body implementation
  - Runtime-aware build system with automatic source inclusion
- **Advanced C Code Generation**: Sophisticated Python-to-C translation features
  - Python-like error handling system with detailed context and stack traces
  - Memory safety with bounds checking, safe allocation, and automatic cleanup
  - High-performance container operations using STC with Python semantics
  - Enhanced type mapping and expression generation
  - Support for Python built-ins (bool, abs, min, max, sum, range, etc.)

### Changed
- **C Backend Architecture**: Complete overhaul from basic arrays to sophisticated runtime system
  - Replaced simple type mapping with comprehensive Python-to-C semantics
  - Enhanced container system from basic pointers to STC-based high-performance containers
  - Improved build system to automatically include runtime libraries
  - Updated code generation to use integrated runtime instead of external dependencies
- **Runtime Integration**: CGen runtime libraries fully integrated into MGen codebase
  - All runtime code copied and adapted with `mgen_*` prefixes for independence
  - No external CGen dependencies - fully self-contained MGen implementation
  - Enhanced Makefile generation with development targets (test, debug, release)

### Technical Details
- **Runtime Components**: Error handling, Python operations, memory management, STC bridge
- **Container Support**: vec_T, map_K_V, set_T with Python-like operations and bounds checking
- **Code Quality**: All 67 tests passing, maintains full MGen API compatibility
- **Build Integration**: Automatic runtime source detection and inclusion in compilation

## [0.1.2]

### Added
- **C++ Backend**: Complete C++ backend implementation following MGen architecture
  - Full C++ code generation with modern C++17 features
  - STL container support (std::vector, std::map, std::set, etc.)
  - Comprehensive Makefile generation with development targets
  - CMake support as alternative build system
  - Direct compilation support with g++
- **Enhanced 7-Phase Pipeline**: Integrated CGen's sophisticated pipeline into MGen
  - Validation Phase: Static-python style validation and translatability assessment
  - Analysis Phase: AST parsing and semantic element breakdown
  - Python Optimization Phase: Compile-time evaluation, loop analysis, function specialization
  - Mapping Phase: Python to target language semantics mapping
  - Target Optimization Phase: Language-specific optimizations
  - Generation Phase: Target language code generation
  - Build Phase: Direct compilation or build file generation
- **Multi-Language CLI**: Complete CLI conversion from CGen-specific to MGen architecture
  - Dynamic backend discovery and listing (`mgen backends`)
  - Language-aware runtime library management
  - Multi-language batch processing support
  - Consistent command interface across all target languages

### Changed
- **Pipeline Architecture**: Enhanced pipeline with comprehensive phase tracking and error handling
  - Language-agnostic constraint checking (C-specific rules only apply to C targets)
  - Advanced optimization phases for both Python-level and target-language-level optimizations
  - Graceful fallbacks when frontend components are not available
- **Backend System**: Improved backend abstraction and container systems
  - Enhanced container type mappings and operations for all languages
  - Language-specific build file generation (Makefile, Cargo.toml, go.mod)
  - Improved type mapping and code generation consistency
- **CLI Interface**: Transformed from CGen-specific to fully multi-language
  - Updated help text and documentation to reflect multi-language support
  - Language-aware compiler selection and build system integration
  - Enhanced error messages and user feedback

### Fixed
- **Test Compatibility**: Updated all backend tests to include C++ backend
  - Fixed constraint checking conflicts with non-C backends
  - Resolved abstract method implementation issues in C++ backend
  - Enhanced test coverage to 67 passing tests across all backends
- **Pipeline Integration**: Resolved compatibility issues between CGen and MGen pipelines
  - Fixed missing method implementations in abstract base classes
  - Corrected type annotation requirements for multi-language validation

### Technical Details
- **Supported Languages**: C, C++, Rust, Go (all with full pipeline support)
- **Build Systems**: Makefile (C/C++), Cargo.toml (Rust), go.mod (Go), CMake (C++ alternative)
- **Code Quality**: 67/67 tests passing, comprehensive error handling, phase-by-phase progress tracking
- **CLI Commands**:
  ```bash
  mgen --target cpp convert file.py        # Generate C++ code
  mgen --target rust build file.py -m      # Generate Rust + Cargo.toml
  mgen backends                             # List available languages
  mgen --target go batch --source-dir src/ # Batch convert to Go
  ```

## [0.0.1]

- Project created as a generalize of the [CGen](https://github.com/shakfu/cgen) project. 