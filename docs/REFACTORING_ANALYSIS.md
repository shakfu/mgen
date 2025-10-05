# Complex Functions Refactoring Analysis

## Executive Summary

Analysis of 58 functions with McCabe complexity >15 reveals significant refactoring opportunities using visitor and strategy design patterns. The codebase already successfully implements visitor pattern in `static_ir.py`, providing a proven template for refactoring complex converter functions.

**Key Findings**:
- **Visitor pattern**: Applicable to 12 complex statement/expression conversion functions
- **Strategy pattern**: Applicable to 8 complex container operation functions
- **Estimated effort**: 5-7 days to refactor top 20 functions
- **Expected benefits**: 40-60% complexity reduction, improved maintainability

## Top Complex Functions Analysis

### 1. `_convert_function` (Haskell) - Complexity 69
**Location**: `src/mgen/backends/haskell/converter.py:375`

**Current Issues**:
- Monolithic function with 7 distinct responsibilities
- 300+ lines handling multiple concerns
- Deep nesting (4-5 levels in places)
- Difficult to test individual behaviors

**Responsibilities**:
1. Parameter mutation detection (lines 379-391)
2. Main function special handling (lines 394-484)
3. Pre-scanning for conditional assignments (lines 399-429)
4. Do-notation generation (lines 431-480)
5. Type inference (lines 486-507)
6. Statement conversion (lines 527-659)
7. Duplicate binding elimination (lines 592-643)

**Refactoring Recommendation**: ✅ **Visitor Pattern**

**Proposed Solution**:
```python
class HaskellStatementVisitor(ABC):
    """Visitor for converting Python statements to Haskell."""

    @abstractmethod
    def visit_assign(self, node: ast.Assign) -> str: pass

    @abstractmethod
    def visit_if(self, node: ast.If) -> str: pass

    @abstractmethod
    def visit_return(self, node: ast.Return) -> str: pass

    # ... other statement types

class MainFunctionVisitor(HaskellStatementVisitor):
    """Specialized visitor for main() function with IO do-notation."""

    def visit_assign(self, node: ast.Assign) -> str:
        # Convert to 'let' binding in do-notation
        return f"let {self._convert_binding(node)}"

    def visit_if(self, node: ast.If) -> str:
        # Handle conditional assignments vs regular if
        if self._is_conditional_assignment(node):
            return self._convert_conditional_binding(node)
        return self._convert_io_if(node)

class PureFunctionVisitor(HaskellStatementVisitor):
    """Visitor for pure functions (non-main)."""

    def visit_assign(self, node: ast.Assign) -> str:
        # Convert to where-clause or let-expression
        return self._convert_pure_binding(node)
```

**Benefits**:
- Separate main() vs pure function logic
- Each statement type isolated
- Testable in isolation
- Complexity reduced to ~15-20 per visitor method

**Estimated Effort**: 2 days

---

### 2. `translate_container_operation` (STC Translator) - Complexity 66
**Location**: `src/mgen/backends/c/ext/stc/translator.py:136`

**Current Issues**:
- 150-line if/elif chain
- 30+ container method translations
- Three container types mixed (list, dict, set)
- No separation of concerns

**Refactoring Recommendation**: ✅ **Strategy Pattern**

**Proposed Solution**:
```python
class ContainerOperationStrategy(ABC):
    """Strategy for translating container operations."""

    @abstractmethod
    def translate(self, method: str, obj_name: str, args: list) -> Optional[str]:
        """Translate a container method call."""
        pass

class ListOperationStrategy(ContainerOperationStrategy):
    """Strategy for Python list operations."""

    def translate(self, method: str, obj_name: str, args: list) -> Optional[str]:
        operations = {
            'append': lambda: f"{obj_name}_push(&{obj_name}, {args[0]})",
            'pop': lambda: f"{obj_name}_pop(&{obj_name})" if not args
                          else f"{obj_name}_erase_at(&{obj_name}, {args[0]})",
            'insert': lambda: f"{obj_name}_insert_at(&{obj_name}, {args[0]}, {args[1]})",
            'remove': lambda: f"{obj_name}_erase_val(&{obj_name}, {args[0]})",
            'clear': lambda: f"{obj_name}_clear(&{obj_name})",
            # ... more operations
        }
        return operations.get(method, lambda: None)()

class DictOperationStrategy(ContainerOperationStrategy):
    """Strategy for Python dict operations."""

    def translate(self, method: str, obj_name: str, args: list) -> Optional[str]:
        operations = {
            'get': lambda: self._translate_get(obj_name, args),
            'keys': lambda: f"{obj_name}_keys({obj_name})",
            'values': lambda: f"{obj_name}_values({obj_name})",
            'items': lambda: f"{obj_name}_items({obj_name})",
            # ... more operations
        }
        return operations.get(method, lambda: None)()

class SetOperationStrategy(ContainerOperationStrategy):
    """Strategy for Python set operations."""

    def translate(self, method: str, obj_name: str, args: list) -> Optional[str]:
        operations = {
            'add': lambda: f"{obj_name}_insert(&{obj_name}, {args[0]})",
            'discard': lambda: f"{obj_name}_erase(&{obj_name}, {args[0]})",
            'union': lambda: f"{obj_name}_union(&{obj_name}, &{args[0]})",
            # ... more operations
        }
        return operations.get(method, lambda: None)()

class ContainerTranslator:
    """Main translator using strategy pattern."""

    def __init__(self):
        self.strategies = {
            'list': ListOperationStrategy(),
            'dict': DictOperationStrategy(),
            'set': SetOperationStrategy(),
        }

    def translate_operation(self, container_type: str, method: str,
                           obj_name: str, args: list) -> Optional[str]:
        strategy = self.strategies.get(container_type)
        if strategy:
            return strategy.translate(method, obj_name, args)
        return None
```

