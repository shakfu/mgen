# CGen Translation Test Examples

This directory contains focused test cases for Python-to-C translation features. These files are specifically designed to test and validate core translation capabilities.

## Test Categories

### Container and Data Structure Tests

- `test_container_iteration.py` - Tests iteration over lists and sets
- `container_iteration_test.py` - Alternative container iteration tests
- `test_list_slicing.py` - Tests list slicing operations
- `test_simple_slice.py` - Simple slicing test cases

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

## Usage

Test all translation features at once:

```bash
cgen batch -s examples --summary-only
```

Test individual translation features:

```bash
cgen convert examples/test_string_methods.py
cgen convert examples/test_container_iteration.py
```

## Note

For more complex demonstrations and examples beyond basic translation testing, see the `tests/demos/` directory.
