# Constraint Checker Split Proposal

**Objective**: Split monolithic `constraint_checker.py` (777 LOC) into two focused subsystems

---

## 🎯 Proposed Architecture

### 1. **MemorySafetyChecker** (C/C++ backends only)
**Location**: `src/mgen/backends/c/memory_safety.py` and `src/mgen/backends/cpp/memory_safety.py`

**Rules**: 4 core memory safety checks
- MS001: Buffer overflow potential
- MS002: Null pointer dereference
- MS003: Memory leak potential
- MS004: Dangling pointer risk

**Scope**: Python code analysis for C/C++ target safety
**When**: Validation phase (C/C++ only)
**Size**: ~250 LOC (reuse shared logic)

### 2. **PythonConstraintChecker** (Universal - all backends)
**Location**: `src/mgen/frontend/python_constraints.py`

**Rules**: 9 high-value Python validation checks

**Type Safety** (4 rules):
- TS001: Type consistency
- TS002: Implicit conversions
- TS003: Division by zero ⚠️
- TS004: Integer overflow ⚠️

**Static Analysis** (5 rules):
- SA001: Unreachable code
- SA002: Unused variables
- SA003: Uninitialized variables
- SA005: Parameter mutability (suggests better type annotations) ✨ NEW
- CC004: Function complexity

**Scope**: Python code quality and safety (language-agnostic)
**When**: Validation phase (all backends)
**Size**: ~400 LOC (focused implementation)

**Note**: SA005 reuses immutability analysis results from pipeline (no duplicate work)

### 3. **Removed/Deprecated** (4 rules)
- ❌ SA004: Infinite loops (false positives)
- ❌ CC001: Unsupported features (SubsetValidator handles this)
- ❌ CC002: Name conflicts (backend-specific, C-only concern)
- ❌ CC003: Reserved keywords (backends already handle)

---

## 📊 Split Analysis

### Current State (constraint_checker.py: 777 LOC)
```
Memory Safety (MS*):     4 rules  →  MemorySafetyChecker (C/C++)
Type Safety (TS*):       4 rules  →  PythonConstraintChecker (Universal)
Static Analysis (SA*):   4 rules  →  4 kept (all retained)
Compatibility (CC*):     4 rules  →  1 kept, 3 dropped/delegated
```

### After Split
```
MemorySafetyChecker:       4 rules, ~250 LOC (C/C++ backends)
PythonConstraintChecker:   9 rules, ~400 LOC (All backends)
Removed:                   4 rules, ~177 LOC (redundant/low-value)
ImmutabilityAnalyzer:      Moved to frontend (shared analysis)
```

**Net Change**: 777 LOC → 650 LOC (-16%), better architecture, improved code quality checks
**Bonus**: Immutability analysis now available to ALL backends (was Rust-only)

---

## 🔍 Detailed Rule Analysis

### MemorySafetyChecker Rules

#### MS001: Buffer Overflow Potential
**Why C/C++ only**: Manual array indexing, no bounds checking
**Implementation**: Analyze subscript operations for unsafe patterns
```python
arr[i]  # Warning: variable index without bounds check
arr[len(arr)]  # Error: index equals length (off-by-one)
```

#### MS002: Null Pointer Dereference
**Why C/C++ only**: Raw pointers, manual None checking
**Implementation**: Track None-able references and dereferences
```python
obj = get_object()  # May return None
obj.method()  # Warning: potential null dereference
```

#### MS003: Memory Leak Potential
**Why C/C++ only**: Manual malloc/free, no garbage collection
**Implementation**: Track allocations without corresponding frees
```python
def foo():
    data = create_buffer()  # Allocates
    return  # Warning: no cleanup
```

#### MS004: Dangling Pointer Risk
**Why C/C++ only**: Pointers to stack memory, manual lifetime management
**Implementation**: Detect returning references to local variables
```python
def get_ref():
    local_var = [1, 2, 3]
    return local_var  # Warning: C will return pointer to stack memory
```

### PythonConstraintChecker Rules

#### TS001: Type Consistency ✅
**Universal**: All backends need type validation
**Value**: Catches int/str mixing, list/dict confusion
**Example**:
```python
x: int = 5
y: str = "10"
z = x + y  # Error: type inconsistency
```

#### TS002: Implicit Conversions ✅
**Universal**: Different backends handle conversions differently
**Value**: Warns about lossy conversions
**Example**:
```python
f: float = 3.14
i: int = f  # Warning: implicit float->int conversion loses precision
```

