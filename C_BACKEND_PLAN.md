# C Backend Improvement Plan

## Executive Summary

Analysis of mgen's C backend against the cgen reference implementation reveals critical missing features that cause 96.3% of translation tests to fail. This document outlines the gaps, provides implementation guidance, and prioritizes fixes.

## Test Results Comparison

### Current State

**MGen C Backend (v0.1.85-dev)**
- Translation tests: 1/27 passing (3.7% success rate)
- Only passing: `test_string_membership.py`
- Status: 26 files failing to build
- Root cause: Missing assert/dataclass support + broken error handling

**CGen Reference (Comparison Baseline)**
- Translation tests: 11/20 passing (55% success rate)
- Comprehensive assert, dataclass, namedtuple support
- Production-ready error handling
- File: `~/projects/cgen/src/cgen/generator/py2c.py`

**Gap Analysis**: 51.3 percentage point deficit in test pass rate

## Failure Breakdown

### 1. Assert Statement Failures (14 files - 52%)

**Affected Files:**
- container_iteration_test.py
- simple_infer_test.py
- simple_test.py
- string_methods_test.py
- test_container_iteration.py
- test_control_flow.py
- test_list_slicing.py
- test_math_import.py
- test_simple_slice.py
- test_simple_string_ops.py
- test_string_membership_simple.py
- test_string_methods_new.py
- test_string_methods.py
- test_string_split_simple.py

**Problem**: No handler for `ast.Assert` statements

**Current Behavior**:
1. `converter.py:549` raises `UnsupportedFeatureError`
2. `emitter.py:67` catches exception and attempts fallback
3. Fallback emits `/* TODO: Enhanced statement generation */` for ALL statements
4. Generated code won't compile

**Example Failure** (`simple_test.py`):
```python
def main() -> int:
    result: int = simple_test()
    assert result == 1  # <-- Triggers failure
    return result
```

Generated broken code:
```c
int main(void) {
    /* TODO: Enhanced statement generation */
    /* TODO: Enhanced statement generation */
    return result;  // <-- 'result' undefined!
}
```

### 2. Dataclass Failures (2 files - 7%)

**Affected Files:**
- test_dataclass_basic.py
- test_struct_field_access.py

**Problem**: Dataclass decorator not recognized; empty structs generated

**Current Behavior**:
```c
// Current mgen output (BROKEN)
typedef struct Point {
    char _dummy;  // Empty struct placeholder
} Point;

int main(void) {
    Point p = Point_new(10, 20);  // <-- Point_new doesn't exist!
    return 0;
}
```

**Expected Behavior** (from cgen):
```c
// Expected output
typedef struct {
    int x;
    int y;
} Point;

Point make_Point(int x, int y) {
    return (Point){x, y};
}

int main(void) {
    Point p;
    p = make_Point(10, 20);  // <-- Works!
    return 0;
}
```

### 3. NamedTuple Failures (1 file - 4%)

**Affected Files:**
- test_namedtuple_basic.py

**Problem**: NamedTuple not detected; treated as regular class

### 4. Compilation Errors (9 files - 33%)

**Affected Files:**
- nested_2d_params.py
- nested_2d_return.py
- nested_2d_simple.py
- nested_containers_comprehensive.py
- nested_dict_list.py
- test_2d_simple.py
- test_dict_comprehension.py
- test_list_comprehension.py
- test_set_support.py

**Problem**: Build phase reports "Build phase failed" but CLI says "Compilation successful! Executable: None"

**Investigation Needed**: These files generate valid-looking C code but don't produce executables. Possible runtime library linking issues.

## Missing AST Node Support

### Critical Missing Nodes (in CGen but not MGen)

| AST Node | Usage | Impact |
|----------|-------|--------|
| `ast.Assert` | Assert statements | 14 files broken |
| `ast.Import` | Import statements | Limited import support |
| `ast.ImportFrom` | From imports | Limited import support |
| `ast.BoolOp` | Boolean and/or | Control flow issues |
| `ast.Slice` | Explicit slicing | Slicing may not work |
| Comparison operators | Eq, Gt, GtE, Lt, LtE, NotEq | Comparison limitations |