**Benefits**:
- Separate strategy per container type
- Operations defined as dictionary mappings
- Easy to add new container types
- Testable in isolation
- Complexity reduced to ~10 per strategy

**Estimated Effort**: 1.5 days

---

### 3. `_infer_type_from_value` (Multiple Backends) - Complexity 33-45
**Locations**:
- `src/mgen/backends/base_converter.py:855`
- `src/mgen/backends/cpp/converter.py` (similar pattern)
- `src/mgen/backends/go/converter.py` (similar pattern)

**Current Issues**:
- Deep nested if/elif chains
- Duplicated across backends
- Limited extensibility for new types

**Refactoring Recommendation**: ✅ **Strategy Pattern + Chain of Responsibility**

**Proposed Solution**:
```python
class TypeInferenceStrategy(ABC):
    """Strategy for inferring types from AST values."""

    @abstractmethod
    def can_infer(self, value: ast.expr) -> bool:
        """Check if this strategy can infer the type."""
        pass

    @abstractmethod
    def infer(self, value: ast.expr) -> Optional[str]:
        """Infer the type from the value."""
        pass

class ConstantTypeStrategy(TypeInferenceStrategy):
    """Infer types from constant values."""

    def can_infer(self, value: ast.expr) -> bool:
        return isinstance(value, ast.Constant)

    def infer(self, value: ast.expr) -> Optional[str]:
        if isinstance(value.value, bool):
            return "bool"
        elif isinstance(value.value, int):
            return "int"
        elif isinstance(value.value, float):
            return "float"
        elif isinstance(value.value, str):
            return "str"
        return None

class ContainerLiteralStrategy(TypeInferenceStrategy):
    """Infer types from container literals."""

    def can_infer(self, value: ast.expr) -> bool:
        return isinstance(value, (ast.List, ast.Dict, ast.Set))

    def infer(self, value: ast.expr) -> Optional[str]:
        if isinstance(value, ast.List):
            return "list"
        elif isinstance(value, ast.Dict):
            return "dict"
        elif isinstance(value, ast.Set):
            return "set"
        return None

class ConstructorCallStrategy(TypeInferenceStrategy):
    """Infer types from constructor calls."""

    def __init__(self, classes: set[str]):
        self.classes = classes

    def can_infer(self, value: ast.expr) -> bool:
        return (isinstance(value, ast.Call) and
                isinstance(value.func, ast.Name))

    def infer(self, value: ast.expr) -> Optional[str]:
        if isinstance(value.func, ast.Name):
            func_name = value.func.id
            if func_name in self.classes:
                return func_name
        return None

class TypeInferenceChain:
    """Chain of responsibility for type inference."""

    def __init__(self, strategies: list[TypeInferenceStrategy]):
        self.strategies = strategies

    def infer_type(self, value: ast.expr) -> str:
        for strategy in self.strategies:
            if strategy.can_infer(value):
                result = strategy.infer(value)
                if result:
                    return result
        return "Any"  # Default
```

**Benefits**:
- Extensible type inference system
- Easy to add new type inference rules
- Reusable across backends
- Complexity reduced to ~5-10 per strategy

**Estimated Effort**: 1 day

---

### 4. `_convert_for_statement` (OCaml/Haskell) - Complexity 40
**Locations**:
- `src/mgen/backends/ocaml/converter.py`
- `src/mgen/backends/haskell/converter.py`

**Current Issues**:
- Handles multiple for-loop patterns
- Range iteration vs container iteration
- Nested loop detection
- Mutation detection

**Refactoring Recommendation**: ✅ **Strategy Pattern**