#### TS003: Division by Zero ⚠️
**Universal**: Runtime error in ALL backends
**Value**: Critical safety check
**Example**:
```python
x = 10 / 0  # Error: division by zero
y = 10 / (z - z)  # Warning: potential division by zero
```

#### TS004: Integer Overflow ⚠️
**Universal**: Undefined behavior in most backends (except Python)
**Value**: Warns about potential overflow when translating to C/Rust/Go
**Example**:
```python
x: int = 2147483647  # INT_MAX in C
y = x + 1  # Warning: overflow in C/C++/Go/Rust (i32)
```

#### SA003: Uninitialized Variables ✅
**Universal**: All backends error on undefined variables
**Value**: Catches typos, missing initialization
**Example**:
```python
if condition:
    x = 5
print(x)  # Warning: x may be uninitialized
```

#### SA001: Unreachable Code ✅
**Universal**: Code quality check
**Value**: Detects dead code that will never execute
**Example**:
```python
def foo():
    return 5
    print("never executed")  # Warning: unreachable code
```

#### SA002: Unused Variables ✅
**Universal**: Code quality check
**Value**: Detects variables that are assigned but never used
**Example**:
```python
def bar():
    x = compute_value()  # Warning: variable 'x' is never used
    return 42
```

#### SA005: Parameter Mutability ✅ NEW
**Universal**: Code quality and type annotation improvement
**Value**: Suggests more restrictive type annotations for read-only parameters
**Reuses**: Immutability analysis results from pipeline (no duplicate work)
**Example**:
```python
def process_items(items: list[int]) -> int:  # items is never modified
    total = sum(items)
    return total

# SA005 Warning: Parameter 'items' is never modified
# Suggestion: Use tuple[int] or Sequence[int] for better type safety
```

#### CC004: Function Complexity ✅
**Universal**: Code quality metric
**Value**: Warns about overly complex functions
**Example**:
```python
def complex_function():  # 50 lines, 10 branches, 5 loops
    # Warning: cyclomatic complexity = 15 (threshold: 10)
```

---

## 🏗️ Implementation Design

### 1. MemorySafetyChecker

**File**: `src/mgen/backends/c/memory_safety.py`

```python
from dataclasses import dataclass
from enum import Enum

class MemorySafetyViolation(Enum):
    BUFFER_OVERFLOW = "buffer_overflow"
    NULL_DEREFERENCE = "null_dereference"
    MEMORY_LEAK = "memory_leak"
    DANGLING_POINTER = "dangling_pointer"

@dataclass
class MemorySafetyWarning:
    violation_type: MemorySafetyViolation
    message: str
    line: int
    severity: str  # "warning" | "error"

class MemorySafetyChecker:
    """C/C++ memory safety analysis for Python code."""

    def __init__(self):
        self.warnings: list[MemorySafetyWarning] = []

    def check_code(self, source_code: str) -> list[MemorySafetyWarning]:
        """Analyze Python code for C/C++ memory safety issues."""
        tree = ast.parse(source_code)

        self._check_buffer_overflows(tree)
        self._check_null_dereferences(tree)
        self._check_memory_leaks(tree)
        self._check_dangling_pointers(tree)

        return self.warnings

    def _check_buffer_overflows(self, tree: ast.AST) -> None:
        """Detect potential buffer overflow patterns."""
        # Implementation from current MS001
        ...
```

**Integration**:
```python
# src/mgen/backends/c/backend.py
from .memory_safety import MemorySafetyChecker

class CBackend(LanguageBackend):
    def validate_for_target(self, source_code: str) -> list[str]:
        checker = MemorySafetyChecker()
        warnings = checker.check_code(source_code)
        return [w.message for w in warnings]
```

### 2. PythonConstraintChecker

**File**: `src/mgen/frontend/python_constraints.py`

