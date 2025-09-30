"""Static Constraint Checking for Python-to-C Conversion.

This module implements comprehensive constraint checking to ensure
that Python code can be safely and correctly converted to C code.
"""

import ast
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from ..common import log
from .ast_analyzer import TypeInfo
from .type_inference import TypeInferenceEngine


class ConstraintSeverity(Enum):
    """Severity levels for constraint violations."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ConstraintCategory(Enum):
    """Categories of constraints."""

    MEMORY_SAFETY = "memory_safety"
    TYPE_SAFETY = "type_safety"
    STATIC_ANALYSIS = "static_analysis"
    C_COMPATIBILITY = "c_compatibility"
    PERFORMANCE = "performance"
    CORRECTNESS = "correctness"


@dataclass
class ConstraintViolation:
    """Represents a constraint violation found during analysis."""

    severity: ConstraintSeverity
    category: ConstraintCategory
    rule_id: str
    message: str
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    source_code: Optional[str] = None
    suggestion: Optional[str] = None
    auto_fixable: bool = False


@dataclass
class ConstraintReport:
    """Complete constraint checking report."""

    violations: List[ConstraintViolation] = field(default_factory=list)
    passed_checks: List[str] = field(default_factory=list)
    conversion_safe: bool = True
    confidence_score: float = 1.0

    def add_violation(self, violation: ConstraintViolation) -> None:
        """Add a violation to the report."""
        self.violations.append(violation)
        if violation.severity in [ConstraintSeverity.ERROR, ConstraintSeverity.CRITICAL]:
            self.conversion_safe = False

    def get_violations_by_severity(self, severity: ConstraintSeverity) -> List[ConstraintViolation]:
        """Get all violations of a specific severity."""
        return [v for v in self.violations if v.severity == severity]

    def get_violations_by_category(self, category: ConstraintCategory) -> List[ConstraintViolation]:
        """Get all violations of a specific category."""
        return [v for v in self.violations if v.category == category]


class StaticConstraintChecker:
    """Comprehensive static constraint checker for Python-to-C conversion."""

    def __init__(self) -> None:
        self.log = log.config(self.__class__.__name__)
        self.report = ConstraintReport()
        self.type_engine = TypeInferenceEngine()
        self.current_function: Optional[str] = None
        self.variable_scopes: Dict[str, Dict[str, TypeInfo]] = {}

        # Constraint rules registry
        self.rules = {
            # Memory safety rules
            "MS001": self._check_buffer_overflow_potential,
            "MS002": self._check_null_pointer_dereference,
            "MS003": self._check_memory_leak_potential,
            "MS004": self._check_dangling_pointer_risk,
            # Type safety rules
            "TS001": self._check_type_consistency,
            "TS002": self._check_implicit_conversions,
            "TS003": self._check_division_by_zero,
            "TS004": self._check_integer_overflow,
            # Static analysis rules
            "SA001": self._check_unreachable_code,
            "SA002": self._check_unused_variables,
            "SA003": self._check_uninitialized_variables,
            "SA004": self._check_infinite_loops,
            # C compatibility rules
            "CC001": self._check_unsupported_features,
            "CC002": self._check_name_conflicts,
            "CC003": self._check_reserved_keywords,
            "CC004": self._check_function_complexity,
            # Performance rules
            "PF001": self._check_inefficient_patterns,
            "PF002": self._check_repeated_computations,
            "PF003": self._check_memory_allocation_patterns,
            # Correctness rules
            "CR001": self._check_return_path_coverage,
            "CR002": self._check_parameter_validation,
            "CR003": self._check_bounds_checking,
        }

    def check_code(self, source_code: str) -> ConstraintReport:
        """Check Python source code for conversion constraints."""
        try:
            tree = ast.parse(source_code)
            self._analyze_tree(tree)
            self._run_all_checks(tree)
            self._calculate_confidence_score()
            return self.report
        except SyntaxError as e:
            self.report.add_violation(
                ConstraintViolation(
                    severity=ConstraintSeverity.CRITICAL,
                    category=ConstraintCategory.STATIC_ANALYSIS,
                    rule_id="PARSE001",
                    message=f"Syntax error: {e}",
                    line_number=e.lineno,
                    column_number=e.offset,
                )
            )
            return self.report

    def _analyze_tree(self, tree: ast.AST) -> None:
        """Perform initial analysis of the AST."""
        # Build variable scope information
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                self.variable_scopes[node.name] = {}
                for arg in node.args.args:
                    if arg.annotation:
                        type_info = self._extract_type_info(arg.annotation)
                        self.variable_scopes[node.name][arg.arg] = type_info

    def _run_all_checks(self, tree: ast.AST) -> None:
        """Run all constraint checking rules."""
        for rule_id, rule_func in self.rules.items():
            try:
                rule_func(tree)
                self.report.passed_checks.append(rule_id)
            except Exception as e:
                self.report.add_violation(
                    ConstraintViolation(
                        severity=ConstraintSeverity.ERROR,
                        category=ConstraintCategory.STATIC_ANALYSIS,
                        rule_id=rule_id,
                        message=f"Internal error in rule {rule_id}: {e}",
                    )
                )

    # Memory Safety Rules

    def _check_buffer_overflow_potential(self, tree: ast.AST) -> None:
        """Check for potential buffer overflow conditions."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Subscript):
                # Skip type annotations - they are not actual array access
                if self._is_type_annotation(node):
                    continue

                # Check array access patterns
                if isinstance(node.slice, ast.Name):
                    # Variable index - potential risk
                    self.report.add_violation(
                        ConstraintViolation(
                            severity=ConstraintSeverity.WARNING,
                            category=ConstraintCategory.MEMORY_SAFETY,
                            rule_id="MS001",
                            message="Array access with variable index - ensure bounds checking",
                            line_number=node.lineno,
                            suggestion="Add explicit bounds checking before array access",
                        )
                    )

    def _is_type_annotation(self, node: ast.Subscript) -> bool:
        """Check if a subscript node represents a type annotation rather than array access."""
        # Common type annotation patterns: list[int], dict[str, int], etc.
        if isinstance(node.value, ast.Name):
            type_names = {
                "list",
                "dict",
                "set",
                "tuple",
                "List",
                "Dict",
                "Set",
                "Tuple",
                "Optional",
                "Union",
                "Callable",
                "Type",
                "ClassVar",
                "Final",
            }
            return node.value.id in type_names

        # Handle nested type annotations: typing.List[int]
        if isinstance(node.value, ast.Attribute):
            if isinstance(node.value.value, ast.Name) and node.value.value.id == "typing":
                return True

        return False

    def _check_null_pointer_dereference(self, tree: ast.AST) -> None:
        """Check for potential null pointer dereferences."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                # Check for attribute access that might dereference null
                if isinstance(node.value, ast.Name):
                    var_name = node.value.id
                    # Check if variable might be None/null
                    if self._variable_might_be_none(var_name):
                        self.report.add_violation(
                            ConstraintViolation(
                                severity=ConstraintSeverity.ERROR,
                                category=ConstraintCategory.MEMORY_SAFETY,
                                rule_id="MS002",
                                message=f"Potential null pointer dereference of variable '{var_name}'",
                                line_number=node.lineno,
                                suggestion="Add null check before dereferencing",
                            )
                        )

    def _check_memory_leak_potential(self, tree: ast.AST) -> None:
        """Check for potential memory leaks."""
        # This is a simplified check - in real implementation would be more sophisticated
        allocated_vars = set()
        freed_vars = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                func_name = node.func.id
                if func_name in ["malloc", "calloc", "realloc"]:
                    # Memory allocation (hypothetical - Python doesn't have these)
                    # Note: AST nodes don't have .parent attribute by default
                    if hasattr(node, "parent") and isinstance(getattr(node, "parent", None), ast.Assign):
                        allocated_vars.add("allocated_memory")
                elif func_name in ["free"]:
                    freed_vars.add("freed_memory")

        # Check for leaks (simplified)
        if len(allocated_vars) > len(freed_vars):
            self.report.add_violation(
                ConstraintViolation(
                    severity=ConstraintSeverity.WARNING,
                    category=ConstraintCategory.MEMORY_SAFETY,
                    rule_id="MS003",
                    message="Potential memory leak - not all allocated memory is freed",
                    suggestion="Ensure all allocated memory is properly freed",
                )
            )

    def _check_dangling_pointer_risk(self, tree: ast.AST) -> None:
        """Check for dangling pointer risks."""
        # Simplified check for returning local variable addresses
        for node in ast.walk(tree):
            if isinstance(node, ast.Return) and isinstance(node.value, ast.Name):
                # This would need more sophisticated analysis in practice
                pass

    # Type Safety Rules

    def _check_type_consistency(self, tree: ast.AST) -> None:
        """Check for type consistency violations."""
        for node in ast.walk(tree):
            if isinstance(node, ast.BinOp):
                # Check binary operation type compatibility
                left_type = self._infer_expression_type(node.left)
                right_type = self._infer_expression_type(node.right)

                if not self._types_compatible_for_operation(left_type, right_type, node.op):
                    self.report.add_violation(
                        ConstraintViolation(
                            severity=ConstraintSeverity.ERROR,
                            category=ConstraintCategory.TYPE_SAFETY,
                            rule_id="TS001",
                            message=f"Type mismatch in binary operation: {left_type} and {right_type}",
                            line_number=node.lineno,
                            suggestion="Ensure operand types are compatible",
                        )
                    )

    def _check_implicit_conversions(self, tree: ast.AST) -> None:
        """Check for potentially dangerous implicit type conversions."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                # Check assignment type compatibility
                if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                    target_name = node.targets[0].id
                    target_type = self._get_variable_type(target_name)
                    value_type = self._infer_expression_type(node.value)

                    if target_type and value_type != target_type:
                        # Check if conversion is safe
                        if not self._conversion_is_safe(value_type, target_type):
                            self.report.add_violation(
                                ConstraintViolation(
                                    severity=ConstraintSeverity.WARNING,
                                    category=ConstraintCategory.TYPE_SAFETY,
                                    rule_id="TS002",
                                    message=f"Potentially unsafe implicit conversion from {value_type} to {target_type}",
                                    line_number=node.lineno,
                                    suggestion="Add explicit type conversion",
                                )
                            )

    def _check_division_by_zero(self, tree: ast.AST) -> None:
        """Check for potential division by zero."""
        for node in ast.walk(tree):
            if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Div, ast.FloorDiv, ast.Mod)):
                # Check if right operand could be zero
                if isinstance(node.right, ast.Constant) and node.right.value == 0:
                    self.report.add_violation(
                        ConstraintViolation(
                            severity=ConstraintSeverity.ERROR,
                            category=ConstraintCategory.TYPE_SAFETY,
                            rule_id="TS003",
                            message="Division by zero detected",
                            line_number=node.lineno,
                            suggestion="Add zero check before division",
                        )
                    )
                elif isinstance(node.right, ast.Name):
                    # Variable division - add warning
                    self.report.add_violation(
                        ConstraintViolation(
                            severity=ConstraintSeverity.WARNING,
                            category=ConstraintCategory.TYPE_SAFETY,
                            rule_id="TS003",
                            message="Division by variable - ensure divisor is not zero",
                            line_number=node.lineno,
                            suggestion="Add zero check before division",
                        )
                    )

    def _check_integer_overflow(self, tree: ast.AST) -> None:
        """Check for potential integer overflow."""
        for node in ast.walk(tree):
            if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Mult, ast.Pow)):
                # This would need more sophisticated analysis in practice
                # For now, just check for large constants
                if isinstance(node.left, ast.Constant) and isinstance(node.left.value, int):
                    if abs(node.left.value) > 2**31:
                        self.report.add_violation(
                            ConstraintViolation(
                                severity=ConstraintSeverity.WARNING,
                                category=ConstraintCategory.TYPE_SAFETY,
                                rule_id="TS004",
                                message="Large integer constant may cause overflow in C",
                                line_number=node.lineno,
                                suggestion="Use appropriate integer type or bounds checking",
                            )
                        )

    # Static Analysis Rules

    def _check_unreachable_code(self, tree: ast.AST) -> None:
        """Check for unreachable code."""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check for code after return statements
                for i, stmt in enumerate(node.body):
                    if isinstance(stmt, ast.Return) and i < len(node.body) - 1:
                        self.report.add_violation(
                            ConstraintViolation(
                                severity=ConstraintSeverity.WARNING,
                                category=ConstraintCategory.STATIC_ANALYSIS,
                                rule_id="SA001",
                                message="Unreachable code after return statement",
                                line_number=node.body[i + 1].lineno,
                                suggestion="Remove unreachable code",
                            )
                        )

    def _check_unused_variables(self, tree: ast.AST) -> None:
        """Check for unused variables."""
        # This would need data flow analysis in practice
        pass

    def _check_uninitialized_variables(self, tree: ast.AST) -> None:
        """Check for use of uninitialized variables."""
        # This would need data flow analysis in practice
        pass

    def _check_infinite_loops(self, tree: ast.AST) -> None:
        """Check for potential infinite loops."""
        for node in ast.walk(tree):
            if isinstance(node, ast.While):
                # Check for obvious infinite loops
                if isinstance(node.test, ast.Constant) and node.test.value is True:
                    # Check if there's a break statement
                    has_break = any(isinstance(n, ast.Break) for n in ast.walk(node))
                    if not has_break:
                        self.report.add_violation(
                            ConstraintViolation(
                                severity=ConstraintSeverity.ERROR,
                                category=ConstraintCategory.STATIC_ANALYSIS,
                                rule_id="SA004",
                                message="Potential infinite loop detected",
                                line_number=node.lineno,
                                suggestion="Add break condition or modify loop condition",
                            )
                        )

    # C Compatibility Rules

    def _check_unsupported_features(self, tree: ast.AST) -> None:
        """Check for Python features not supported in C conversion."""
        unsupported_nodes = {
            ast.GeneratorExp: "Generator expressions",
            ast.Lambda: "Lambda functions",
            ast.Yield: "Yield statements",
            ast.Try: "Try-except blocks",
            ast.With: "With statements",
        }

        for node in ast.walk(tree):
            for node_type, feature_name in unsupported_nodes.items():
                if isinstance(node, node_type):
                    self.report.add_violation(
                        ConstraintViolation(
                            severity=ConstraintSeverity.ERROR,
                            category=ConstraintCategory.C_COMPATIBILITY,
                            rule_id="CC001",
                            message=f"Unsupported feature for C conversion: {feature_name}",
                            line_number=getattr(node, "lineno", 0),
                            suggestion="Rewrite using supported constructs",
                        )
                    )

            # Special handling for ClassDef - only allow dataclass and namedtuple
            if isinstance(node, ast.ClassDef):
                if not (self._is_dataclass(node) or self._is_namedtuple(node)):
                    self.report.add_violation(
                        ConstraintViolation(
                            severity=ConstraintSeverity.ERROR,
                            category=ConstraintCategory.C_COMPATIBILITY,
                            rule_id="CC001",
                            message="Class definitions only supported for @dataclass and NamedTuple",
                            line_number=node.lineno,
                            suggestion="Use @dataclass decorator or inherit from NamedTuple",
                        )
                    )

            # Check for dynamic execution functions
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in ("eval", "exec", "compile", "__import__"):
                    self.report.add_violation(
                        ConstraintViolation(
                            severity=ConstraintSeverity.ERROR,
                            category=ConstraintCategory.C_COMPATIBILITY,
                            rule_id="CC001",
                            message=f"Dynamic execution function '{node.func.id}' not supported for C conversion",
                            line_number=node.lineno,
                            suggestion="Replace with static constructs",
                        )
                    )

    def _is_dataclass(self, node: ast.ClassDef) -> bool:
        """Check if class has @dataclass decorator."""
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name) and decorator.id == "dataclass":
                return True
            elif isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name):
                if decorator.func.id == "dataclass":
                    return True
        return False

    def _is_namedtuple(self, node: ast.ClassDef) -> bool:
        """Check if class inherits from NamedTuple."""
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id == "NamedTuple":
                return True
            elif isinstance(base, ast.Attribute):
                if isinstance(base.value, ast.Name) and base.value.id == "typing" and base.attr == "NamedTuple":
                    return True
        return False

    def _check_name_conflicts(self, tree: ast.AST) -> None:
        """Check for naming conflicts with C keywords/stdlib."""
        c_keywords = {
            "auto",
            "break",
            "case",
            "char",
            "const",
            "continue",
            "default",
            "do",
            "double",
            "else",
            "enum",
            "extern",
            "float",
            "for",
            "goto",
            "if",
            "int",
            "long",
            "register",
            "return",
            "short",
            "signed",
            "sizeof",
            "static",
            "struct",
            "switch",
            "typedef",
            "union",
            "unsigned",
            "void",
            "volatile",
            "while",
        }

        # Collect type annotation nodes to exclude from conflict checking
        type_annotation_nodes = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AnnAssign)):
                if isinstance(node, ast.FunctionDef):
                    # Function return type annotation
                    if node.returns:
                        for child in ast.walk(node.returns):
                            if isinstance(child, ast.Name):
                                type_annotation_nodes.add(child)
                    # Parameter type annotations
                    for arg in node.args.args:
                        if arg.annotation:
                            for child in ast.walk(arg.annotation):
                                if isinstance(child, ast.Name):
                                    type_annotation_nodes.add(child)
                elif isinstance(node, ast.AnnAssign):
                    # Variable type annotation
                    for child in ast.walk(node.annotation):
                        if isinstance(child, ast.Name):
                            type_annotation_nodes.add(child)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                name = node.name
                if name in c_keywords:
                    self.report.add_violation(
                        ConstraintViolation(
                            severity=ConstraintSeverity.ERROR,
                            category=ConstraintCategory.C_COMPATIBILITY,
                            rule_id="CC002",
                            message=f"Name conflict with C keyword: '{name}'",
                            line_number=node.lineno,
                            suggestion=f"Rename '{name}' to avoid C keyword conflict",
                        )
                    )
            elif isinstance(node, ast.Name) and node not in type_annotation_nodes:
                # Only check actual variable/function names, not type annotations
                name = node.id
                if name in c_keywords and isinstance(node.ctx, (ast.Store, ast.Del)):
                    # Only flag when name is being assigned/deleted, not just referenced
                    self.report.add_violation(
                        ConstraintViolation(
                            severity=ConstraintSeverity.ERROR,
                            category=ConstraintCategory.C_COMPATIBILITY,
                            rule_id="CC002",
                            message=f"Name conflict with C keyword: '{name}'",
                            line_number=node.lineno,
                            suggestion=f"Rename '{name}' to avoid C keyword conflict",
                        )
                    )

    def _check_reserved_keywords(self, tree: ast.AST) -> None:
        """Check for use of reserved keywords that might cause issues."""
        # Implementation similar to name conflicts
        pass

    def _check_function_complexity(self, tree: ast.AST) -> None:
        """Check if functions are too complex for safe conversion."""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                complexity = self._calculate_complexity(node)
                if complexity > 10:  # Arbitrary threshold
                    self.report.add_violation(
                        ConstraintViolation(
                            severity=ConstraintSeverity.WARNING,
                            category=ConstraintCategory.C_COMPATIBILITY,
                            rule_id="CC004",
                            message=f"Function '{node.name}' is highly complex (score: {complexity})",
                            line_number=node.lineno,
                            suggestion="Consider breaking into smaller functions",
                        )
                    )

    # Performance Rules

    def _check_inefficient_patterns(self, tree: ast.AST) -> None:
        """Check for inefficient coding patterns."""
        # Example: string concatenation in loops
        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.While)):
                for stmt in ast.walk(node):
                    if isinstance(stmt, ast.BinOp) and isinstance(stmt.op, ast.Add):
                        # Check if string concatenation
                        left_type = self._infer_expression_type(stmt.left)
                        if left_type == "str":
                            self.report.add_violation(
                                ConstraintViolation(
                                    severity=ConstraintSeverity.WARNING,
                                    category=ConstraintCategory.PERFORMANCE,
                                    rule_id="PF001",
                                    message="String concatenation in loop may be inefficient",
                                    line_number=stmt.lineno,
                                    suggestion="Consider using buffer or array for string building",
                                )
                            )

    def _check_repeated_computations(self, tree: ast.AST) -> None:
        """Check for computations that could be cached."""
        # This would need more sophisticated analysis
        pass

    def _check_memory_allocation_patterns(self, tree: ast.AST) -> None:
        """Check for inefficient memory allocation patterns."""
        # This would analyze list/array creation patterns
        pass

    # Correctness Rules

    def _check_return_path_coverage(self, tree: ast.AST) -> None:
        """Check that all code paths return a value when needed."""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.returns and not isinstance(node.returns, ast.Constant):
                    # Function should return a value
                    has_return = any(isinstance(n, ast.Return) and n.value for n in ast.walk(node))
                    if not has_return:
                        self.report.add_violation(
                            ConstraintViolation(
                                severity=ConstraintSeverity.ERROR,
                                category=ConstraintCategory.CORRECTNESS,
                                rule_id="CR001",
                                message=f"Function '{node.name}' may not return a value on all paths",
                                line_number=node.lineno,
                                suggestion="Ensure all code paths return appropriate values",
                            )
                        )

    def _check_parameter_validation(self, tree: ast.AST) -> None:
        """Check for proper parameter validation."""
        # This would check for bounds checking on parameters
        pass

    def _check_bounds_checking(self, tree: ast.AST) -> None:
        """Check for proper bounds checking on array access."""
        # Implementation would analyze array access patterns
        pass

    # Utility methods

    def _extract_type_info(self, annotation: ast.expr) -> TypeInfo:
        """Extract type information from AST annotation."""
        if isinstance(annotation, ast.Name):
            return TypeInfo(annotation.id)
        return TypeInfo("unknown")

    def _variable_might_be_none(self, var_name: str) -> bool:
        """Check if a variable might be None."""
        # Check if variable is in current scope and has a known type
        if self.current_function and self.current_function in self.variable_scopes:
            scope = self.variable_scopes[self.current_function]
            if var_name in scope:
                var_info = scope[var_name]
                # If variable has a concrete type annotation like list[int], it's not None
                if hasattr(var_info, "type_annotation") and getattr(var_info, "type_annotation", None):
                    return False
                # If variable is a built-in collection type, it's initialized
                if hasattr(var_info, "inferred_type"):
                    inferred = getattr(var_info, "inferred_type", None)
                    if inferred in ["list", "dict", "set", "tuple"]:
                        return False

        # For known variable patterns that are clearly initialized
        # This is a simplified check for common patterns
        return False  # Less conservative - trust type annotations and initialization patterns

    def _infer_expression_type(self, expr: ast.expr) -> str:
        """Infer the type of an expression."""
        if isinstance(expr, ast.Constant):
            return type(expr.value).__name__
        elif isinstance(expr, ast.Name):
            # For variables, we'd need scope analysis
            # For now, return the name for known builtin types
            if expr.id in ["int", "float", "str", "bool"]:
                return expr.id
            return "unknown"
        elif isinstance(expr, ast.Call) and isinstance(expr.func, ast.Name):
            # Handle builtin function calls
            if expr.func.id == "range":
                return "int"  # range() returns integers when iterated
            elif expr.func.id == "len":
                return "int"
            elif expr.func.id in ["int", "float", "str", "bool"]:
                return expr.func.id
            return "unknown"
        elif isinstance(expr, ast.BinOp):
            left_type = self._infer_expression_type(expr.left)
            right_type = self._infer_expression_type(expr.right)
            # Simple type inference for binary operations
            if isinstance(expr.op, (ast.Add, ast.Sub, ast.Mult)):
                if left_type == "int" and right_type == "int":
                    return "int"
                elif left_type in ["int", "float"] and right_type in ["int", "float"]:
                    return "float"
            return "unknown"
        return "unknown"

    def _types_compatible_for_operation(self, left_type: str, right_type: str, op: ast.operator) -> bool:
        """Check if types are compatible for the given operation."""
        # Simplified compatibility check
        if left_type == right_type:
            return True
        if left_type in ["int", "float"] and right_type in ["int", "float"]:
            return True
        # Don't flag errors for unknown types (too conservative)
        if left_type == "unknown" or right_type == "unknown":
            return True
        return False

    def _get_variable_type(self, var_name: str) -> Optional[str]:
        """Get the type of a variable."""
        # Would need scope analysis
        return None

    def _conversion_is_safe(self, from_type: str, to_type: str) -> bool:
        """Check if type conversion is safe."""
        safe_conversions = {
            ("int", "float"): True,
            ("int", "double"): True,
            ("float", "double"): True,
        }
        return safe_conversions.get((from_type, to_type), False)

    def _calculate_complexity(self, func_node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1  # Base complexity
        for node in ast.walk(func_node):
            if isinstance(node, (ast.If, ast.For, ast.While, ast.Try)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        return complexity

    def _calculate_confidence_score(self) -> None:
        """Calculate overall confidence score for conversion."""
        critical_errors = len(self.report.get_violations_by_severity(ConstraintSeverity.CRITICAL))
        errors = len(self.report.get_violations_by_severity(ConstraintSeverity.ERROR))
        warnings = len(self.report.get_violations_by_severity(ConstraintSeverity.WARNING))

        if critical_errors > 0:
            self.report.confidence_score = 0.0
        elif errors > 0:
            self.report.confidence_score = max(0.0, 1.0 - (errors * 0.3))
        elif warnings > 0:
            self.report.confidence_score = max(0.7, 1.0 - (warnings * 0.1))
        else:
            self.report.confidence_score = 1.0
