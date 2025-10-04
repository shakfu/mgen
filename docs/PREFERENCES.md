# MGen Backend Preferences System

MGen provides a comprehensive preference system that allows users to customize code generation behavior for each target language. This enables choosing between cross-language consistency and language-specific idiomatic optimizations across **all supported backends**: Haskell, C, C++, Rust, and Go.

## Overview

The preference system supports:

- **Universal backend support**: Works with all MGen backends (Haskell, C, C++, Rust, Go)
- **Default behavior**: Cross-language consistency using runtime library functions
- **Language-specific optimizations**: Idiomatic code generation for each target language
- **CLI integration**: Set preferences via command-line arguments for any backend
- **Extensible architecture**: Easy to add new preferences for existing and new backends

## Usage

### Command Line Interface

Use the `--prefer` or `-p` flag to set backend preferences:

```bash
# Enable native Haskell comprehensions
mgen convert example.py --target haskell --prefer use_native_comprehensions=true

# C backend with custom settings
mgen convert example.py --target c --prefer use_stc_containers=false --prefer indent_size=2

# C++ backend with modern features
mgen convert example.py --target cpp --prefer cpp_standard=c++20 --prefer use_modern_cpp=true

# Rust backend with specific edition
mgen convert example.py --target rust --prefer rust_edition=2018 --prefer clone_strategy=explicit

# Go backend with custom version
mgen convert example.py --target go --prefer go_version=1.19 --prefer use_generics=false

# Multiple preferences for any backend
mgen build app.py --target haskell \
  --prefer use_native_comprehensions=true \
  --prefer camel_case_conversion=false \
  --prefer strict_data_types=true

# Boolean values (case-insensitive)
--prefer use_native_comprehensions=true
--prefer use_stc_containers=false

# Numeric values
--prefer indent_size=2
--prefer timeout=30.5

# String values
--prefer brace_style=allman
--prefer cpp_standard=c++20
```

### Programmatic Usage

```python
from mgen.backends.preferences import (
    HaskellPreferences, CPreferences, CppPreferences,
    RustPreferences, GoPreferences, PreferencesRegistry
)
from mgen.backends.registry import registry

# Create preferences for any backend
haskell_prefs = HaskellPreferences()
haskell_prefs.set('use_native_comprehensions', True)

c_prefs = CPreferences()
c_prefs.set('use_stc_containers', False)
c_prefs.set('indent_size', 2)

cpp_prefs = CppPreferences()
cpp_prefs.set('cpp_standard', 'c++20')
cpp_prefs.set('use_modern_cpp', True)

# Or use the registry
rust_prefs = PreferencesRegistry.create_preferences('rust')
rust_prefs.set('rust_edition', '2018')

# Use with backends
haskell_backend = registry.get_backend('haskell', haskell_prefs)
c_backend = registry.get_backend('c', c_prefs)
cpp_backend = registry.get_backend('cpp', cpp_prefs)
rust_backend = registry.get_backend('rust', rust_prefs)
```

## Available Preferences

### Haskell Backend

#### Comprehension Generation

- **`use_native_comprehensions`** (bool, default: `false`)
  - `false`: Use runtime functions for cross-language consistency

    ```haskell
    listComprehension numbers (\x -> x * 2)
    ```

  - `true`: Use native Haskell comprehension syntax

    ```haskell
    [x * 2 | x <- numbers]
    ```

- **`prefer_idiomatic_syntax`** (bool, default: `false`)
  - Enable Haskell-specific syntax optimizations

#### Code Style

- **`camel_case_conversion`** (bool, default: `true`)
  - Convert Python snake_case to Haskell camelCase

- **`module_pragmas`** (list, default: `['OverloadedStrings']`)
  - Language extensions to include in generated modules

- **`import_qualified`** (bool, default: `true`)
  - Use qualified imports for standard libraries

#### Type System

- **`enable_type_annotations`** (bool, default: `true`)
  - Include explicit type signatures

- **`strict_data_types`** (bool, default: `false`)
  - Use strict data fields with `!` annotations

- **`unpack_pragmas`** (bool, default: `false`)
  - Add `{-# UNPACK #-}` pragmas for performance

#### Performance

- **`enable_fusion_rules`** (bool, default: `false`)
  - Enable list fusion optimizations

- **`use_strict_mode`** (bool, default: `false`)
  - Use strict evaluation instead of lazy

### C Backend

#### Code Generation

- **`use_stc_containers`** (bool, default: `true`)
  - Use Smart Template Containers for collections

- **`inline_functions`** (bool, default: `false`)
  - Add `inline` keywords to function declarations

- **`use_restrict_keywords`** (bool, default: `false`)
  - Use `restrict` pointers for optimization hints

#### Memory Management

- **`explicit_memory_management`** (bool, default: `true`)
  - Manual memory allocation/deallocation

- **`bounds_checking`** (bool, default: `true`)
  - Array bounds validation

