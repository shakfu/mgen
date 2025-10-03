# Generated Container Implementation Design

**Status**: Design Document
**Created**: 2025-10-04
**Author**: Architecture Discussion

## Problem Statement

The C backend currently has two approaches for container implementations, both with significant drawbacks:

### Approach 1: STC Macro Library (Current, Being Replaced)
```c
#define i_type map_str_int
#define i_keyclass cstr_raw
#define i_val int
#include "ext/stc/include/stc/hmap.h"
```

**Problems**:
- Macro hell - difficult to debug
- Non-owning string pointers (`cstr_raw`) cause subtle bugs
- Include order dependencies
- Opaque code generation via macro expansion
- IDE/tooling support breaks down

### Approach 2: Type-Specific Runtime Libraries (v0.1.37)
```c
#include "mgen_str_int_map.h"  // Separate library for each type combination
```

**Problems**:
- Need separate libraries for each type combination:
  - `mgen_str_int_map.h/c`
  - `mgen_int_int_map.h/c` (future)
  - `mgen_str_str_map.h/c` (future)
  - `mgen_vec_int.h/c` (future)
  - etc.
- Library explosion: N key types × M value types = N×M libraries
- Still requires linking external files
- Doesn't fully leverage code generation capabilities

## Proposed Solution: Generated Type-Specific Containers

**Core Idea**: Generate complete, type-specific container implementations directly into the output C file.

### Philosophy

Code generators should produce **self-contained, complete code**. This is how:
- **C++ templates** work (monomorphization at compile time)
- **Rust generics** work (monomorphization to concrete types)
- **Modern transpilers** work (complete output, minimal runtime)

### Architecture

```
Python Code → Analyzer → Code Generator → Complete C File
                           ├─ Detect needed containers
                           ├─ Generate container implementations
                           └─ Generate user code
```

### Example Output

Instead of including headers:
```c
#include "mgen_str_int_map.h"  // External dependency
```

Generate inline implementations:
```c
// ========== Generated Container: str_int_map ==========
// Hash table for string→int mappings
// Generated specifically for this program

typedef struct str_int_entry {
    char* key;        // Owned string (strdup'd)
    int value;
    struct str_int_entry* next;
} str_int_entry_t;

typedef struct {
    str_int_entry_t** buckets;
    size_t bucket_count;
    size_t size;
} str_int_map_t;

static unsigned long str_int_hash(const char* str) {
    unsigned long hash = 5381;
    int c;
    while ((c = *str++)) {
        hash = ((hash << 5) + hash) + c;  // hash * 33 + c
    }
    return hash;
}

static str_int_map_t* str_int_map_new(void) {
    str_int_map_t* map = malloc(sizeof(str_int_map_t));
    if (!map) return NULL;

    map->buckets = calloc(16, sizeof(str_int_entry_t*));
    if (!map->buckets) {
        free(map);
        return NULL;
    }

    map->bucket_count = 16;
    map->size = 0;
    return map;
}

static bool str_int_map_insert(str_int_map_t* map, const char* key, int value) {
    unsigned long hash = str_int_hash(key);
    size_t index = hash % map->bucket_count;

    // Check if key exists - update if so
    str_int_entry_t* entry = map->buckets[index];
    while (entry) {
        if (strcmp(entry->key, key) == 0) {
            entry->value = value;
            return false;  // Updated
        }
        entry = entry->next;
    }

    // Insert new entry
    str_int_entry_t* new_entry = malloc(sizeof(str_int_entry_t));
    if (!new_entry) return false;

    new_entry->key = strdup(key);
    if (!new_entry->key) {
        free(new_entry);
        return false;
    }

    new_entry->value = value;
    new_entry->next = map->buckets[index];
    map->buckets[index] = new_entry;
    map->size++;
    return true;  // Inserted
}

static int* str_int_map_get(str_int_map_t* map, const char* key) {
    if (!map || !key) return NULL;

    unsigned long hash = str_int_hash(key);
    size_t index = hash % map->bucket_count;

    str_int_entry_t* entry = map->buckets[index];
    while (entry) {
        if (strcmp(entry->key, key) == 0) {
            return &entry->value;
        }
        entry = entry->next;
    }
    return NULL;
}

// ... rest of implementation (contains, remove, free, etc.) ...

// ========== User Code ==========

int main(void) {
    str_int_map_t* word_counts = str_int_map_new();
    str_int_map_insert(word_counts, "hello", 1);

    int* count = str_int_map_get(word_counts, "hello");
    if (count) {
        printf("Count: %d\n", *count);
    }

    return 0;
}
```

## Benefits