**Proposed Solution**:
```python
class ForLoopStrategy(ABC):
    """Strategy for converting different for-loop patterns."""

    @abstractmethod
    def can_handle(self, node: ast.For) -> bool: pass

    @abstractmethod
    def convert(self, node: ast.For) -> str: pass

class RangeLoopStrategy(ForLoopStrategy):
    """Convert range-based for loops."""

    def can_handle(self, node: ast.For) -> bool:
        return (isinstance(node.iter, ast.Call) and
                isinstance(node.iter.func, ast.Name) and
                node.iter.func.id == 'range')

    def convert(self, node: ast.For) -> str:
        # Convert to indexed loop
        return self._convert_range_loop(node)

class ContainerLoopStrategy(ForLoopStrategy):
    """Convert container iteration loops."""

    def can_handle(self, node: ast.For) -> bool:
        return isinstance(node.iter, ast.Name)

    def convert(self, node: ast.For) -> str:
        # Convert to foreach/map
        return self._convert_foreach_loop(node)

class ForLoopConverter:
    """Main for-loop converter using strategies."""

    def __init__(self):
        self.strategies = [
            RangeLoopStrategy(),
            ContainerLoopStrategy(),
            # Add more strategies
        ]

    def convert(self, node: ast.For) -> str:
        for strategy in self.strategies:
            if strategy.can_handle(node):
                return strategy.convert(node)
        raise UnsupportedFeatureError("Unsupported for-loop pattern")
```

**Benefits**:
- Each loop pattern isolated
- Easy to add new patterns
- Testable separately
- Complexity reduced to ~10-15 per strategy

**Estimated Effort**: 1 day

---

## Pattern Application Summary

### Visitor Pattern - Best For:
1. ✅ Statement conversion functions (if/while/for/assign/return)
2. ✅ Expression conversion functions (binop/call/subscript/attribute)
3. ✅ AST traversal and transformation

**Candidates** (12 functions):
- `_convert_function` (Haskell) - 69 complexity → ~20
- `_convert_statement` (multiple backends) - 25-35 → ~10
- `_convert_expression` (multiple backends) - 20-30 → ~8
- Statement-specific converters (if/for/while) - 15-40 → ~12

### Strategy Pattern - Best For:
1. ✅ Container operations (list/dict/set method translations)
2. ✅ Type inference (value-based type detection)
3. ✅ Loop pattern conversion (range/foreach/comprehension)
4. ✅ Backend-specific formatting

**Candidates** (8 functions):
- `translate_container_operation` - 66 complexity → ~10
- `_infer_type_from_value` - 33-45 → ~8
- `_convert_for_statement` - 40 → ~12
- `_analyze_dict_key_types` - 32 → ~10

### Combined Patterns:
Some functions benefit from **both patterns**:

```python
# Visitor for statement traversal + Strategy for conversion logic
class StatementConverter:
    def __init__(self):
        self.visitor = StatementVisitor()
        self.strategies = {
            'assign': AssignmentStrategy(),
            'if': ConditionalStrategy(),
            'for': LoopStrategy(),
        }

    def convert(self, stmt: ast.stmt) -> str:
        stmt_type = type(stmt).__name__.lower()
        strategy = self.strategies.get(stmt_type)
        if strategy:
            return self.visitor.visit(stmt, strategy)
        raise UnsupportedFeatureError(f"No strategy for {stmt_type}")
```

---

## Implementation Roadmap

### Phase 1: High-Impact Refactoring (3 days)
**Priority**: Top 3 complex functions

1. **Day 1**: Refactor `translate_container_operation` (complexity 66)
   - Implement ContainerOperationStrategy pattern
   - Create ListOperationStrategy, DictOperationStrategy, SetOperationStrategy
   - Update tests (existing tests should pass unchanged)

2. **Day 2-3**: Refactor `_convert_function` (Haskell, complexity 69)
   - Implement HaskellStatementVisitor
   - Create MainFunctionVisitor and PureFunctionVisitor
   - Extract mutation detection, type inference to separate methods
   - Verify all 7 Haskell benchmarks still pass

### Phase 2: Type Inference Refactoring (1.5 days)
**Priority**: Reusable across backends

3. **Day 4**: Refactor `_infer_type_from_value` (complexity 33-45)
   - Implement TypeInferenceStrategy pattern
   - Create reusable strategies in base_converter
   - Update all backends to use shared strategies
   - Reduce code duplication ~30%

### Phase 3: Loop Conversion Refactoring (1.5 days) ✅ **COMPLETED**
**Priority**: OCaml and Haskell backends

4. **Day 5**: Refactor `_convert_for_statement` (complexity 40)
   - Implement ForLoopStrategy pattern
   - Create RangeLoopStrategy, ContainerLoopStrategy
   - Apply to OCaml and Haskell converters

**Completion Status**: ✅ Completed on 2025-10-05