### MGen-Exclusive Nodes (not in CGen)

| AST Node | Usage | Status |
|----------|-------|--------|
| `ast.FormattedValue` | F-strings | ✓ Working (v0.1.86) |
| `ast.JoinedStr` | F-strings | ✓ Working (v0.1.86) |
| `ast.FloorDiv` | Floor division | ✓ Working |
| `ast.Pow` | Power operator | ✓ Working |

## Root Cause Analysis

### Architecture Issue

The mgen C backend was adapted from cgen but the integration is incomplete:

1. **Sophisticated conversion added** (`converter.py` - 2,485 lines)
   - Multi-pass type inference
   - Container code generation
   - STC integration

2. **Error handling broken** (`emitter.py:62-72`)
   ```python
   def emit_module(self, source_code: str, analysis_result: Optional[Any] = None) -> str:
       try:
           # Try sophisticated py2c conversion first
           return self.py2c_converter.convert_code(source_code)
       except UnsupportedFeatureError as e:
           # Fall back to basic conversion with warning
           return f"/* Py2C conversion failed: {e} */\n" + self._emit_module_with_runtime(source_code)
   ```

3. **Fallback doesn't work**
   - Basic emission doesn't implement statement conversion
   - Results in `/* TODO: Enhanced statement generation */` output
   - Entire function body becomes invalid

### Comparison with CGen

**CGen Architecture** (Production-Ready):
```
Python AST → py2c.py (conversion) → core.py (C AST) → writer.py (emission) → C code
```
- Clean separation of concerns
- RawCode elements for direct C injection
- Explicit include management
- Comprehensive error messages

**MGen Architecture** (Hybrid):
```
Python AST → converter.py (conversion + emission) → C code
```
- Direct string-based generation
- Sophisticated type inference
- Runtime library integration
- Broken error paths

## Implementation Plan

### Phase 1: Critical Fixes (High Priority)

#### 1.1 Add Assert Statement Support
**Impact**: Fixes 14 files (52% of failures)
**Effort**: Low (30-60 minutes)
**Files**: `src/mgen/backends/c/converter.py`

**Implementation**:

Location: `converter.py:546` (in `_convert_statement` method)

```python
def _convert_statement(self, stmt: ast.stmt) -> str:
    """Convert Python statement to C code."""
    if isinstance(stmt, ast.Return):
        return self._convert_return(stmt)
    elif isinstance(stmt, ast.Assign):
        return self._convert_assignment(stmt)
    # ... existing handlers ...
    elif isinstance(stmt, ast.Pass):
        return "/* pass */"
    elif isinstance(stmt, ast.Assert):  # <-- ADD THIS
        return self._convert_assert(stmt)
    else:
        raise UnsupportedFeatureError(f"Unsupported statement type: {type(stmt).__name__}")
```

Add new method after `_convert_pass`:

```python
def _convert_assert(self, stmt: ast.Assert) -> str:
    """Convert Python assert statement to C assert() call.

    Args:
        stmt: Python assert statement node

    Returns:
        C assert() call as string

    Example:
        assert x > 0  →  assert(x > 0);
        assert result == 1, "Test failed"  →  assert(result == 1); // Test failed
    """
    # Convert the test expression
    test_expr = self._convert_expression(stmt.test)

    # Handle optional message
    if stmt.msg:
        # Convert message to string
        if isinstance(stmt.msg, ast.Constant):
            msg = stmt.msg.value
            return f"assert({test_expr}); // {msg}"
        else:
            # Complex message expression - just add assert without comment
            return f"assert({test_expr});"
    else:
        return f"assert({test_expr});"
```

Update `_generate_includes()` to add assert.h when needed:

```python
def _generate_includes(self) -> list[str]:
    """Generate C include statements."""
    includes = [
        "#include <stdio.h>",
        "#include <stdlib.h>",
        "#include <stdbool.h>",
    ]

    # Add assert.h if asserts are used
    if self._uses_asserts:
        includes.append("#include <assert.h>")

    # ... rest of includes ...
    return includes
```

