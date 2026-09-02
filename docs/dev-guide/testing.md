# Testing Guide

MultiGen has a comprehensive test suite covering all aspects of code generation.
A count is deliberately not quoted here: it goes stale on the next commit.

## Running Tests

`make test` runs the pytest suite but **excludes** `tests/translation`, which is
driven through the CLI rather than pytest. Run both before calling a change done:

```bash
# Unit and integration tests
make test

# End-to-end translation of the corpus in tests/translation
make test-translation

# Everything the CI target checks: tests, lint, types, formatting
make qa

# Or with uv
uv run pytest

# Run specific test file
uv run pytest tests/test_backend_c_basics.py

# Run specific test
uv run pytest tests/test_backend_c_basics.py::TestCBasics::test_basic_function

# Run with verbose output
uv run pytest -v
```

## Test Organization

Tests are organized by backend and feature:

```text
tests/
  test_backend_c_*.py           # C backend tests
  test_backend_cpp_*.py         # C++ backend tests
  test_backend_rust_*.py        # Rust backend tests
  test_backend_go_*.py          # Go backend tests
  test_backend_haskell_*.py     # Haskell backend tests
  test_backend_ocaml.py         # OCaml backend tests
  test_backend_llvm_*.py        # LLVM backend tests
  test_pipeline.py              # Pipeline tests
  test_type_inference.py        # Type inference tests
  test_exception_handling.py    # Exception handling tests
  test_context_managers.py      # Context manager tests
  test_generators.py            # Generator/yield tests
  test_check_slice_fspec_finally.py  # Slicing, format specs, finally/else tests
  benchmarks/                   # Benchmark test cases
```

## Benchmark Suite

MultiGen includes 7 comprehensive benchmarks:

**Algorithms**: fibonacci, quicksort, matmul, wordcount

**Data Structures**: list_ops, dict_ops, set_ops

```bash
# Run all benchmarks
make benchmark

# Generate benchmark report
make benchmark-report
```

The harness compares each generated program's output with CPython's and exits non-zero on any
mismatch, so its pass rate measures translation correctness rather than exit status. Current
per-backend rates are in the README; open defects are tracked in TODO.md.

## Writing Tests

Test template:

```python
class TestNewFeature:
    """Test suite for new feature."""

    def setup_method(self) -> None:
        self.converter = MultiGenPythonToCppConverter()

    def test_basic_case(self) -> None:
        """Test basic functionality."""
        code = '''
def example(x: int) -> int:
    return x + 1
'''
        result = self.converter.convert_code(code)
        assert "x + 1" in result

    def test_edge_case(self) -> None:
        """Test edge conditions."""
        # ...
```

## Test Quality Standards

- ALL tests must pass -- zero tolerance
- No flaky tests
- Unit tests: <100ms each
- Full suite: <25s
- Test happy path, edge cases, and error conditions

## Debugging Tests

```bash
# Verbose output
pytest -vv

# Show print statements
pytest -s

# Drop into debugger on failure
pytest --pdb

# Run single test with full output
pytest tests/test_file.py::test_name -vv -s
```

## Troubleshooting

**Import errors**:

```bash
export PYTHONPATH=src
pytest
```

**Z3 not available**:

```bash
pip install z3-solver
# Or skip Z3 tests
pytest -m "not verification"
```

## Next Steps

- [Contributing Guide](contributing.md) -- Contributing guidelines
- [Architecture](architecture.md) -- Understanding architecture