```python
from dataclasses import dataclass
from enum import Enum

class ConstraintCategory(Enum):
    TYPE_SAFETY = "type_safety"
    STATIC_ANALYSIS = "static_analysis"

@dataclass
class PythonConstraintViolation:
    category: ConstraintCategory
    rule_id: str
    message: str
    line: int
    severity: str  # "info" | "warning" | "error"

class PythonConstraintChecker:
    """Universal Python code constraint validation."""

    def __init__(self):
        self.violations: list[PythonConstraintViolation] = []
        self.type_engine = TypeInferenceEngine()

    def check_code(self, source_code: str) -> list[PythonConstraintViolation]:
        """Validate Python code for safety and quality."""
        tree = ast.parse(source_code)

        # Type safety
        self._check_type_consistency(tree)
        self._check_implicit_conversions(tree)
        self._check_division_by_zero(tree)
        self._check_integer_overflow(tree)

        # Static analysis & code quality
        self._check_unreachable_code(tree)
        self._check_unused_variables(tree)
        self._check_uninitialized_variables(tree)
        self._check_parameter_mutability(tree)  # SA005 - uses immutability results
        self._check_function_complexity(tree)

        return self.violations

    def _check_parameter_mutability(self, tree: ast.AST) -> None:
        """Suggest better type annotations for read-only parameters (SA005)."""
        if not self.immutability_results:
            return  # Skip if no immutability analysis available

        for func_name, params in self.immutability_results.items():
            for param, mutability in params.items():
                if mutability == MutabilityClass.READ_ONLY:
                    self.violations.append(
                        PythonConstraintViolation(
                            category=ConstraintCategory.CODE_QUALITY,
                            rule_id="SA005",
                            message=f"Parameter '{param}' in '{func_name}' is never modified. "
                                    f"Consider using immutable type (tuple, Sequence) for better type safety",
                            severity="info"
                        )
                    )
```

**Integration**:
```python
# src/mgen/pipeline.py
def _validation_phase(self, source_code: str, input_path: Path, result: PipelineResult) -> bool:
    # Universal Python constraints
    python_checker = PythonConstraintChecker()
    python_violations = python_checker.check_code(source_code)

    for violation in python_violations:
        if violation.severity == "error":
            result.errors.append(violation.message)
        else:
            result.warnings.append(violation.message)

    # Backend-specific memory safety (C/C++ only)
    if self.config.target_language in ["c", "cpp"]:
        memory_warnings = self.backend.validate_for_target(source_code)
        result.warnings.extend(memory_warnings)
```

---

## 🔄 Migration Plan

### Phase 1: Create New Modules (1-2 hours)

1. **Create `src/mgen/backends/c/memory_safety.py`**:
   - Extract MS001-MS004 from constraint_checker
   - Simplify to C/C++ focus
   - ~250 LOC

2. **Create `src/mgen/frontend/python_constraints.py`**:
   - Extract TS001-TS004, SA001-SA003, SA005, CC004
   - Remove backend-specific logic
   - ~400 LOC

3. ✅ **Move immutability analyzer to frontend** (DONE):
   - `analysis/immutability.py` → `frontend/immutability_analyzer.py`
   - Integrated into pipeline analysis phase
   - Available to all backends (was Rust-only)

### Phase 2: Update Pipeline Integration (1 hour)

1. **Modify `src/mgen/pipeline.py`**:
   - Replace constraint_checker with python_constraints (universal)
   - Add backend-specific validation hook
   - Remove C-only conditional

2. **Update Backend Interface**:
   - Add optional `validate_for_target()` method to LanguageBackend
   - C/C++ backends implement with MemorySafetyChecker
   - Other backends return empty list

### Phase 3: Test & Validate (2 hours)

1. **Update Tests**:
   - Split test_frontend.py constraint tests
   - Add test_memory_safety.py (C/C++ specific)
   - Add test_python_constraints.py (universal)

2. **Run Test Suite**:
   - Ensure all 855 tests still pass
   - Verify warnings appear correctly
   - Test with all 6 backends

### Phase 4: Cleanup (30 minutes)

1. **Delete Old Code**:
   - Remove `src/mgen/frontend/constraint_checker.py` (777 LOC)
   - Update imports

2. **Update Documentation**:
   - Update CLAUDE.md with new architecture
   - Document in CHANGELOG.md

**Total Effort**: ~5 hours

---

## ✅ Benefits

### 1. **Clearer Architecture**
- Memory safety checks clearly belong to C/C++ backends
- Python validation is universal and language-agnostic
- No more confusing "why C-only?" questions

### 2. **Better Code Organization**
- Backend-specific logic lives in backends
- Frontend logic applies to all backends
- Single Responsibility Principle

### 3. **Reduced Code Size**
- 777 LOC → 600 LOC (-23%)
- Remove 4 low-value rules
- Keep all valuable code quality checks
- More maintainable

### 4. **Improved User Experience**
- C/C++ users get memory safety warnings
- All users get comprehensive Python code quality checks
- Catches unreachable code and unused variables early
- No false positives from irrelevant checks

### 5. **Extensibility**
- Easy to add Rust-specific checks later
- Easy to add more Python validation rules
- Clear pattern for backend-specific validation

