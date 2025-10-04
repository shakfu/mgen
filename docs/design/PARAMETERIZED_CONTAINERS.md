# Parameterized Container Code Generation System

**Version**: 0.2.0 (Phase 3)
**Date**: 2025-10-04
**Status**: Design & Implementation

## Overview

The Parameterized Container System enables automatic generation of container implementations for arbitrary type combinations by treating container templates as generic types with parameters, similar to C++ templates.

## Goals

1. **Eliminate Hardcoded Templates**: Replace 10+ individual template files with 3 generic templates
2. **Support Arbitrary Types**: Enable any valid type combination (e.g., `vec_float`, `map_str_bool`, `set_double`)
3. **Maintain Compatibility**: Generated code should be identical to current hardcoded templates
4. **Enable Full STC Independence**: Support all type combinations STC provides

## Architecture

### Current System (v0.1.43)

```
Hardcoded Approach:
- vec_int.h/c, vec_float.h/c, vec_double.h/c (3 nearly identical implementations)
- map_str_int.h/c, map_int_int.h/c, map_str_str.h/c (3 similar implementations)
- set_int.h/c, set_str.h/c (2 similar implementations)

Total: 10 container types = 20 template files
```

**Problem**: Adding `vec_bool` requires creating 2 new files and a new generator method.

### Parameterized System (v0.2.0)

```
Generic Template Approach:
- vec_T.h.tmpl, vec_T.c.tmpl (1 generic vector template)
- map_K_V.h.tmpl, map_K_V.c.tmpl (1 generic map template)
- set_T.h.tmpl, set_T.c.tmpl (1 generic set template)

Total: 3 container families = 6 template files
```

**Solution**: Adding `vec_bool` is automatic - just request it.

## Type Parameter System

### Supported Patterns

1. **Vector**: `vec_<T>` where T = element type
   - Examples: `vec_int`, `vec_float`, `vec_double`, `vec_bool`, `vec_char`

2. **Map**: `map_<K>_<V>` where K = key type, V = value type
   - Examples: `map_str_int`, `map_int_int`, `map_str_str`, `map_int_bool`

3. **Set**: `set_<T>` where T = element type
   - Examples: `set_int`, `set_str`, `set_float`, `set_double`

4. **Nested**: `vec_vec_<T>` where T = inner element type
   - Examples: `vec_vec_int`, `vec_vec_float`

### Type Mapping

Python types to C types:

```python
TYPE_MAPPINGS = {
    # Primitive types
    "int": "int",
    "float": "float",
    "double": "double",
    "bool": "bool",
    "char": "char",
    "str": "char*",

    # Pointer types
    "cstr": "char*",  # Alias for clarity

    # Container types (recursive)
    "vec_int": "vec_int",  # For nested containers
}
```

### Type Properties

Each type has properties that affect code generation:

```python
class TypeProperties:
    name: str           # "int", "float", "char*"
    c_type: str         # C type declaration
    is_pointer: bool    # Needs pointer semantics?
    needs_drop: bool    # Needs cleanup (free/drop)?
    printf_fmt: str     # Format specifier for printf
    zero_value: str     # Default/zero value
    compare_fn: str     # Comparison function (strcmp for strings, == for primitives)
```

Examples:
```python
INT_PROPS = TypeProperties(
    name="int",
    c_type="int",
    is_pointer=False,
    needs_drop=False,
    printf_fmt="%d",
    zero_value="0",
    compare_fn="=="
)

STR_PROPS = TypeProperties(
    name="char*",
    c_type="char*",
    is_pointer=True,
    needs_drop=True,  # Needs free()
    printf_fmt="%s",
    zero_value="NULL",
    compare_fn="strcmp"
)
```

## Template Substitution Engine

### Placeholder Syntax

Templates use `{{TYPE}}` placeholders:

```c
// vec_T.h.tmpl
typedef struct {
    {{T}}* data;        // Array of T
    size_t size;
    size_t capacity;
} vec_{{T_SUFFIX}};

void vec_{{T_SUFFIX}}_push(vec_{{T_SUFFIX}}* vec, {{T}} value);
{{T}}* vec_{{T_SUFFIX}}_at(vec_{{T_SUFFIX}}* vec, size_t index);
```

### Substitution Variables

