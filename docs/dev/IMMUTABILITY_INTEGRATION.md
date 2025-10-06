# Immutability Analyzer Integration Proposal

**Current**: `src/mgen/analysis/immutability.py` (252 LOC) - Used only by Rust backend
**Proposed**: Integrate into constraint split architecture

---

## Current State

### What It Does
Analyzes Python code to determine parameter mutability:
- **IMMUTABLE**: Type guarantees immutability (tuple, frozenset, str, Final)
- **READ_ONLY**: Never modified in function body
- **MUTABLE**: Modified in function body (append, subscript assignment, etc.)
- **UNKNOWN**: Cannot determine

### Current Usage
```python
# Rust backend (converter.py)
self.immutability_analyzer = ImmutabilityAnalyzer()
self.mutability_info = self.immutability_analyzer.analyze_module(tree)

# Later used to decide: &T vs &mut T
if param_mutability == MutabilityClass.READ_ONLY:
    return f"&{rust_type}"  # Immutable reference
else:
    return f"&mut {rust_type}"  # Mutable reference
```

**Problem**: Orphaned in `src/mgen/analysis/`, only Rust uses it, but C++ could benefit too

---

## Why It's Python-Specific

**Analyzes Python Patterns**:
1. Mutating method calls: `list.append()`, `dict.update()`, etc.
2. Subscript assignment: `param[i] = value`
3. Augmented assignment: `param[i] += value`
4. Type annotations: `tuple[int]`, `Sequence[str]`, `typing.Final`

**Backend-Agnostic Results**: Each backend interprets results differently
- Rust: `&T` vs `&mut T`
- C++: `const T&` vs `T&`
- C: Could use `const` qualifiers
- Others: Less applicable

---

## Integration Options

### Option 1: Add as PythonConstraintChecker Rule ❌
**Approach**: SA005 - Parameter Mutability Warning

```python
class PythonConstraintChecker:
    def _check_parameter_mutability(self, tree: ast.AST) -> None:
        """Warn if parameters could be more restrictive."""
        analyzer = ImmutabilityAnalyzer()
        results = analyzer.analyze_module(tree)

        for func_name, params in results.items():
            for param, mutability in params.items():
                if mutability == MutabilityClass.READ_ONLY:
                    self.violations.append(
                        PythonConstraintViolation(
                            category=ConstraintCategory.CODE_QUALITY,
                            rule_id="SA005",
                            message=f"Parameter '{param}' in '{func_name}' is never modified, "
                                    f"consider using immutable type annotation",
                            severity="info"
                        )
                    )
```

**Pros**:
- Gives users helpful warnings
- Encourages better type annotations
- Natural fit with other SA* rules

**Cons**:
- **Backends still need the analysis results** (not just warnings)
- Rust needs mutability info to generate correct code
- Would duplicate analysis (once for warnings, once for backends)
- Mixing validation with analysis

### Option 2: Move to Frontend Analysis ✅ RECOMMENDED
**Approach**: Move to `src/mgen/frontend/immutability_analyzer.py`, run in analysis phase

```python
# pipeline.py - Analysis phase
if FRONTEND_AVAILABLE and self.config.enable_advanced_analysis:
    # ... existing analyzers ...

    # Immutability analysis (for backends that need it)
    from .frontend.immutability_analyzer import ImmutabilityAnalyzer
    immutability_analyzer = ImmutabilityAnalyzer()
    immutability_results = immutability_analyzer.analyze_module(ast_root)
    advanced_analysis["immutability"] = immutability_results
```

**Backends access results**:
```python
# backends/rust/converter.py
def convert(self, source_code: str) -> str:
    # Get immutability analysis from pipeline
    if hasattr(self, 'pipeline_analysis'):
        self.mutability_info = self.pipeline_analysis.get('immutability', {})
    else:
        # Fallback: run analysis locally
        self.mutability_info = ImmutabilityAnalyzer().analyze_module(tree)
```

**Pros**:
- Centralized analysis (run once, used by multiple backends)
- Clear separation: analysis in frontend, consumption in backends
- C++ backend can easily adopt for const-correctness
- Fits existing advanced_analysis pattern
- No duplication

**Cons**:
- Slight refactoring needed in Rust backend
- Need to pass analysis results to backends

### Option 3: Hybrid Approach ✅ BEST OF BOTH
**Approach**: Move to frontend + optionally add constraint rule

1. **Move to `src/mgen/frontend/immutability_analyzer.py`**
   - Run in analysis phase
   - Results available to all backends

2. **Optionally add SA005 to PythonConstraintChecker**
   - Reuse immutability results from analysis phase
   - Provide helpful user warnings
   - No duplicate analysis

```python
# PythonConstraintChecker can optionally use results
class PythonConstraintChecker:
    def __init__(self, immutability_results: Optional[dict] = None):
        self.immutability_results = immutability_results or {}

    def _check_parameter_mutability(self, tree: ast.AST) -> None:
        """Warn about parameters that could be more restrictive."""
        if not self.immutability_results:
            return  # Skip if no analysis available

        for func_name, params in self.immutability_results.items():
            for param, mutability in params.items():
                if mutability == MutabilityClass.READ_ONLY:
                    # Suggest better annotation
                    self.violations.append(...)
```