### 1. Zero External Dependencies
- Single `.c` file output (or `.c + .h` for multi-file projects)
- No runtime libraries to link
- No header files to distribute
- Fully self-contained programs

### 2. Maximum Type Safety & Optimization
- Compiler sees concrete types everywhere
- No `void*` indirection (unlike generic C libraries)
- Aggressive inlining opportunities
- Better optimization (compiler knows exact types)
- Compile-time type checking

### 3. Superior Debugging Experience
- All code visible in one file
- No macro expansion to trace
- Standard debugger works perfectly
- Clear stack traces
- Easy to read generated code

### 4. Minimal Code Generation
- Only generate containers actually used
- Don't generate `remove()` if never called
- Tree-shaking at generation time
- Optimal code size

### 5. Type-Specific Optimizations
- String keys: use `strcmp` directly
- Integer keys: use direct comparison
- Pointer keys: use pointer comparison
- No dispatch overhead

### 6. Portable & Predictable
- Standard C89/C99 code
- No platform-specific dependencies
- Works with any C compiler
- Easy to understand output

## Implementation Strategy

### Phase 1: Template-Based Code Generation (Prototype)

Convert existing runtime libraries into code generation templates:

```python
class ContainerCodeGenerator:
    """Generate type-specific container implementations."""

    def __init__(self):
        # Load templates from runtime library files
        self.templates = {
            'str_int_map': self._load_str_int_map_template(),
            'vec_int': self._load_vec_int_template(),
            # etc.
        }

    def _load_str_int_map_template(self) -> str:
        """Load mgen_str_int_map.c as a template."""
        template_path = "src/mgen/backends/c/runtime/mgen_str_int_map.c"
        with open(template_path) as f:
            return f.read()

    def generate_container_code(self, container_type: str) -> str:
        """Generate complete implementation for a container type."""
        if container_type == "map_str_int":
            return self._generate_str_int_map()
        # ... other types

    def _generate_str_int_map(self) -> str:
        """Generate string→int hash table implementation."""
        # For prototype: return template directly
        # Future: parameterize template for different types
        return self.templates['str_int_map']
```

### Phase 2: Parameterized Templates

Extend to support arbitrary type combinations:

```python
def generate_map_code(self, key_type: str, value_type: str) -> str:
    """Generate map<K,V> for any types K, V."""

    template = self._get_map_template()

    # Parameterize template
    code = template.format(
        KEY_TYPE=key_type,
        VALUE_TYPE=value_type,
        TYPE_NAME=f"map_{self._sanitize(key_type)}_{self._sanitize(value_type)}",
        HASH_FUNC=self._get_hash_function(key_type),
        COMPARE_FUNC=self._get_compare_function(key_type),
        KEY_CLONE=self._get_clone_function(key_type),
        KEY_FREE=self._get_free_function(key_type),
    )

    return code
```

Examples:
- `generate_map_code("char*", "int")` → `map_str_int`
- `generate_map_code("int", "int")` → `map_int_int`
- `generate_map_code("char*", "char*")` → `map_str_str`

### Phase 3: Integration with Converter

Update C converter to use generated containers:

```python
class CConverter:
    def __init__(self):
        self.container_gen = ContainerCodeGenerator()
        self.needed_containers = set()

    def generate(self, ast_tree):
        # 1. Analyze to detect needed containers
        self._analyze_container_usage(ast_tree)

        # 2. Generate output
        code_sections = []

        # Standard includes
        code_sections.append(self._generate_includes())

        # Generated container implementations
        for container_type in sorted(self.needed_containers):
            code_sections.append(
                self.container_gen.generate_container_code(container_type)
            )

        # User code
        code_sections.append(self._generate_user_code(ast_tree))

        return "\n\n".join(code_sections)
```

### Phase 4: Optimization

Add smart code generation:

1. **Dead Code Elimination**: Only generate methods actually called
   ```python
   # If remove() never called, don't generate it
   if 'remove' in self.used_methods[container_type]:
       code.append(generate_remove_function())
   ```

2. **Inline Small Functions**: Inline single-use functions
   ```c
   static inline bool str_int_map_contains(str_int_map_t* map, const char* key) {
       return str_int_map_get(map, key) != NULL;
   }
   ```

3. **Constant Folding**: Optimize known-constant operations

4. **Type-Specific Optimizations**:
   - String keys: Intern common strings
   - Integer keys: Perfect hashing for small key sets
   - Dense integer keys: Use array instead of hash table

## Comparison Table