Add detection method:

```python
def _detect_asserts(self, node: ast.AST) -> bool:
    """Check if module uses assert statements."""
    for child in ast.walk(node):
        if isinstance(child, ast.Assert):
            return True
    return False
```

Update `_convert_module()` to set flag:

```python
def _convert_module(self, node: ast.Module) -> str:
    """Convert a Python module to C code."""
    parts = []

    # ... existing code ...

    # Detect asserts for include generation
    self._uses_asserts = self._detect_asserts(node)

    # ... rest of conversion ...
```

**Testing**:
```bash
# After implementation
uv run mgen build -t c tests/translation/simple_test.py
./build/simple_test  # Should run without errors
```

**Reference**: `~/projects/cgen/src/cgen/generator/py2c.py:835-850`

#### 1.2 Add Dataclass Support
**Impact**: Fixes 2 files (7% of failures)
**Effort**: Medium (2-3 hours)
**Files**: `src/mgen/backends/c/converter.py`

**Implementation**:

Add dataclass detection:

```python
def _is_dataclass(self, node: ast.ClassDef) -> bool:
    """Check if class has @dataclass decorator.

    Args:
        node: Class definition node

    Returns:
        True if class has @dataclass decorator

    Example:
        @dataclass
        class Point:
            x: int
            y: int
    """
    for decorator in node.decorator_list:
        # Handle @dataclass
        if isinstance(decorator, ast.Name) and decorator.id == "dataclass":
            return True
        # Handle @dataclass(...) with arguments
        elif isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name):
            if decorator.func.id == "dataclass":
                return True
    return False
```

Extract dataclass fields from annotations:

```python
def _extract_dataclass_fields(self, node: ast.ClassDef) -> dict[str, str]:
    """Extract field names and types from dataclass.

    Args:
        node: Dataclass definition node

    Returns:
        Dictionary mapping field names to C types

    Example:
        @dataclass
        class Point:
            x: int  →  {"x": "int"}
            y: int  →  {"y": "int"}
    """
    fields = {}

    for stmt in node.body:
        if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
            field_name = stmt.target.id

            # Extract type annotation
            if isinstance(stmt.annotation, ast.Name):
                python_type = stmt.annotation.id
                c_type = self.type_mapping.get(python_type, "int")
                fields[field_name] = c_type
            elif isinstance(stmt.annotation, ast.Subscript):
                # Handle generic types like list[int]
                c_type = self._extract_c_type_from_annotation(stmt.annotation)
                fields[field_name] = c_type

    return fields
```

Generate dataclass constructor:

```python
def _generate_dataclass_constructor(self, struct_name: str, fields: dict[str, str]) -> str:
    """Generate constructor function for dataclass.

    Args:
        struct_name: Name of the struct
        fields: Dictionary of field names to C types

    Returns:
        C constructor function as string

    Example:
        make_Point(int x, int y) { return (Point){x, y}; }
    """
    # Create parameter list
    params = [f"{c_type} {name}" for name, c_type in fields.items()]
    params_str = ", ".join(params)

    # Create field list for initialization
    field_names = ", ".join(fields.keys())

    # Generate constructor function
    constructor = f"""{struct_name} make_{struct_name}({params_str})
{{
    return ({struct_name}){{{field_names}}};
}}"""

    return constructor
```

Update `_convert_class()` to handle dataclasses:

```python
def _convert_class(self, node: ast.ClassDef) -> str:
    """Convert Python class to C struct with associated methods."""
    class_name = node.name

    # Check if this is a dataclass
    is_dataclass = self._is_dataclass(node)

    if is_dataclass:
        # Extract fields from annotations
        fields = self._extract_dataclass_fields(node)

        # Generate struct definition
        field_lines = [f"    {c_type} {name};" for name, c_type in fields.items()]
        struct_def = f"""typedef struct {{
{chr(10).join(field_lines)}
}} {class_name};"""

        # Generate constructor
        constructor = self._generate_dataclass_constructor(class_name, fields)

        # Store struct info
        self.defined_structs[class_name] = {
            "instance_vars": fields,
            "attributes": fields,
            "is_dataclass": True,
        }

        return f"{struct_def}\n\n{constructor}"
    else:
        # Regular class - use existing logic
        # ... existing implementation ...
```

