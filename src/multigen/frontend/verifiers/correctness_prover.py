"""Algorithm Correctness Verification.

This module provides formal verification of algorithm correctness using
preconditions, postconditions, loop invariants, and functional specifications.
"""

import ast
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

try:
    import z3  # type: ignore[import-untyped]

    Z3_AVAILABLE = True
except ImportError:
    Z3_AVAILABLE = False
    z3 = None


from ..base import AnalysisContext
from .theorem_prover import ProofProperty, ProofResult, ProofStatus, PropertyType, TheoremProver


class CorrectnessPropertyType(Enum):
    """Types of correctness properties."""

    PRECONDITION = "precondition"
    POSTCONDITION = "postcondition"
    LOOP_INVARIANT = "loop_invariant"
    ASSERTION = "assertion"
    FUNCTIONAL_CORRECTNESS = "functional_correctness"
    TERMINATION = "termination"
    PARTIAL_CORRECTNESS = "partial_correctness"
    TOTAL_CORRECTNESS = "total_correctness"


@dataclass
class FormalSpecification:
    """Formal specification of a function or algorithm."""

    name: str
    preconditions: list[str]  # Conditions that must hold at function entry
    postconditions: list[str]  # Conditions that must hold at function exit
    loop_invariants: dict[int, list[str]]  # Line number -> invariants
    assertions: dict[int, str]  # Line number -> assertion
    termination_conditions: list[str]  # Conditions ensuring termination
    functional_spec: Optional[str] = None  # High-level functional specification


@dataclass
class AlgorithmProof:
    """Result of algorithm correctness verification."""

    function_name: str
    specification: FormalSpecification
    correctness_type: CorrectnessPropertyType
    is_correct: bool
    proof_results: list[ProofResult]
    failed_properties: list[str]
    loop_analysis: dict[int, dict[str, Any]]
    verification_time: float
    confidence: float

    @property
    def summary(self) -> str:
        """Human-readable summary of the proof."""
        status = "CORRECT" if self.is_correct else "INCORRECT"
        return f"{self.function_name}: {self.correctness_type.value} - {status} (confidence: {self.confidence:.2f})"