| Aspect | STC Macros | Runtime Libraries | **Generated Code** |
|--------|------------|-------------------|--------------------|
| **Dependencies** | STC headers | Multiple .h/.c | **None** |
| **Debugging** | ❌ Macro expansion | ✅ Standard | **✅ Easiest** |
| **Type Safety** | ⚠️ Macro-based | ✅ Type-specific | **✅ Best** |
| **Performance** | ✅ Zero overhead | ✅ Zero overhead | **✅ Zero overhead + optimization** |
| **Portability** | ⚠️ Depends on STC | ⚠️ Need libs | **✅ Single file** |
| **Code Size** | ⚠️ All features | ⚠️ All features | **✅ Only used features** |
| **Maintainability** | ❌ Hard | ✅ Moderate | **✅ Easy** |
| **IDE Support** | ❌ Poor | ✅ Good | **✅ Perfect** |
| **Error Messages** | ❌ Cryptic | ✅ Clear | **✅ Very clear** |
| **Learning Curve** | ❌ High | ✅ Low | **✅ Lowest** |

## Code Duplication Concerns

**Question**: Won't we duplicate code if multiple files use the same container?

**Answer**: Yes, but this is acceptable and standard practice:

1. **Each program is independent**: C programs are compiled separately
2. **Similar to C++ templates**: Each instantiation gets its own code
3. **Compilation is fast**: ~300 lines compiles in milliseconds
4. **Binary size**: Linker removes duplicates in single-binary projects
5. **Benefit outweighs cost**: Zero dependencies > smaller source

Example: If you have 5 programs each using `map_str_int`, you get 5 copies of the implementation. But:
- Each program is self-contained
- No shared library versioning issues
- No linking complexity
- Each can be optimized independently

## Migration Path

### Phase 1: Prototype (Current)
- Keep existing runtime library approach
- Build parallel template-based generator
- Test on single container type (`map_str_int`)
- Validate generated code quality

### Phase 2: Dual Mode
- Add converter flag: `--container-mode=runtime|generated`
- Allow users to choose approach
- Default to runtime for stability
- Extensive testing of generated mode

### Phase 3: Transition
- Switch default to generated mode
- Keep runtime mode as fallback
- Update all tests to use generated mode
- Performance benchmarking

### Phase 4: Completion
- Remove runtime libraries from include path
- Keep runtime library source as templates
- Update documentation
- Archive STC library

## Template Library Organization

Future structure:
```
src/mgen/backends/c/templates/
├── containers/
│   ├── map_template.c         # Parameterized map<K,V>
│   ├── vec_template.c         # Parameterized vector<T>
│   ├── set_template.c         # Parameterized set<T>
│   └── deque_template.c       # Parameterized deque<T>
├── type_traits/
│   ├── hash_functions.c       # Hash for various types
│   ├── compare_functions.c    # Comparison for various types
│   └── copy_functions.c       # Clone/free for various types
└── utils/
    ├── memory.c               # Memory allocation helpers
    └── error.c                # Error handling
```

## Open Questions

1. **Template Language**: Use Python string formatting, Jinja2, or custom DSL?
2. **Optimization Level**: How aggressive should tree-shaking be?
3. **Debug Support**: Generate debug-mode versions with assertions?
4. **Documentation**: Generate inline comments explaining the code?
5. **Multiple Files**: How to handle multi-file projects (headers vs inline)?

## Future Enhancements

1. **Generic Containers**: Support arbitrary types via template expansion
   ```python
   generate_map("MyStruct*", "MyOtherStruct*")
   ```

2. **Custom Allocators**: Allow user-specified allocators
   ```python
   generate_map("char*", "int", allocator="arena_alloc")
   ```

3. **Thread Safety**: Generate thread-safe versions when needed
   ```python
   generate_map("char*", "int", thread_safe=True)
   ```

4. **Optimization Profiles**: Different implementations for different use cases
   - Small maps: Linear search
   - Large maps: Hash table
   - Dense integer keys: Direct array

## References

- **C++ Templates**: Monomorphization approach
- **Rust Generics**: Zero-cost abstractions via code generation
- **D Templates**: Compile-time code generation
- **Zig Comptime**: Compile-time execution for code generation

## Conclusion

Generated container code is the superior approach for a code generator:
- ✅ Aligns with code generation philosophy (self-contained output)
- ✅ Zero external dependencies
- ✅ Maximum type safety and optimization
- ✅ Superior debugging experience
- ✅ Minimal code (only what's needed)
- ✅ Industry-standard approach (like C++ templates)

The v0.1.37 runtime library should be viewed as a **working prototype** and **template source**, not the final architecture. The path forward is clear: convert runtime libraries into code generation templates.