- **`null_pointer_checks`** (bool, default: `true`)
  - NULL pointer validation

#### Style

- **`brace_style`** (string, default: `"k&r"`)
  - Options: `"k&r"`, `"allman"`, `"gnu"`, `"linux"`

- **`indent_size`** (int, default: `4`)
  - Number of spaces for indentation

- **`use_stdint_types`** (bool, default: `true`)
  - Use `int32_t` instead of `int`

## Design Philosophy

### Cross-Language Consistency (Default)

The default behavior prioritizes consistency across all target languages:

```python
# Python source
result = [x * 2 for x in range(5) if x > 2]
```

```haskell
-- Haskell (consistent runtime approach)
result = listComprehensionWithFilter (rangeList (range 5)) (\x -> x > 2) (\x -> x * 2)
```

```c
// C (consistent runtime approach)
vec_int result = listComprehensionWithFilter_int(range_create(0, 5, 1), filter_gt2, transform_mult2);
```

### Language-Specific Optimizations

With preferences enabled, each language uses idiomatic constructs:

```python
# Python source
result = [x * 2 for x in range(5) if x > 2]
```

```haskell
-- Haskell (native comprehensions enabled)
result = [x * 2 | x <- [0..4], x > 2]
```

```c
// C (with optimization preferences)
static inline int numbers[] = {0, 1, 2, 3, 4};
vec_int result = vec_int_with_capacity(3);
for (int i = 0; i < 5; i++) {
    if (numbers[i] > 2) vec_int_push(&result, numbers[i] * 2);
}
```

## Adding New Preferences

### For Existing Backends

#### 1. Update preferences class

```python
@dataclass
class HaskellPreferences(BackendPreferences):
    def __post_init__(self):
        self.language_specific.update({
            'new_preference': False,
            # ... existing preferences
        })
```

#### 2. Use in emitter

```python
class HaskellEmitter(AbstractEmitter):
    def generate_function(self, node):
        if self.preferences and self.preferences.get('new_preference', False):
            # Custom behavior
            return self.generate_optimized_function(node)
        else:
            # Default behavior
            return self.generate_standard_function(node)
```

### For New Backends

#### 1. Create preferences class

```python
@dataclass
class MyLangPreferences(BackendPreferences):
    def __post_init__(self):
        self.language_specific.update({
            'use_native_features': False,
            'optimization_level': 'standard',
            'memory_model': 'automatic',
        })
```

#### 2. Register in preferences registry

```python
PreferencesRegistry.register_backend('mylang', MyLangPreferences)
```

#### 3. Use in backend components

```python
class MyLangEmitter(AbstractEmitter):
    def __init__(self, preferences=None):
        super().__init__(preferences)
        self.use_native = preferences and preferences.get('use_native_features', False)
```

## Examples

### Haskell Native Comprehensions

**Input Python**:

```python
def process_data(numbers):
    # List comprehension with filter
    evens = [x for x in numbers if x % 2 == 0]

    # Dictionary comprehension
    squares = {x: x*x for x in evens}

    # Set comprehension
    unique_squares = {x*x for x in numbers}

    return evens, squares, unique_squares
```

**Default Output** (runtime consistency):

```haskell
processData :: [Int] -> ([Int], Dict Int Int, Set Int)
processData numbers =
  let evens = listComprehensionWithFilter numbers (\x -> (x `mod` 2) == 0) (\x -> x)
      squares = dictComprehension evens (\x -> x) (\x -> x * x)
      uniqueSquares = setComprehension numbers (\x -> x * x)
  in (evens, squares, uniqueSquares)
```

**Native Comprehensions Enabled**:

```haskell
processData :: [Int] -> ([Int], Dict Int Int, Set Int)
processData numbers =
  let evens = [x | x <- numbers, (x `mod` 2) == 0]
      squares = Map.fromList [(x, x * x) | x <- evens]
      uniqueSquares = Set.fromList [x * x | x <- numbers]
  in (evens, squares, uniqueSquares)
```

### Performance Comparison

The preference system allows users to choose based on their priorities:

- **Default (Consistency)**: Predictable behavior across languages, easier debugging
- **Native (Performance)**: Language-specific optimizations, better integration with ecosystem

| Aspect             | Default (Runtime)              | Native (Idiomatic)            |
|------------------- |------------------------------- | ------------------------------|
| **Consistency**    | + Identical patterns           | - Language-specific           |
| **Performance**    | - Function call overhead       | + Compiler optimized          |
| **Readability**    | - Verbose for native speakers  | + Familiar syntax             |
| **Learning Curve** | + Same across languages        | - Language-specific knowledge |

## Future Extensions

The preference system is designed for extensibility:

- **Profile-based preferences**: Save/load preference profiles
- **Project-level configuration**: `.mgen.toml` configuration files
- **IDE integration**: Language server protocol support
- **Performance analysis**: Benchmark-driven preference suggestions
- **Template preferences**: Per-project-type optimization templates