**Testing**:
```bash
uv run mgen build -t c tests/translation/test_dataclass_basic.py
./build/test_dataclass_basic  # Should run successfully
```

**Reference**: `~/projects/cgen/src/cgen/generator/py2c.py:657-779`

#### 1.3 Fix Error Handling
**Impact**: Prevents cascading failures
**Effort**: Low (1 hour)
**Files**: `src/mgen/backends/c/emitter.py`

**Problem**: When unsupported feature encountered, entire function breaks

**Current Code** (`emitter.py:62-72`):
```python
def emit_module(self, source_code: str, analysis_result: Optional[Any] = None) -> str:
    try:
        return self.py2c_converter.convert_code(source_code)
    except UnsupportedFeatureError as e:
        # Fall back to basic conversion with warning
        return f"/* Py2C conversion failed: {e} */\n" + self._emit_module_with_runtime(source_code)
```

**Fix**:
```python
def emit_module(self, source_code: str, analysis_result: Optional[Any] = None) -> str:
    try:
        return self.py2c_converter.convert_code(source_code)
    except UnsupportedFeatureError as e:
        # Log detailed error and fail gracefully
        error_msg = f"C backend does not support: {e}"
        raise UnsupportedFeatureError(error_msg) from e
    except Exception as e:
        # Unexpected error - provide diagnostics
        error_msg = f"C code generation failed: {e}\n"
        error_msg += "Please report this issue with the input file."
        raise UnsupportedFeatureError(error_msg) from e
```

Remove broken fallback in `_emit_module_with_runtime()` - it doesn't work and causes confusion.

**Update CLI** (`src/mgen/cli.py`):

Fix misleading success message:

```python
# Current (WRONG):
if result.executable_path:
    self.logger.info(f"Compilation successful! Executable: {result.executable_path}")
else:
    self.logger.info(f"Compilation successful! Executable: None")  # <-- Misleading!

# Fixed:
if result.executable_path:
    self.logger.info(f"Compilation successful! Executable: {result.executable_path}")
else:
    self.logger.error("Build failed: No executable produced")
    sys.exit(1)
```

### Phase 2: NamedTuple Support (Medium Priority)

#### 2.1 Add NamedTuple Detection
**Impact**: Fixes 1 file (4% of failures)
**Effort**: Low (1 hour)
**Files**: `src/mgen/backends/c/converter.py`

**Implementation**:

```python
def _is_namedtuple(self, node: ast.ClassDef) -> bool:
    """Check if class inherits from NamedTuple.

    Args:
        node: Class definition node

    Returns:
        True if class inherits from NamedTuple

    Example:
        class Point(NamedTuple):
            x: int
            y: int
    """
    for base in node.bases:
        if isinstance(base, ast.Name):
            if base.id == "NamedTuple":
                return True
        elif isinstance(base, ast.Attribute):
            if base.attr == "NamedTuple":
                return True
    return False
```

Update `_convert_class()`:

```python
def _convert_class(self, node: ast.ClassDef) -> str:
    """Convert Python class to C struct with associated methods."""
    class_name = node.name

    # Check if this is a dataclass or namedtuple
    is_dataclass = self._is_dataclass(node)
    is_namedtuple = self._is_namedtuple(node)

    if is_dataclass or is_namedtuple:
        # Extract fields from annotations
        fields = self._extract_dataclass_fields(node)

        # Generate struct definition
        field_lines = [f"    {c_type} {name};" for name, c_type in fields.items()]
        struct_def = f"""typedef struct {{
{chr(10).join(field_lines)}
}} {class_name};"""

        # Generate constructor (only for dataclass, not namedtuple)
        if is_dataclass:
            constructor = self._generate_dataclass_constructor(class_name, fields)
            return f"{struct_def}\n\n{constructor}"
        else:
            # NamedTuple - just struct definition
            return struct_def
    else:
        # Regular class - use existing logic
        # ... existing implementation ...
```

