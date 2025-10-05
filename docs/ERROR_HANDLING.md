# Error Handling Guide

**Version**: v0.1.58+
**Status**: Production Ready

This guide explains how MGen handles errors and how to interpret error messages.

---

## Overview

MGen provides enhanced error messages with:
- **Source location** - Exact file, line, and column where error occurred
- **Colored output** - Color-coded error messages for better readability
- **Helpful suggestions** - Actionable advice to fix common errors
- **Error codes** - Categorized error codes for documentation lookup
- **Source snippets** - Show the problematic code with visual indicators

---

## Error Message Format

A typical MGen error looks like this:

```
error[E1001]: Generator expressions are not supported
  --> example.py:42:10
   |
42 |     result = (x for x in range(10))
               ^^^^^^^^^^^^^^^^^^^^^^
   |
help: Use a list comprehension instead: [x for x in range(10)]
note: See https://github.com/yourusername/mgen/docs/supported-features.md
```

### Components

1. **Error label** (`error[E1001]`) - Error severity and code
2. **Message** - Clear description of what went wrong
3. **Location** (`example.py:42:10`) - File:line:column
4. **Source snippet** - The problematic code with caret (^) indicator
5. **Help** - Suggested fix or workaround
6. **Note** - Additional context or documentation link

---

## Error Codes

MGen uses categorized error codes to help you quickly identify the type of error:

### E1xxx - Feature Support Errors

| Code | Description | Common Cause |
|------|-------------|--------------|
| E1001 | Unsupported feature | Using Python feature not yet supported by MGen |
| E1002 | Unsupported statement | Statement type not supported in target backend |
| E1003 | Unsupported expression | Expression type not supported |
| E1004 | Unsupported operator | Operator not available in target language |
| E1005 | Unsupported constant type | Constant type cannot be translated |

**Example**:
```python
# Python code
async def fetch_data():  # E1001: async not supported
    pass
```

**Fix**: Remove `async` keyword and use synchronous functions.

### E2xxx - Type System Errors

| Code | Description | Common Cause |
|------|-------------|--------------|
| E2001 | Type mapping failed | Type annotation cannot be mapped to target language |
| E2002 | Type inference failed | Cannot infer type from context |
| E2003 | Incompatible types | Type mismatch in operation |
| E2004 | Missing type annotation | Required type annotation not provided |

**Example**:
```python
# Python code
def process(data: CustomGeneric[T, K]):  # E2001: complex generic
    pass
```

**Fix**: Use simpler types like `dict[str, Any]` or concrete types.

### E3xxx - Syntax Errors

| Code | Description | Common Cause |
|------|-------------|--------------|
| E3001 | Invalid syntax | Python syntax error in source file |
| E3002 | Parse error | Unable to parse Python source |

### E4xxx - Import/Module Errors

| Code | Description | Common Cause |
|------|-------------|--------------|
| E4001 | Import not found | Module or symbol not found |
| E4002 | Circular import | Circular dependency detected |

### E5xxx - Runtime Errors

| Code | Description | Common Cause |
|------|-------------|--------------|
| E5001 | Code generation failed | Error during target code generation |
| E5002 | Compilation failed | Target compiler error |

---

## Common Errors and Solutions

### Generator Expressions (E1001)

**Error**:
```
error[E1001]: Generator expressions are not supported
```

**Fix**: Use list comprehensions instead:
```python
# Before (not supported)
result = (x * 2 for x in items)

# After (supported)
result = [x * 2 for x in items]
```

### Async/Await (E1001)

**Error**:
```
error[E1001]: Async functions are not supported
```

**Fix**: Use synchronous functions:
```python
# Before (not supported)
async def fetch_data():
    await some_operation()

# After (supported)
def fetch_data():
    some_operation()
```

### Context Managers (E1001)

**Error**:
```
error[E1001]: Context managers (with statement) are not supported
```

**Fix**: Use try/finally for cleanup:
```python
# Before (not supported)
with open('file.txt') as f:
    data = f.read()

# After (supported)
f = open('file.txt')
try:
    data = f.read()
finally:
    f.close()
```

### Lambda Expressions (E1001)

**Error**:
```
error[E1001]: Lambda expressions are not fully supported
```

**Fix**: Use named functions:
```python
# Before (limited support)
callback = lambda x: x * 2

# After (fully supported)
def callback(x):
    return x * 2
```

### *args and **kwargs (E1001)

**Error**:
```
error[E1001]: *args and **kwargs are not supported
```

**Fix**: Use explicit parameters:
```python
# Before (not supported)
def process(*args, **kwargs):
    pass

# After (supported)
def process(items: list[int], options: dict[str, str]):
    pass
```

---

## Disabling Colors

For CI/CD environments or terminals without color support, you can disable colored output:

```bash
# Disable colors
mgen convert example.py --no-color

# Or set environment variable
export NO_COLOR=1
mgen convert example.py
```

---

## For Backend Developers

### Raising Errors in Your Code

When developing MGen backends, use the enhanced error classes:

```python
from mgen.errors import UnsupportedFeatureError, ErrorCode

# Basic error
raise UnsupportedFeatureError("Decorators are not supported")

# Error with location and suggestion
from mgen.errors import SourceLocation

location = SourceLocation(filename="example.py", line=42, column=10)
raise UnsupportedFeatureError(
    "Decorators are not supported",
    location=location,
    suggestion="Remove decorator or use a regular function call",
    error_code=ErrorCode.E1001,
)

# Error from AST node (preferred)
error = UnsupportedFeatureError.from_ast_node(
    message="Decorators are not supported",
    node=decorator_node,
    filename=source_filename,
    suggestion="Remove decorator or use a regular function call",
    error_code=ErrorCode.E1001,
)
```

### Helper Functions

Use helper functions for common error patterns:

```python
from mgen.errors import create_unsupported_feature_error

error = create_unsupported_feature_error(
    feature_name="generator expression",
    node=ast_node,
    filename="example.py",
    backend="Rust"
)
# Automatically includes helpful suggestion and documentation link
```

---

## Best Practices

1. **Always include source location** when possible (from AST nodes)
2. **Provide actionable suggestions** - Tell users how to fix the error
3. **Use appropriate error codes** - Helps users find documentation
4. **Include source context** - Show the problematic code
5. **Link to documentation** - Guide users to more information

---

## Future Enhancements

Planned improvements to error handling:

- [ ] "Did you mean?" suggestions for typos
- [ ] Multi-line error spans
- [ ] Related error grouping
- [ ] JSON error output for IDE integration
- [ ] Error recovery suggestions with code examples
- [ ] Interactive error fixing (mgen --fix)

---

## See Also

- [Supported Python Features](SUPPORTED_FEATURES.md)
- [Backend Development Guide](BACKEND_DEVELOPMENT.md)
- [Contributing Guide](../CONTRIBUTING.md)

---

**Last Updated**: 2025-10-05
**Version**: v0.1.58