For `vec_float`:
```python
{
    "T": "float",              # C type
    "T_SUFFIX": "float",       # Type name for function/struct names
    "T_ZERO": "0.0f",          # Zero value
    "T_NEEDS_DROP": False,     # No cleanup needed
    "T_COMPARE": "==",         # Comparison operator
}
```

For `vec_cstr`:
```python
{
    "T": "char*",
    "T_SUFFIX": "cstr",
    "T_ZERO": "NULL",
    "T_NEEDS_DROP": True,      # Needs free()
    "T_COMPARE": "strcmp",
}
```

### Conditional Code Generation

Some code is type-specific. Use conditional blocks:

```c
void vec_{{T_SUFFIX}}_drop(vec_{{T_SUFFIX}}* vec) {
    if (!vec) return;

    {{#T_NEEDS_DROP}}
    // Free each element if it's a pointer type
    for (size_t i = 0; i < vec->size; i++) {
        free(vec->data[i]);
    }
    {{/T_NEEDS_DROP}}

    free(vec->data);
    vec->data = NULL;
    vec->size = 0;
    vec->capacity = 0;
}
```

## Implementation Plan

### Phase 3.1: Core Infrastructure (Week 1)

**Tasks**:
1. Create `TypeProperties` class and type registry
2. Implement `TypeParameterExtractor` to parse type patterns
3. Create `TemplateSubstitutionEngine` with placeholder replacement
4. Write tests for type extraction and substitution

**Deliverables**:
- `src/mgen/backends/c/type_properties.py`
- `src/mgen/backends/c/template_engine.py`
- Tests validating type extraction and substitution

### Phase 3.2: Generic Templates (Week 2)

**Tasks**:
1. Create `vec_T.h.tmpl` and `vec_T.c.tmpl` generic templates
2. Validate against existing vec_int, vec_float implementations
3. Create `map_K_V.h.tmpl` and `map_K_V.c.tmpl` generic templates
4. Create `set_T.h.tmpl` and `set_T.c.tmpl` generic templates

**Deliverables**:
- `src/mgen/backends/c/templates/vec_T.h.tmpl`
- `src/mgen/backends/c/templates/vec_T.c.tmpl`
- Similar for map and set

### Phase 3.3: Integration (Week 3)

**Tasks**:
1. Update `ContainerCodeGenerator` to use parameterized system
2. Add fallback to hardcoded templates for compatibility
3. Update converter to request parameterized types
4. Comprehensive testing with all type combinations

**Deliverables**:
- Updated `container_codegen.py` with parameterized generation
- All 741 tests + benchmarks passing

### Phase 3.4: Type Inference Enhancement (Week 4)

**Tasks**:
1. Update type inference to detect and map all type combinations
2. Improve empty container initialization handling
3. Add type hint support for all combinations
4. Integration testing

**Deliverables**:
- Enhanced `enhanced_type_inference.py`
- Support for `dict[str, str]` → `map_str_str` etc.

## Benefits

1. **Code Reduction**: 20 template files → 6 template files (70% reduction)
2. **Maintainability**: Fix a bug once in generic template, affects all types
3. **Extensibility**: Adding new types is trivial
4. **Consistency**: All containers use identical patterns
5. **STC Independence**: Complete - no STC dependency for any type
6. **Type Safety**: Compile-time type checking preserved

## Migration Strategy

**Backward Compatibility**:
- Keep existing hardcoded templates as fallback
- Gradually enable parameterized generation per container family
- Run full test suite + benchmarks after each migration
- Ensure generated code is byte-for-byte identical

**Rollout Order**:
1. **Week 1**: Implement core infrastructure
2. **Week 2**: Vectors (simplest - single type parameter)
3. **Week 3**: Sets (similar to vectors)
4. **Week 4**: Maps (most complex - dual type parameters)

## Success Metrics

- [ ] All 741 unit tests pass
- [ ] All 7 benchmarks pass with identical output
- [ ] Generated code is ≤ 5% different in size from hardcoded templates
- [ ] Performance is within 5% of hardcoded templates
- [ ] Can generate 20+ type combinations without adding code

## Future Enhancements

**Phase 4: Advanced Features**
- Generic containers with custom hash functions
- Parameterized error handling
- Optimization hints per type
- Cross-backend template system (C++, Rust, Go)

---

**Status**: Ready to implement Phase 3.1