**Reference**: `~/projects/cgen/src/cgen/generator/py2c.py:727-736`

### Phase 3: Additional AST Nodes (Lower Priority)

#### 3.1 Add BoolOp Support
**Impact**: Better control flow support
**Effort**: Low (30 minutes)

```python
def _convert_boolop(self, expr: ast.BoolOp) -> str:
    """Convert boolean operation (and/or).

    Args:
        expr: BoolOp node

    Returns:
        C boolean expression

    Example:
        x > 0 and y < 10  →  (x > 0) && (y < 10)
        a or b  →  (a) || (b)
    """
    # Determine operator
    if isinstance(expr.op, ast.And):
        op = "&&"
    elif isinstance(expr.op, ast.Or):
        op = "||"
    else:
        raise UnsupportedFeatureError(f"Unsupported boolean operator: {type(expr.op).__name__}")

    # Convert operands
    operands = [f"({self._convert_expression(val)})" for val in expr.values]

    # Join with operator
    return f" {op} ".join(operands)
```

Update `_convert_expression()`:

```python
def _convert_expression(self, expr: ast.expr) -> str:
    """Convert Python expression to C expression."""
    # ... existing handlers ...
    elif isinstance(expr, ast.BoolOp):
        return self._convert_boolop(expr)
    # ... rest ...
```

#### 3.2 Add Import/ImportFrom Support
**Impact**: Better module support
**Effort**: Medium (2 hours)

This requires coordination with the module system and is lower priority since the benchmark suite works.

## Testing Strategy

### Phase 1 Testing (After Critical Fixes)

Run all translation tests:

```bash
#!/bin/bash
# test_c_backend.sh

echo "=== C Backend Translation Tests ==="
echo ""

success=0
total=0

for py_file in tests/translation/*.py; do
    total=$((total + 1))
    filename=$(basename "$py_file")

    if uv run mgen build -t c "$py_file" 2>&1 | grep -q "Compilation successful"; then
        exec_name="build/$(basename "$py_file" .py)"
        if [ -f "$exec_name" ] && [ -x "$exec_name" ]; then
            echo "✓ $filename"
            success=$((success + 1))
        else
            echo "✗ $filename [NO EXECUTABLE]"
        fi
    else
        echo "✗ $filename [BUILD FAILED]"
    fi
done

echo ""
echo "Results: $success/$total passing ($(awk "BEGIN {printf \"%.1f\", ($success/$total)*100}")%)"
```

### Success Criteria

**Phase 1 Complete**:
- Assert support: 14+ files passing (simple_test.py, test_control_flow.py, etc.)
- Dataclass support: 2+ files passing (test_dataclass_basic.py, test_struct_field_access.py)
- Error handling: No more "Compilation successful! Executable: None" messages
- Minimum 60% pass rate (16/27 files)

**Phase 2 Complete**:
- NamedTuple support: 1+ file passing (test_namedtuple_basic.py)
- Minimum 65% pass rate (17/27 files)

### Regression Testing

After each change, run:

```bash
# Ensure benchmarks still work
make benchmark-c

# Ensure existing tests pass
make test

# Type check
make type-check
```

## Known Issues to Investigate

### Compilation Errors (9 files)

These files generate C code but don't produce executables:

- nested_2d_params.py
- nested_2d_return.py
- nested_2d_simple.py
- nested_containers_comprehensive.py
- nested_dict_list.py
- test_2d_simple.py
- test_dict_comprehension.py
- test_list_comprehension.py
- test_set_support.py

**Investigation needed**:
1. Check if C code compiles manually with gcc
2. Verify runtime library is copied to build directory
3. Check for linker errors in build logs
4. May be related to nested container support or STC library issues

## Code Quality Standards

### Before Committing