class CorrectnessProver:
    """Formal verification of algorithm correctness."""

    def __init__(self, theorem_prover: Optional[TheoremProver] = None):
        """Initialize the correctness prover.

        Args:
            theorem_prover: Z3 theorem prover instance
        """
        self.theorem_prover = theorem_prover or TheoremProver()
        self.z3_available = Z3_AVAILABLE

        # Built-in algorithm specifications
        self.algorithm_specs = {
            "factorial": self._factorial_specification,
            "fibonacci": self._fibonacci_specification,
            "binary_search": self._binary_search_specification,
            "merge_sort": self._merge_sort_specification,
            "quicksort": self._quicksort_specification,
        }

    def verify_algorithm_correctness(
        self, context: AnalysisContext, specification: Optional[FormalSpecification] = None
    ) -> AlgorithmProof:
        """Verify algorithm correctness using formal methods.

        Args:
            context: Analysis context with AST and metadata
            specification: Optional formal specification

        Returns:
            AlgorithmProof with verification results
        """
        start_time = time.time()

        function_name = self._extract_function_name(context)

        # Auto-detect specification if not provided
        if specification is None:
            specification = self._infer_specification(function_name, context)

        # Extract algorithm structure
        algorithm_extractor = AlgorithmStructureExtractor()
        algorithm_extractor.visit(context.ast_node)

        # Verify different aspects of correctness
        all_proof_results = []
        failed_properties = []

        # 1. Verify preconditions
        precondition_results = self._verify_preconditions(specification, context)
        all_proof_results.extend(precondition_results)

        # 2. Verify postconditions
        postcondition_results = self._verify_postconditions(specification, context)
        all_proof_results.extend(postcondition_results)

        # 3. Verify loop invariants
        loop_results, loop_analysis = self._verify_loop_invariants(specification, algorithm_extractor, context)
        all_proof_results.extend(loop_results)

        # 4. Verify termination
        termination_results = self._verify_termination(specification, algorithm_extractor, context)
        all_proof_results.extend(termination_results)

        # 5. Verify functional correctness if specified
        if specification.functional_spec:
            functional_results = self._verify_functional_correctness(specification, context)
            all_proof_results.extend(functional_results)

        # Determine overall correctness
        is_correct = all(result.is_verified for result in all_proof_results)

        # A property is only "failed" when Z3 produced a counterexample. An
        # undecided property is unproved, not violated.
        for result in all_proof_results:
            if result.status == ProofStatus.DISPROVED:
                failed_properties.append(result.proof_property.name)

        # Calculate confidence
        confidence = self._calculate_correctness_confidence(all_proof_results)

        verification_time = time.time() - start_time

        return AlgorithmProof(
            function_name=function_name,
            specification=specification,
            correctness_type=CorrectnessPropertyType.TOTAL_CORRECTNESS,
            is_correct=is_correct,
            proof_results=all_proof_results,
            failed_properties=failed_properties,
            loop_analysis=loop_analysis,
            verification_time=verification_time,
            confidence=confidence,
        )

    def _undecided(self, prop: ProofProperty, reason: str) -> ProofResult:
        """Record a property this prover cannot decide.

        Every check below the precondition level needs a model of what the
        function body does, which this prover does not build. Handing the bare
        specification to Z3 instead would ask whether it holds for *all* values
        of its free variables - almost never true - and report correct code as
        disproved.

        Args:
            prop: The property that was not decided
            reason: Why it could not be decided

        Returns:
            A ProofResult with UNKNOWN status
        """
        return ProofResult(
            proof_property=prop,
            status=ProofStatus.UNKNOWN,
            proof_time=0.0,
            error_message=reason,
        )

    def _verify_preconditions(self, spec: FormalSpecification, context: AnalysisContext) -> list[ProofResult]:
        """Check that each precondition is satisfiable.

        A precondition is an assumption, not a theorem: proving it outright would
        ask whether it holds for every input. What can be checked is consistency
        - an unsatisfiable precondition makes the whole specification vacuous.
        """
        results = []

        for i, precondition in enumerate(spec.preconditions):
            prop = self._create_precondition_property(f"{spec.name}_pre_{i}", precondition)
            results.append(self._check_satisfiable(prop))

        return results

    def _check_satisfiable(self, prop: ProofProperty) -> ProofResult:
        """Check a property for satisfiability rather than validity.

        Args:
            prop: The property to check

        Returns:
            PROVED when a model exists, DISPROVED when the formula is
            contradictory, UNKNOWN when Z3 cannot decide or is unavailable
        """
        if not self.z3_available:
            return self._undecided(prop, "Z3 not available. Install with: pip install z3-solver")

        start_time = time.time()
        try:
            solver = z3.Solver()
            solver.add(prop.z3_formula)
            outcome = solver.check()
            proof_time = time.time() - start_time

            if outcome == z3.sat:
                return ProofResult(
                    proof_property=prop,
                    status=ProofStatus.PROVED,
                    proof_time=proof_time,
                    verification_steps=[f"Z3 found a model in {proof_time:.3f}s"],
                )
            if outcome == z3.unsat:
                return ProofResult(
                    proof_property=prop,
                    status=ProofStatus.DISPROVED,
                    proof_time=proof_time,
                    error_message="assumption is contradictory, so the specification is vacuous",
                )
            return self._undecided(prop, "Z3 could not determine satisfiability")
        except Exception as exc:  # pragma: no cover - defensive
            return ProofResult(
                proof_property=prop,
                status=ProofStatus.ERROR,
                proof_time=time.time() - start_time,
                error_message=str(exc),
            )

    def _verify_postconditions(self, spec: FormalSpecification, context: AnalysisContext) -> list[ProofResult]:
        """Record postconditions as undecided.

        Proving a postcondition needs the function body's transition relation,
        which this prover does not construct.
        """
        results = []

        for i, postcondition in enumerate(spec.postconditions):
            prop = self._create_postcondition_property(f"{spec.name}_post_{i}", postcondition)
            results.append(self._undecided(prop, "postcondition needs a model of the function body"))

        return results

    def _verify_loop_invariants(
        self, spec: FormalSpecification, extractor: "AlgorithmStructureExtractor", context: AnalysisContext
    ) -> tuple[list[ProofResult], dict[int, dict[str, Any]]]:
        """Verify loop invariants."""
        results = []
        loop_analysis = {}

        for line_no, invariants in spec.loop_invariants.items():
            loop_info = extractor.get_loop_info(line_no)
            if loop_info:
                loop_analysis[line_no] = loop_info

                for i, invariant in enumerate(invariants):
                    # Verify invariant holds at loop entry
                    entry_prop = self._create_loop_invariant_property(
                        f"{spec.name}_loop_{line_no}_entry_{i}", invariant, "entry", loop_info
                    )
                    results.append(
                        self._undecided(entry_prop, "loop invariant entry needs a model of the loop's state")
                    )

                    # Verify invariant is maintained
                    maintenance_prop = self._create_loop_invariant_property(
                        f"{spec.name}_loop_{line_no}_maintenance_{i}", invariant, "maintenance", loop_info
                    )
                    results.append(
                        self._undecided(
                            maintenance_prop, "loop invariant maintenance needs the loop's transition relation"
                        )
                    )

        return results, loop_analysis

    def _verify_termination(
        self, spec: FormalSpecification, extractor: "AlgorithmStructureExtractor", context: AnalysisContext
    ) -> list[ProofResult]:
        """Verify algorithm termination."""
        results = []

        # Verify termination conditions
        for i, termination_condition in enumerate(spec.termination_conditions):
            prop = self._create_termination_property(f"{spec.name}_termination_{i}", termination_condition)
            results.append(self._undecided(prop, "termination needs a model of how the loop variables change"))

        # Verify loop termination using ranking functions
        for loop_info in extractor.loops:
            ranking_prop = self._create_ranking_function_property(loop_info)
            results.append(
                self._undecided(ranking_prop, "no transition relation is available to establish a ranking function")
            )

        return results

    def _verify_functional_correctness(self, spec: FormalSpecification, context: AnalysisContext) -> list[ProofResult]:
        """Verify functional correctness specification."""
        func_spec = spec.functional_spec if spec.functional_spec is not None else ""
        prop = self._create_functional_correctness_property(spec.name, func_spec)
        return [self._undecided(prop, "functional correctness needs a model of the function body")]

    def _create_precondition_property(self, name: str, precondition: str) -> ProofProperty:
        """Create a precondition verification property."""
        if not self.z3_available:
            return ProofProperty(
                name=name,
                property_type=PropertyType.PRECONDITION_SATISFACTION,
                description=f"Precondition: {precondition}",
                z3_formula="mock_formula",
            )

        # Parse precondition into Z3 formula
        z3_formula = self._parse_condition_to_z3(precondition)

        return ProofProperty(
            name=name,
            property_type=PropertyType.PRECONDITION_SATISFACTION,
            description=f"Precondition: {precondition}",
            z3_formula=z3_formula,
        )

    def _create_postcondition_property(self, name: str, postcondition: str) -> ProofProperty:
        """Create a postcondition verification property."""
        if not self.z3_available:
            return ProofProperty(
                name=name,
                property_type=PropertyType.POSTCONDITION_SATISFACTION,
                description=f"Postcondition: {postcondition}",
                z3_formula="mock_formula",
            )

        z3_formula = self._parse_condition_to_z3(postcondition)

        return ProofProperty(
            name=name,
            property_type=PropertyType.POSTCONDITION_SATISFACTION,
            description=f"Postcondition: {postcondition}",
            z3_formula=z3_formula,
        )

    def _create_loop_invariant_property(
        self, name: str, invariant: str, phase: str, loop_info: dict[str, Any]
    ) -> ProofProperty:
        """Create a loop invariant verification property."""
        if not self.z3_available:
            return ProofProperty(
                name=name,
                property_type=PropertyType.LOOP_INVARIANT,
                description=f"Loop invariant ({phase}): {invariant}",
                z3_formula="mock_formula",
            )

        z3_formula = self._parse_condition_to_z3(invariant)

        return ProofProperty(
            name=name,
            property_type=PropertyType.LOOP_INVARIANT,
            description=f"Loop invariant ({phase}): {invariant}",
            z3_formula=z3_formula,
            context={"loop_info": loop_info, "phase": phase},
        )

    def _create_termination_property(self, name: str, termination_condition: str) -> ProofProperty:
        """Create a termination verification property."""
        if not self.z3_available:
            return ProofProperty(
                name=name,
                property_type=PropertyType.TERMINATION,
                description=f"Termination: {termination_condition}",
                z3_formula="mock_formula",
            )

        z3_formula = self._parse_condition_to_z3(termination_condition)

        return ProofProperty(
            name=name,
            property_type=PropertyType.TERMINATION,
            description=f"Termination: {termination_condition}",
            z3_formula=z3_formula,
        )

    def _create_ranking_function_property(self, loop_info: dict[str, Any]) -> ProofProperty:
        """Create a ranking function property for loop termination."""
        if not self.z3_available:
            return ProofProperty(
                name=f"ranking_function_loop_{loop_info.get('line', 'unknown')}",
                property_type=PropertyType.TERMINATION,
                description="Ranking function ensures loop termination",
                z3_formula="mock_formula",
            )

        # A ranking function requires a transition relation between loop
        # iterations. The extractor does not provide one, so fail closed
        # rather than claiming that non-negativity alone proves termination.
        ranking_formula: Any = z3.BoolVal(False)

        return ProofProperty(
            name=f"ranking_function_loop_{loop_info.get('line', 'unknown')}",
            property_type=PropertyType.TERMINATION,
            description="Ranking function could not be established from the available loop transition data",
            z3_formula=ranking_formula,
            context={"loop_info": loop_info},
        )

    def _create_functional_correctness_property(self, name: str, functional_spec: str) -> ProofProperty:
        """Create a functional correctness property."""
        if not self.z3_available:
            return ProofProperty(
                name=f"{name}_functional_correctness",
                property_type=PropertyType.FUNCTIONAL_CORRECTNESS,
                description=f"Functional correctness: {functional_spec}",
                z3_formula="mock_formula",
            )

        z3_formula = self._parse_condition_to_z3(functional_spec)

        return ProofProperty(
            name=f"{name}_functional_correctness",
            property_type=PropertyType.FUNCTIONAL_CORRECTNESS,
            description=f"Functional correctness: {functional_spec}",
            z3_formula=z3_formula,
        )

    def _parse_condition_to_z3(self, condition: str) -> Any:
        """Parse a textual condition into a Z3 formula."""
        if not self.z3_available:
            return "mock_formula"

        try:
            expression = ast.parse(condition, mode="eval").body
            formula = self._ast_expression_to_z3(expression, expect_bool=True, declared={})
            if not z3.is_bool(formula):
                raise ValueError("specification does not denote a Boolean condition")
            return formula
        except (SyntaxError, ValueError, TypeError, z3.Z3Exception):
            # Never turn an unsupported specification into an unconstrained
            # Boolean. A false formula makes the attempted proof fail closed.
            # Z3Exception covers sort mismatches that only show up once the
            # translated sub-expressions are combined.
            return z3.BoolVal(False)

    def _ast_expression_to_z3(
        self,
        expression: ast.AST,
        expect_bool: bool = False,
        declared: Optional[dict[str, str]] = None,
    ) -> Any:
        """Translate the supported Python expression subset to Z3.

        ``expect_bool`` records whether the surrounding syntax requires a
        Boolean, which decides the sort of a bare name. ``declared`` tracks the
        sort already chosen for each name, so a specification that uses one name
        as both an integer and a Boolean is rejected instead of being translated
        into two unrelated Z3 constants that happen to share a printed name.
        """
        if declared is None:
            declared = {}

        if isinstance(expression, ast.Constant):
            if isinstance(expression.value, bool):
                return z3.BoolVal(expression.value)
            if isinstance(expression.value, (int, float)):
                return (
                    z3.RealVal(expression.value) if isinstance(expression.value, float) else z3.IntVal(expression.value)
                )
            if isinstance(expression.value, str):
                return z3.StringVal(expression.value)
        if isinstance(expression, ast.Name):
            # Specifications are written by hand and use both Python and
            # SMT-style spellings of the Boolean constants.
            if expression.id in ("True", "true"):
                return z3.BoolVal(True)
            if expression.id in ("False", "false"):
                return z3.BoolVal(False)
            sort = "bool" if expect_bool else "int"
            if declared.setdefault(expression.id, sort) != sort:
                raise ValueError(f"name '{expression.id}' is used with conflicting sorts")
            return z3.Bool(expression.id) if expect_bool else z3.Int(expression.id)
        if isinstance(expression, ast.UnaryOp):
            if isinstance(expression.op, ast.Not):
                return z3.Not(self._ast_expression_to_z3(expression.operand, True, declared))
            operand = self._ast_expression_to_z3(expression.operand, False, declared)
            if isinstance(expression.op, ast.USub):
                return -operand
            if isinstance(expression.op, ast.UAdd):
                return operand
        if isinstance(expression, ast.BoolOp):
            values = [self._ast_expression_to_z3(value, True, declared) for value in expression.values]
            if isinstance(expression.op, ast.And):
                return z3.And(values)
            if isinstance(expression.op, ast.Or):
                return z3.Or(values)
        if isinstance(expression, ast.BinOp):
            left = self._ast_expression_to_z3(expression.left, False, declared)
            right = self._ast_expression_to_z3(expression.right, False, declared)
            operators: dict[type[ast.operator], Callable[[], Any]] = {
                ast.Add: lambda: left + right,
                ast.Sub: lambda: left - right,
                ast.Mult: lambda: left * right,
                ast.Div: lambda: left / right,
                ast.FloorDiv: lambda: left / right,
                ast.Mod: lambda: left % right,
            }
            for operator_type, operation in operators.items():
                if isinstance(expression.op, operator_type):
                    return operation()
        if isinstance(expression, ast.Compare):
            left = self._ast_expression_to_z3(expression.left, False, declared)
            comparisons = []
            for operator, comparator in zip(expression.ops, expression.comparators):
                right = self._ast_expression_to_z3(comparator, False, declared)
                # Distinct name from the binary-operator table above: reusing
                # one name in the same scope conflates the two value types.
                comparison_operators = {
                    ast.Eq: left == right,
                    ast.NotEq: left != right,
                    ast.Lt: left < right,
                    ast.LtE: left <= right,
                    ast.Gt: left > right,
                    ast.GtE: left >= right,
                }
                for comparison_type, comparison in comparison_operators.items():
                    if isinstance(operator, comparison_type):
                        comparisons.append(comparison)
                        break
                else:
                    raise ValueError("unsupported comparison")
                left = right
            return z3.And(comparisons)
        if isinstance(expression, ast.Call) and isinstance(expression.func, ast.Name) and expression.func.id == "len":
            if len(expression.args) == 1 and isinstance(expression.args[0], ast.Name):
                return z3.Int(f"len_{expression.args[0].id}")
        raise ValueError("unsupported specification expression")

    def _extract_function_name(self, context: AnalysisContext) -> str:
        """Extract function name from context."""
        if context.analysis_result and hasattr(context.analysis_result, "functions"):
            if context.analysis_result.functions:
                return list(context.analysis_result.functions.keys())[0]
        elif hasattr(context.ast_node, "name"):
            name: str = context.ast_node.name
            return name
        return "unknown_function"

    def _infer_specification(self, function_name: str, context: AnalysisContext) -> FormalSpecification:
        """Infer formal specification for known algorithms."""
        if function_name in self.algorithm_specs:
            return self.algorithm_specs[function_name]()

        # Create a basic specification
        return FormalSpecification(
            name=function_name,
            preconditions=["true"],  # Default: no preconditions
            postconditions=["true"],  # Default: no postconditions
            loop_invariants={},
            assertions={},
            termination_conditions=["true"],
        )

    def _calculate_correctness_confidence(self, proof_results: list[ProofResult]) -> float:
        """Calculate confidence in correctness verification."""
        if not proof_results:
            return 0.0

        proved_count = sum(1 for result in proof_results if result.status == ProofStatus.PROVED)
        total_count = len(proof_results)

        return proved_count / total_count

    # Built-in algorithm specifications

    def _factorial_specification(self) -> FormalSpecification:
        """Formal specification for factorial function."""
        return FormalSpecification(
            name="factorial",
            preconditions=["n >= 0"],
            postconditions=["result >= 1", "result == factorial_math(n)"],
            loop_invariants={},
            assertions={},
            termination_conditions=["n decreases towards 0"],
            functional_spec="result == n! (mathematical factorial)",
        )

    def _fibonacci_specification(self) -> FormalSpecification:
        """Formal specification for Fibonacci function."""
        return FormalSpecification(
            name="fibonacci",
            preconditions=["n >= 0"],
            postconditions=["result >= 0", "result == fib_math(n)"],
            loop_invariants={},
            assertions={},
            termination_conditions=["n decreases towards base case"],
            functional_spec="result == nth Fibonacci number",
        )

    def _binary_search_specification(self) -> FormalSpecification:
        """Formal specification for binary search."""
        return FormalSpecification(
            name="binary_search",
            preconditions=["array is sorted", "0 <= left <= right < len(array)"],
            postconditions=["result == -1 OR array[result] == target"],
            loop_invariants={
                # Line numbers would be determined during analysis
            },
            assertions={},
            termination_conditions=["search space decreases each iteration"],
            functional_spec="finds target in sorted array or returns -1",
        )

    def _merge_sort_specification(self) -> FormalSpecification:
        """Formal specification for merge sort."""
        return FormalSpecification(
            name="merge_sort",
            preconditions=["array is valid"],
            postconditions=["array is sorted", "array contains same elements as input"],
            loop_invariants={},
            assertions={},
            termination_conditions=["recursive calls reduce problem size"],
            functional_spec="sorts array in O(n log n) time",
        )

    def _quicksort_specification(self) -> FormalSpecification:
        """Formal specification for quicksort."""
        return FormalSpecification(
            name="quicksort",
            preconditions=["array is valid", "left <= right"],
            postconditions=["array[left:right+1] is sorted", "permutation preserved"],
            loop_invariants={},
            assertions={},
            termination_conditions=["partition reduces problem size"],
            functional_spec="sorts array in average O(n log n) time",
        )