---

## Recommended Implementation

### Phase 1: Move to Frontend (Required)

1. **Move file**:
   ```bash
   mv src/mgen/analysis/immutability.py src/mgen/frontend/immutability_analyzer.py
   ```

2. **Update pipeline** (`src/mgen/pipeline.py`):
   ```python
   # _analysis_phase method
   from .frontend.immutability_analyzer import ImmutabilityAnalyzer

   immutability_analyzer = ImmutabilityAnalyzer()
   immutability_results = immutability_analyzer.analyze_module(ast_root)
   advanced_analysis["immutability"] = immutability_results
   ```

3. **Update Rust backend** (`src/mgen/backends/rust/converter.py`):
   ```python
   # Remove local instantiation
   # self.immutability_analyzer = ImmutabilityAnalyzer()

   # Get from pipeline analysis instead
   def convert(self, source_code: str) -> str:
       tree = ast.parse(source_code)

       # Get immutability from pipeline if available
       if 'immutability' in self.pipeline_analysis:
           self.mutability_info = self.pipeline_analysis['immutability']
       else:
           # Fallback for standalone usage
           from ...frontend.immutability_analyzer import ImmutabilityAnalyzer
           self.mutability_info = ImmutabilityAnalyzer().analyze_module(tree)
   ```

4. **Enable C++ const-correctness** (Optional, future):
   ```python
   # backends/cpp/converter.py
   def _convert_parameter(self, param: ast.arg) -> str:
       param_type = self._get_type(param)

       # Check immutability
       mutability = self.pipeline_analysis.get('immutability', {}).get(
           self.current_function, {}
       ).get(param.arg, MutabilityClass.UNKNOWN)

       if mutability in [MutabilityClass.IMMUTABLE, MutabilityClass.READ_ONLY]:
           return f"const {param_type}& {param.arg}"
       else:
           return f"{param_type}& {param.arg}"
   ```

### Phase 2: Add Constraint Rule (Optional)

Add SA005 to PythonConstraintChecker if we want user warnings:

```python
# SA005: Parameter Mutability
- Suggests using tuple instead of list for read-only params
- Suggests using Sequence[T] instead of list[T]
- Info-level warnings (not errors)
```

---

## Benefits

### 1. **Better Architecture**
- Analysis in frontend (where it belongs)
- Multiple backends can use results
- Clear separation of concerns

### 2. **Enable C++ const-correctness**
- C++ backend can generate `const T&` for read-only params
- Better generated code quality
- Type safety improvements

### 3. **Optional User Warnings**
- If we add SA005, users get helpful suggestions
- "Use tuple instead of list for read-only data"
- Improves Python code quality

### 4. **No Duplication**
- Analysis runs once in pipeline
- Results shared across backends
- Constraint checker can optionally reuse results

---

## Migration Plan

### Step 1: Move to Frontend (30 min)
1. Move file: `analysis/immutability.py` → `frontend/immutability_analyzer.py`
2. Update imports in Rust backend
3. Update `__init__.py` exports

### Step 2: Integrate with Pipeline (1 hour)
1. Add to analysis phase (like other analyzers)
2. Store results in `advanced_analysis["immutability"]`
3. Make available to backends via pipeline_analysis

### Step 3: Update Rust Backend (30 min)
1. Remove local ImmutabilityAnalyzer instantiation
2. Get results from pipeline_analysis
3. Keep fallback for standalone usage
4. Test thoroughly

### Step 4: Enable C++ (Optional, 1 hour)
1. Add const-correctness logic to C++ converter
2. Use immutability results for parameter types
3. Test with examples

### Step 5: Add SA005 Rule (Optional, 1 hour)
1. Add to PythonConstraintChecker
2. Reuse immutability results from pipeline
3. Generate helpful warnings
4. Add tests

**Total Effort**: 2-3 hours (required), +2 hours (optional enhancements)

---

## Decision

**Recommendation**: **Option 3 (Hybrid)**

1. ✅ **Move to frontend** (required) - Better architecture
2. ✅ **Share analysis** - Multiple backends can use
3. ⚠️ **Add SA005 rule** (optional) - Nice-to-have user warnings
4. ✅ **Enable C++ const** (future) - Unlock new optimization

**Why**:
- ImmutabilityAnalyzer IS Python-specific analysis ✅
- Currently orphaned in wrong location ✅
- Backends need results (not just warnings) ✅
- C++ backend would benefit from const-correctness ✅
- Fits naturally with other frontend analyzers ✅

**Next Steps**:
1. Approve approach
2. Execute Step 1-3 (move + integrate + update Rust)
3. Decide on Step 4-5 (C++ const, SA005 warnings)
4. Test and document

---

## Example: SA005 Warnings (If Implemented)

```python
# User code:
def process_items(items: list[int]) -> int:
    total = 0
    for item in items:
        total += item
    return total

# SA005 Warning:
# Parameter 'items' is never modified, consider using:
#   - tuple[int] (immutable)
#   - Sequence[int] (read-only abstract type)
# This allows callers to pass any sequence type safely.

# Better code:
def process_items(items: Sequence[int]) -> int:
    total = 0
    for item in items:
        total += item
    return total
```

**User benefit**: Learn better type annotation practices, write more robust code
