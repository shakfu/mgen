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

## [0.1.7]

### Added
- **Advanced Python Language Features**: Complete comprehensions support for sophisticated data processing
  - List comprehensions with range iteration and conditional filtering (`[x*2 for x in range(n) if x > 5]`)
  - Dictionary comprehensions with key-value mappings (`{k: v for k in range(n) if condition}`)
  - Set comprehensions with unique value generation (`{x*x for x in range(n) if x % 2 == 0}`)
  - Support for complex expressions within comprehensions (arithmetic, function calls, etc.)
  - Conditional filtering with `if` clauses for selective element inclusion
  - Range-based iteration with start, stop, and step parameters
- **Enhanced STC Integration**: Smart Template Container operations for comprehensions
  - Automatic vector initialization and push operations for list comprehensions
  - HashMap insert operations for dictionary comprehensions with proper key-value handling
  - HashSet insert operations for set comprehensions with duplicate elimination
  - Type inference for container element types and proper C type mapping
  - Memory-safe container operations with bounds checking and error handling

### Technical Achievements
- **Sophisticated AST Conversion**: Complete `ast.ListComp`, `ast.DictComp`, and `ast.SetComp` support
- **Advanced Code Generation**: Multi-line C code blocks with proper loop and condition generation
- **Type Safety**: Automatic type inference for comprehension elements and container specialization
- **Test Coverage**: 29 new comprehensive tests ensuring robust comprehensions functionality (204 total tests passing)
- **Performance**: Efficient C loops with minimal overhead compared to Python equivalents

### Example Conversion
**Python Input:**
```python
def process_numbers(n: int) -> dict:
    # List comprehension with condition
    evens: list = [x * 2 for x in range(n) if x % 2 == 0]

    # Dictionary comprehension
    squares: dict = {i: i * i for i in range(5)}

    # Set comprehension with complex expression
    unique_values: set = {x * x + 1 for x in range(10) if x > 3}

    return squares
```

**Generated C Output:**
```c
dict process_numbers(int n) {
    // List comprehension becomes C loop with vector operations
    vec_int evens = {0};
    for (int x = 0; x < n; x += 1) {
        if ((x % 2) == 0) vec_int_push(&evens, (x * 2));
    }

    // Dictionary comprehension becomes hashmap operations
    map_int_int squares = {0};
    for (int i = 0; i < 5; i += 1) {
        map_int_int_insert(&squares, i, (i * i));
    }

    // Set comprehension becomes hashset operations
    set_int unique_values = {0};
    for (int x = 0; x < 10; x += 1) {
        if ((x > 3)) set_int_insert(&unique_values, ((x * x) + 1));
    }

    return squares;
}
```

## [0.1.6]

### Changed
- **Architecture Consolidation**: Complete merger of py2c converter functionality into emitter module
  - Merged `src/mgen/backends/c/py2c_converter.py` into `src/mgen/backends/c/emitter.py` (1,160 total lines)
  - Consolidated `MGenPythonToCConverter` class, exception classes, and all OOP functionality in single module
  - Simplified import structure by removing separate py2c_converter dependency
  - Updated all test files to import from unified emitter module
- **Code Organization**: Enhanced C backend architecture with streamlined module structure
  - Eliminated redundant file separation while preserving all functionality
  - Improved maintainability with related functionality grouped in single location
  - Reduced module complexity and import dependencies across the codebase

### Technical Improvements
- **Unified C Backend**: All 866 lines of sophisticated Python-to-C conversion code now integrated in emitter.py
- **Preserved API Compatibility**: All existing functionality maintained with identical interface
- **Test Coverage**: All 175 tests continue to pass with zero regressions after merge
- **Clean Architecture**: Consolidated sophisticated OOP support, runtime integration, and code generation in one module

## [0.1.5]

### Added
- **Object-Oriented Programming Support**: Complete Python class to C struct conversion system
  - Full Python class support with `__init__` constructors and instance methods
  - Automatic struct generation with typedef declarations for each Python class
  - Sophisticated method conversion with proper `self` parameter handling (converted to struct pointers)
  - Constructor functions (`ClassName_new()`) with parameter passing and instance initialization
  - Instance variable access conversion (`self.attr` → `self->attr`, `obj.attr` → `obj.attr`)
  - Method call conversion (`obj.method()` → `ClassName_method(&obj)`) with automatic object reference
- **Enhanced Assignment Support**: Complete attribute assignment handling
  - Self-reference assignments in methods (`self.attr = value` → `self->attr = value`)
  - Object attribute assignments (`obj.attr = value` → `obj.attr = value`)
  - Type-annotated attribute assignments with proper C type mapping
  - Mixed typed and inferred instance variable support