**Results**:
- Created `loop_conversion_strategies.py` with ForLoopStrategy base class and ForLoopConverter
- Implemented Haskell strategies: HaskellNestedListBuildingStrategy, HaskellListAppendStrategy, HaskellAccumulationStrategy, HaskellAssignmentInMainStrategy
- Implemented OCaml strategies: OCamlSimpleAssignmentStrategy, OCamlAccumulationStrategy, OCamlGeneralLoopStrategy
- Refactored Haskell `_convert_for_statement`: 251 lines → ~30 lines (88% reduction)
- Refactored OCaml `_convert_for_statement`: 84 lines → ~20 lines (76% reduction)
- **All 870 tests passing** (up from 821 - project growth)
- Type-safe with proper mypy annotations
- Complexity reduction: Haskell 40-50 → ~8-10, OCaml 15-20 → ~5-8

**Files Created**:
- `src/mgen/backends/loop_conversion_strategies.py` (110 lines)
- `src/mgen/backends/haskell/loop_strategies.py` (262 lines)
- `src/mgen/backends/ocaml/loop_strategies.py` (201 lines)

**Benefits Achieved**:
- Strategies handle 7+ common loop patterns (nested lists, append, accumulation, assignment)
- Fallback mechanism for complex patterns (triple-nested matmul, word count)
- Lazy initialization prevents circular imports
- Shared LoopContext provides backend-specific helpers while keeping strategies language-agnostic
- Easy to extend with new strategies for additional patterns

### Phase 4: Expression Conversion (1 day)
**Priority**: Medium complexity, high duplication

5. **Day 6**: Refactor expression conversion functions
   - Extract common expression conversion to visitor
   - Reduce duplication across backends

### Phase 5: Testing & Documentation (0.5 days)
6. **Day 7**: Testing and documentation
   - Verify all 821 tests pass
   - Update architecture documentation
   - Add design pattern examples to CLAUDE.md

---

## Expected Benefits

### Complexity Reduction
- **Top 3 functions**: 69, 66, 45 → 20, 10, 8 (75% reduction)
- **Overall**: 58 complex functions → ~35 (40% reduction)
- **Average complexity**: 22 → 12 (45% reduction)

### Code Quality Improvements
1. **Maintainability**: Each concern isolated in separate class
2. **Testability**: Strategies and visitors testable in isolation
3. **Extensibility**: Easy to add new statement/expression types
4. **Reusability**: Shared strategies across backends (30% less code)

### Developer Experience
- New backend developers understand patterns faster
- Easier to locate and fix bugs (smaller functions)
- Clearer separation of concerns
- Better alignment with existing visitor pattern in static_ir.py

---

## Risk Assessment

### Low Risk ✅
- **Pattern familiarity**: Visitor already successfully used in static_ir.py
- **Test coverage**: 821 tests verify correctness after refactoring
- **Incremental approach**: One function at a time, tests must pass

### Medium Risk ⚠️
- **Regression potential**: Complex functions have many edge cases
  - **Mitigation**: Comprehensive test suite, gradual refactoring
- **Performance impact**: Additional method calls from indirection
  - **Mitigation**: Profile before/after, optimize hot paths if needed

### High Risk ❌
- None identified

---

## Alternatives Considered

### 1. Extract Method Refactoring (Simpler)
**Pros**: Less architectural change, faster implementation
**Cons**: Doesn't address fundamental design issues, still complex

### 2. Template Method Pattern
**Pros**: Good for backend-specific variations
**Cons**: Less flexible than strategy, harder to add new cases

### 3. Command Pattern
**Pros**: Good for operation queueing/undo
**Cons**: Overkill for this use case, adds unnecessary complexity

**Decision**: Visitor + Strategy patterns chosen because:
- Already proven in codebase (static_ir.py)
- Maximum flexibility for adding new features
- Clear separation of concerns
- Best fit for AST traversal and conversion

---

## Success Metrics

### Quantitative
- ✅ Reduce functions >15 complexity from 58 to <40
- ✅ Reduce average complexity from 22 to <15
- ✅ Maintain 100% test pass rate (821/821 tests)
- ✅ Reduce code duplication by >20%

### Qualitative
- ✅ New contributors understand architecture faster
- ✅ Bug fixes require changes to fewer files
- ✅ Adding new statement types takes <1 hour vs 3-4 hours

---

## Conclusion

**Recommendation**: Proceed with visitor/strategy refactoring

The analysis confirms that visitor and strategy patterns are highly applicable to the complex converter functions. The codebase already demonstrates successful visitor pattern usage in `static_ir.py`, providing a proven foundation.

**Key Advantages**:
1. 75% complexity reduction in top 3 functions
2. Improved maintainability and testability
3. Better alignment with existing architecture
4. Low risk due to comprehensive test coverage

**Implementation**: Follow 7-day roadmap, prioritizing highest-impact functions first (translate_container_operation, _convert_function, _infer_type_from_value).

All 821 tests must pass after each refactoring phase - **zero tolerance for regressions**.