class AlgorithmStructureExtractor(ast.NodeVisitor):
    """Extract algorithm structure for correctness verification."""

    def __init__(self) -> None:
        self.loops: list[dict[str, Any]] = []
        self.recursive_calls: list[dict[str, Any]] = []
        self.assertions: list[dict[str, Any]] = []
        self.variables: set[str] = set()
        self.current_function: Optional[str] = None

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Track function context."""
        self.current_function = node.name
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        """Extract for loop information."""
        loop_info: dict[str, Any] = {
            "type": "for",
            "line": node.lineno,
            "variable": None,
            "iterable": None,
            "body_lines": [],
        }

        # Extract loop variable
        if isinstance(node.target, ast.Name):
            loop_info["variable"] = node.target.id

        # Extract iterable information
        if isinstance(node.iter, ast.Call) and isinstance(node.iter.func, ast.Name):
            if node.iter.func.id == "range":
                loop_info["iterable"] = "range"
                loop_info["range_args"] = len(node.iter.args)

        # Extract body line numbers
        for stmt in node.body:
            loop_info["body_lines"].append(stmt.lineno)

        self.loops.append(loop_info)
        self.generic_visit(node)

    def visit_While(self, node: ast.While) -> None:
        """Extract while loop information."""
        loop_info: dict[str, Any] = {
            "type": "while",
            "line": node.lineno,
            "condition": ast.unparse(node.test) if hasattr(ast, "unparse") else str(node.test),
            "body_lines": [],
        }

        # Extract body line numbers
        for stmt in node.body:
            loop_info["body_lines"].append(stmt.lineno)

        self.loops.append(loop_info)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        """Extract function calls (including recursive calls)."""
        if isinstance(node.func, ast.Name):
            if node.func.id == self.current_function:
                # Recursive call
                self.recursive_calls.append({"line": node.lineno, "function": node.func.id, "args": len(node.args)})

        self.generic_visit(node)

    def visit_Assert(self, node: ast.Assert) -> None:
        """Extract assertion statements."""
        assertion_info: dict[str, Any] = {
            "line": node.lineno,
            "condition": ast.unparse(node.test) if hasattr(ast, "unparse") else str(node.test),
            "message": None,
        }

        if node.msg:
            assertion_info["message"] = ast.unparse(node.msg) if hasattr(ast, "unparse") else str(node.msg)

        self.assertions.append(assertion_info)
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        """Extract variable names."""
        self.variables.add(node.id)
        self.generic_visit(node)

    def get_loop_info(self, line_no: int) -> Optional[dict[str, Any]]:
        """Get loop information for a specific line number."""
        for loop in self.loops:
            if loop["line"] == line_no:
                return loop
        return None