1. **Zero test regressions**: All existing tests must pass
2. **Type safety**: Run `make type-check` (mypy strict mode)
3. **Code formatting**: Run `make format`
4. **Linting**: Run `make lint`
5. **Documentation**: Update CHANGELOG.md with changes
6. **Commit message**: Follow conventional commits format

### Implementation Guidelines

1. **Reference cgen implementation**: Use `~/projects/cgen/src/cgen/generator/py2c.py` as reference
2. **Maintain architecture**: Keep mgen's multi-backend architecture intact
3. **Type annotations**: Use Python 3.9+ PEP 585 style annotations
4. **Error messages**: Provide clear, actionable error messages
5. **Comments**: Document complex logic and edge cases

## Timeline Estimate

**Phase 1 (Critical Fixes)**:
- Assert support: 1 hour
- Dataclass support: 3 hours
- Error handling: 1 hour
- Testing: 1 hour
- **Total: 6 hours**

**Phase 2 (NamedTuple)**:
- Implementation: 1 hour
- Testing: 0.5 hours
- **Total: 1.5 hours**

**Phase 3 (Additional nodes)**:
- BoolOp: 0.5 hours
- Import/ImportFrom: 2 hours
- Testing: 1 hour
- **Total: 3.5 hours**

**Grand Total**: ~11 hours for complete implementation

## Success Metrics

### Current State (Baseline)
- Translation test pass rate: 3.7% (1/27)
- Benchmark pass rate: 100% (7/7)
- Production-ready: No (critical features missing)

### Target State (After Phase 1)
- Translation test pass rate: ≥60% (16/27)
- Benchmark pass rate: 100% (7/7, maintained)
- Production-ready: Partial (assert + dataclass support)

### Target State (After Phase 2)
- Translation test pass rate: ≥65% (17/27)
- Benchmark pass rate: 100% (7/7, maintained)
- Production-ready: Yes (feature-complete for common use cases)

## References

### CGen Implementation
- **Main converter**: `~/projects/cgen/src/cgen/generator/py2c.py`
- **Assert handling**: Lines 835-850
- **Dataclass handling**: Lines 657-779
- **NamedTuple handling**: Lines 727-736
- **Core C AST**: `~/projects/cgen/src/cgen/generator/core.py`
- **Writer**: `~/projects/cgen/src/cgen/generator/writer.py`

### MGen Implementation
- **Main converter**: `src/mgen/backends/c/converter.py`
- **Emitter**: `src/mgen/backends/c/emitter.py`
- **Container system**: `src/mgen/backends/c/containers.py`
- **Type inference**: `src/mgen/backends/c/enhanced_type_inference.py`

### Documentation
- **MGen architecture**: `CLAUDE.md`
- **Changelog**: `CHANGELOG.md`
- **Production roadmap**: `PRODUCTION_ROADMAP.md`

## Appendix A: Detailed Test Results

### MGen C Backend Test Results (27 files)

**Successful (1 file)**:
- ✓ test_string_membership.py

**Assert Failures (14 files)**:
- ✗ container_iteration_test.py
- ✗ simple_infer_test.py
- ✗ simple_test.py
- ✗ string_methods_test.py
- ✗ test_container_iteration.py
- ✗ test_control_flow.py
- ✗ test_list_slicing.py
- ✗ test_math_import.py
- ✗ test_simple_slice.py
- ✗ test_simple_string_ops.py
- ✗ test_string_membership_simple.py
- ✗ test_string_methods_new.py
- ✗ test_string_methods.py
- ✗ test_string_split_simple.py

**Dataclass Failures (2 files)**:
- ✗ test_dataclass_basic.py
- ✗ test_struct_field_access.py

**NamedTuple Failures (1 file)**:
- ✗ test_namedtuple_basic.py

**Compilation Failures (9 files)**:
- ✗ nested_2d_params.py
- ✗ nested_2d_return.py
- ✗ nested_2d_simple.py
- ✗ nested_containers_comprehensive.py
- ✗ nested_dict_list.py
- ✗ test_2d_simple.py
- ✗ test_dict_comprehension.py
- ✗ test_list_comprehension.py
- ✗ test_set_support.py