- **Advanced OOP Features**: Production-ready object-oriented code generation
  - Empty class support with dummy struct members for C compatibility
  - Complex method implementations with control flow, loops, and function calls
  - Multi-class interactions and object composition support
  - Integrated type inference for instance variables and method parameters
- **Comprehensive OOP Test Suite**: 19 new tests ensuring robust object-oriented functionality
  - Complete class conversion test coverage (`test_backend_c_oop.py`)
  - Method call, constructor, and instance variable access validation
  - Complex integration scenarios with multiple classes and interactions
  - Error handling and edge case validation for OOP features

### Changed
- **Py2C Converter Architecture**: Expanded to support complete object-oriented programming paradigm
  - Enhanced expression handling to support method calls and class instantiation
  - Updated assignment conversion to handle attribute assignments (`self.attr = value`)
  - Integrated class definition processing in module conversion pipeline
  - Extended type mapping system to track struct types and method signatures
- **Code Generation Pipeline**: Advanced object-oriented code generation capabilities
  - Class-aware variable context tracking for proper method call resolution
  - Sophisticated struct member access pattern generation (`obj.member` vs `ptr->member`)
  - Enhanced function signature generation for class methods with explicit self parameters
  - Improved code organization with struct definitions, constructors, and method implementations

### Technical Achievements
- **Complete OOP Paradigm**: Python classes, methods, constructors, instance variables
- **Advanced Code Generation**: Struct typedefs, constructor functions, method conversion
- **Type Safety**: Automatic struct pointer handling and member access patterns
- **Test Coverage**: All 175 tests passing (156 original + 19 new OOP tests)
- **Production Ready**: Generates clean, efficient C code from Python OOP patterns

### Example Conversion
**Python Input:**
```python
class Rectangle:
    def __init__(self, width: int, height: int):
        self.width: int = width
        self.height: int = height

    def area(self) -> int:
        return self.width * self.height

def create_rect() -> int:
    rect: Rectangle = Rectangle(5, 10)
    return rect.area()
```

**Generated C Output:**
```c
typedef struct Rectangle {
    int width;
    int height;
} Rectangle;

Rectangle Rectangle_new(int width, int height) {
    Rectangle obj;
    obj.width = width;
    obj.height = height;
    return obj;
}

int Rectangle_area(Rectangle* self) {
    return (self->width * self->height);
}

int create_rect(void) {
    Rectangle rect = Rectangle_new(5, 10);
    return Rectangle_area(&rect);
}
```

## [0.1.4]

### Added
- **Advanced Python-to-C Converter**: Sophisticated py2c conversion engine with complex Python support
  - Complete `MGenPythonToCConverter` class with advanced AST-to-C translation
  - Complex control flow support: if/elif/else chains, while loops, for loops with range()
  - Advanced expression handling: arithmetic precedence, comparison operations, unary operators
  - Intelligent type inference system with automatic type mapping and container support
  - Built-in function integration with MGen runtime (abs, bool, len, min, max, sum)
- **Enhanced Code Generation Features**: Production-ready C code generation capabilities
  - Sophisticated function conversion with parameter handling and return types
  - Local variable declarations with automatic type inference
  - Nested control structures and complex expression trees
  - Boolean and string literal handling with proper C syntax
  - Recursive function call support with stack safety
- **Comprehensive Test Suite**: 89 new tests ensuring robust C backend functionality
  - Complete py2c converter test coverage (49 tests in `test_backend_c_py2c.py`)
  - Enhanced C backend integration tests (40 tests in `test_backend_c_enhanced.py`)
  - Parametrized testing for operators, types, and language constructs
  - Error handling and edge case validation

### Changed
- **C Backend Architecture**: Complete transformation to sophisticated code generation
  - Replaced basic code emission with advanced py2c converter integration
  - Enhanced emitter with fallback system for unsupported features
  - Integrated sophisticated control flow and expression generation
  - Updated type system with intelligent inference and container specialization
- **Code Quality and Reliability**: Production-ready code generation with comprehensive validation
  - All 156 tests passing (67 original + 89 new C backend tests)
  - Robust error handling with graceful fallback mechanisms
  - Enhanced debugging support with detailed error context
  - Improved code formatting and C standard compliance

### Technical Achievements
- **Complex Python Feature Support**: if/elif/else, while loops, for-range loops, recursion
- **Advanced Type System**: Automatic inference, annotation support, container type mapping
- **Expression Engine**: Full operator support with proper precedence and parenthesization
- **Runtime Integration**: Seamless MGen runtime library integration with automatic inclusion
- **Test Coverage**: Comprehensive validation of all py2c converter and enhanced backend features

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