---

## 🚦 Decision Points

### Q1: Should we keep all 9 PythonConstraintChecker rules?

**Recommendation**: Yes
- TS001-TS004: High value for type safety
- SA001: Detects dead code (important for code quality)
- SA002: Detects unused variables (important for code quality)
- SA003: Critical for uninitialized detection
- SA005: Suggests better type annotations (improves API design) ✨ NEW
- CC004: Useful complexity warning

**Value**: Comprehensive Python code quality validation helps catch bugs early and improves generated code quality across all backends

**Bonus**: SA005 reuses immutability analysis (zero overhead), and backends like C++ can now use immutability results for const-correctness

### Q2: Should C++ share the same MemorySafetyChecker?

**Recommendation**: Yes, but with minor differences
- Same 4 core checks (MS001-MS004)
- C++ could have additional RAII/smart pointer checks later
- Start with shared implementation, specialize if needed

**Implementation**:
```python
# Option 1: Shared with flags
class MemorySafetyChecker:
    def __init__(self, language: str = "c"):
        self.language = language  # "c" or "cpp"

# Option 2: Inheritance
class CppMemorySafetyChecker(MemorySafetyChecker):
    def _check_smart_pointers(self, tree: ast.AST) -> None:
        # C++ specific
```

### Q3: What about other backends later (Zig, Nim, etc.)?

**Pattern established**:
- Manual memory management → Implement MemorySafetyChecker
- Garbage collected → No memory safety checker needed
- Backend adds `validate_for_target()` if needed

---

## 📝 Example Integration

### Before (Current)
```python
# pipeline.py
if self.config.target_language == "c":  # Confusing!
    constraint_report = self.constraint_checker.check_code(source_code)
```

### After (Proposed)
```python
# pipeline.py - validation phase

# 1. Universal Python constraints (all backends)
python_checker = PythonConstraintChecker()
violations = python_checker.check_code(source_code)
for v in violations:
    if v.severity == "error":
        result.errors.append(v.message)
    else:
        result.warnings.append(v.message)

# 2. Backend-specific validation (if supported)
backend_warnings = self.backend.validate_for_target(source_code)
result.warnings.extend(backend_warnings)
```

### Backend Implementation
```python
# backends/c/backend.py
class CBackend(LanguageBackend):
    def validate_for_target(self, source_code: str) -> list[str]:
        checker = MemorySafetyChecker(language="c")
        warnings = checker.check_code(source_code)
        return [f"[Memory Safety] {w.message}" for w in warnings]

# backends/rust/backend.py
class RustBackend(LanguageBackend):
    def validate_for_target(self, source_code: str) -> list[str]:
        # Rust compiler handles memory safety
        return []
```

---

## 🎯 Success Criteria

1. ✅ All 855 tests pass
2. ✅ C/C++ backends show memory safety warnings
3. ✅ All backends show Python constraint violations (type safety + code quality)
4. ✅ Unreachable code and unused variables are detected
5. ✅ No false positives from irrelevant checks
6. ✅ Code size reduced by ~23%
7. ✅ Architecture is clearer and more maintainable

---

## 🚀 Recommendation

**PROCEED with the split**. This is excellent architecture:

1. **Philosophically sound**: Backend concerns in backends, universal concerns in frontend
2. **Practically valuable**: Real safety and code quality checks users will benefit from
3. **Clean implementation**: Clear boundaries, ~5 hours work
4. **Measurable improvement**: -23% LOC, comprehensive code quality checks, better UX, clearer code

**Approved Rule Set**:
- MemorySafetyChecker: 4 rules (MS001-004) for C/C++
- PythonConstraintChecker: 9 rules (TS001-004, SA001-003, SA005, CC004) for all backends
- ImmutabilityAnalyzer: ✅ Moved to frontend (shared analysis, Rust+C++ can use)
- Comprehensive coverage: type safety + code quality + memory safety + immutability

**Completed**:
1. ✅ Rule selection approved (4 memory + 4 type + 5 static)
2. ✅ ImmutabilityAnalyzer moved to frontend
3. ✅ Pipeline integration complete
4. ✅ All 855 tests passing

**Next Steps**:
1. Implement Phase 1 (create MemorySafetyChecker + PythonConstraintChecker)
2. Update Rust backend to use pipeline immutability results
3. Test thoroughly
4. Deploy and update docs

**Alternative**: If you want to start smaller, implement just MemorySafetyChecker first (C/C++ only), defer PythonConstraintChecker to later.