### CGen Reference Test Results (20 files)

**Successful (11 files)**:
- ✓ container_iteration_test.py
- ✓ simple_test.py
- ✓ string_methods_test.py
- ✓ test_control_flow.py
- ✓ test_dataclass_basic.py
- ✓ test_math_import.py
- ✓ test_namedtuple_basic.py
- ✓ test_set_support.py
- ✓ test_string_membership.py
- ✓ test_string_methods_new.py
- ✓ test_struct_field_access.py

**Failed (9 files)**:
- ✗ test_container_iteration.py
- ✗ test_dict_comprehension.py
- ✗ test_list_comprehension.py
- ✗ test_list_slicing.py
- ✗ test_simple_slice.py
- ✗ test_simple_string_ops.py
- ✗ test_string_membership_simple.py
- ✗ test_string_methods.py
- ✗ test_string_split_simple.py

## Appendix B: Example Code Transformations

### Assert Statement

**Python Input**:
```python
def main() -> int:
    result: int = simple_test()
    assert result == 1
    return result
```

**Current MGen Output (BROKEN)**:
```c
int main(void) {
    /* TODO: Enhanced statement generation */
    /* TODO: Enhanced statement generation */
    return result;
}
```

**Target Output**:
```c
#include <assert.h>

int main(void) {
    int result;
    result = simple_test();
    assert(result == 1);
    return result;
}
```

### Dataclass

**Python Input**:
```python
from dataclasses import dataclass

@dataclass
class Point:
    x: int
    y: int

def main() -> int:
    p: Point = Point(10, 20)
    return 0
```

**Current MGen Output (BROKEN)**:
```c
typedef struct Point {
    char _dummy;  // Empty struct placeholder
} Point;

int main(void) {
    Point p = Point_new(10, 20);  // Point_new doesn't exist!
    return 0;
}
```

**Target Output**:
```c
typedef struct {
    int x;
    int y;
} Point;

Point make_Point(int x, int y) {
    return (Point){x, y};
}

int main(void) {
    Point p;
    p = make_Point(10, 20);
    return 0;
}
```

### NamedTuple

**Python Input**:
```python
from typing import NamedTuple

class Coordinate(NamedTuple):
    x: float
    y: float

def main() -> int:
    coord = Coordinate(1.5, 2.5)
    return 0
```

**Target Output**:
```c
typedef struct {
    double x;
    double y;
} Coordinate;

int main(void) {
    Coordinate coord = {1.5, 2.5};
    return 0;
}
```

## Appendix C: File Locations Quick Reference

### Files to Modify

1. **`src/mgen/backends/c/converter.py`** (Primary)
   - Add `_convert_assert()` method
   - Add `_is_dataclass()` method
   - Add `_is_namedtuple()` method
   - Add `_extract_dataclass_fields()` method
   - Add `_generate_dataclass_constructor()` method
   - Update `_convert_statement()` to handle assert
   - Update `_convert_class()` to handle dataclass/namedtuple
   - Update `_generate_includes()` to add assert.h

2. **`src/mgen/backends/c/emitter.py`** (Secondary)
   - Fix error handling in `emit_module()`
   - Remove broken fallback logic

3. **`src/mgen/cli.py`** (Tertiary)
   - Fix misleading success message

### Files to Reference

1. **`~/projects/cgen/src/cgen/generator/py2c.py`**
   - Assert implementation: lines 835-850
   - Dataclass implementation: lines 657-779
   - NamedTuple implementation: lines 727-736

2. **`tests/translation/*.py`**
   - Test cases for validation

### Files to Update After Changes

1. **`CHANGELOG.md`** - Document all changes
2. **`CLAUDE.md`** - Update feature lists if needed
3. **`tests/translation/README.md`** - Update status

---

**Document Version**: 1.0
**Date**: 2025-10-18
**Author**: Analysis based on cgen comparison study
**Status**: Ready for implementation
