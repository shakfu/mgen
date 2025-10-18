# MGen Translation Test Examples

This directory contains focused test cases for Python-to-C translation features. These files are specifically designed to test and validate core translation capabilities.

## Status (v0.1.98)

**Overall**: Significant improvements in C backend translation capabilities

**Recent Fixes**:
- Tier 1 (v0.1.93): Type casting, string membership
- Tier 2 (v0.1.94): List slicing, set methods
- Category A (v0.1.95-96): Container detection, set iteration
- Category B (v0.1.97): String operations (`len()`, concatenation)
- Category C (v0.1.98): Nested container type inference (2D arrays)

**Implemented Features**:
- ✓ Type casting support (`int()`, `float()`, `str()`)
- ✓ String membership testing (`in` operator for strings)
- ✓ List slicing (`list[1:3]`, `list[1:]`, `list[:2]`, `list[::2]`)
- ✓ Set methods (`.add()`, `.remove()`, `.discard()`, `.clear()`)
- ✓ Set iteration using STC iterator API
- ✓ String length via `strlen()` instead of vec functions
- ✓ String concatenation with `+` operator
- ✓ Nested container parameters (`list` → `vec_vec_int` for 2D arrays)
- ✓ Nested container return types (automatic type upgrading)

**Known Limitations**:
- Dict-with-list-values not yet supported (requires `map_int_vec_int` type)

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
