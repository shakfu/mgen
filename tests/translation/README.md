# MGen Translation Test Examples

This directory contains focused test cases for Python-to-C translation features. These files are specifically designed to test and validate core translation capabilities.

## Status (v0.1.100)

**Overall**: C backend now at **81% actual pass rate** (22/27 tests when counting computed return values correctly)

**Recent Fixes**:
- Tier 1 (v0.1.93): Type casting, string membership
- Tier 2 (v0.1.94): List slicing, set methods
- Category A (v0.1.95-96): Container detection, set iteration
- Category B (v0.1.97): String operations (`len()`, concatenation)
- Category C (v0.1.98): Nested container type inference (2D arrays)
- Category D (v0.1.99): Dict comprehension type inference
- **Phase 1 (v0.1.100)**: Validation fixes - math import and string ops

**Test Results (v0.1.100)**:
- **16 BUILD+RUN PASS** (59% nominal pass rate)
- **6 "Runtime Issues"** - False positives (tests return computed values, not errors)
- **5 BUILD FAIL** - Actual failures
- **Actual Pass Rate**: 22/27 = **81%** (when counting correctly)

**Implemented Features**:
- ✓ Type casting support (`int()`, `float()`, `str()`)
- ✓ String membership testing (`in` operator for strings)
- ✓ List slicing (`list[1:3]`, `list[1:]`, `list[:2]`, `list[::2]`)
- ✓ Set methods (`.add()`, `.remove()`, `.discard()`, `.clear()`)
- ✓ Set iteration using STC iterator API
- ✓ String length via `strlen()` instead of vec functions
- ✓ String concatenation with `+` operator
- ✓ String methods (`.upper()`, `.lower()`, `.strip()`, `.replace()`)
- ✓ Math library imports (`math.sqrt()`, `math.sin()`, `math.pow()`)
- ✓ Nested container parameters (`list` → `vec_vec_int` for 2D arrays)
- ✓ Nested container return types (automatic type upgrading)
- ✓ Dict comprehensions with type casting (`{str(x): x*2 for x in range(5)}`)

**Known Limitations** (5 remaining build failures):
- String array type mismatch (`mgen_string_array_t*` vs `vec_cstr`)
- Dict length function missing (`len()` on dict not supported yet)
- Dict-with-list-values not yet supported (requires `map_str_vec_int` type)
- Comprehensive nested containers (needs better type inference)

## Test Categories

### Container and Data Structure Tests

- `test_container_iteration.py` - Tests iteration over lists and sets
- `container_iteration_test.py` - Alternative container iteration tests
- `test_list_slicing.py` - Tests list slicing operations
- `test_simple_slice.py` - Simple slicing test cases
- `nested_2d_params.py` - Tests 2D array as function parameter
- `nested_2d_return.py` - Tests 2D array as return type
- `nested_2d_simple.py` - Simple 2D array test
- `nested_dict_list.py` - Dict with list values (not yet supported)
- `nested_containers_comprehensive.py` - Comprehensive nested container tests

### String Operation Tests

- `test_string_methods.py` - Tests string methods like `.upper()`, `.lower()`, `.find()`
- `string_methods_test.py` - Alternative string method tests
- `test_string_membership.py` - Tests string membership (`"x" in text`)
- `test_string_membership_simple.py` - Simplified string membership tests
- `test_string_methods_new.py` - Additional string method tests

### Basic Functionality Tests

- `simple_test.py` - Simple test case for basic functionality

## Purpose

These files are designed for:

- **Translation Testing**: Verifying that specific Python features translate correctly to C
- **Regression Testing**: Ensuring that changes don't break existing translation capabilities
- **Feature Validation**: Testing new translation features as they're implemented
- **Batch Testing**: Using with `cgen batch` command to test all translation features at once


## Note

For more complex demonstrations and examples beyond basic translation testing, see the `tests/demos/` directory.
