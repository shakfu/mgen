"""One static validation pass over one parse.

The frontend already had four analyses that each answered part of "can this be
translated": the subset validator, the AST analyzer, the universal constraint
checker, and type inference. Each parsed the source itself, reported in its own
shape, and was wired up separately by every caller.

`StaticValidator` runs them over a single parse and merges everything into one
ordered list of `Diagnostic`s, so a caller asks one question and gets one answer.

Type inference contributes the judgement the others cannot make: a construct can
be individually legal and still not translatable, because nothing determined
what type it has. Whether that is fatal is a policy choice, so it is a parameter
rather than a hardcoded rule.
"""

import ast
from dataclasses import dataclass, field, replace
from typing import Any, Optional

from .ast_analyzer import ASTAnalyzer
from .diagnostics import Diagnostic, DiagnosticSeverity, RuleId, SourceSpan, diagnostics_to_json
from .python_constraints import PythonConstraintChecker, PythonConstraintViolation
from .static_profile import DEFAULT_CONFIDENCE_THRESHOLD, DEFAULT_PROFILE, StaticProfile
from .subset_validator import StaticPythonSubsetValidator, SubsetTier, ValidationResult
from .type_inference import TypeInferenceEngine

__all__ = ["DEFAULT_CONFIDENCE_THRESHOLD", "StaticValidationReport", "StaticValidator"]

_SEVERITY_BY_NAME = {
    "error": DiagnosticSeverity.ERROR,
    "warning": DiagnosticSeverity.WARNING,
    "info": DiagnosticSeverity.INFO,
}


def _source_order(diagnostic: Diagnostic) -> tuple[int, int, int]:
    """Sort located diagnostics by position, and unlocated ones last."""
    if diagnostic.span is None:
        return (1, 0, 0)
    return (0, diagnostic.span.line, diagnostic.span.column)


def _deduplicate(diagnostics: list[Diagnostic]) -> list[Diagnostic]:
    """Drop diagnostics identical in rule, message and position."""
    seen: set[tuple[str, str, Optional[tuple[int, int]]]] = set()
    unique = []
    for diagnostic in diagnostics:
        span = (diagnostic.span.line, diagnostic.span.column) if diagnostic.span else None
        key = (diagnostic.rule_id, diagnostic.message, span)
        if key in seen:
            continue
        seen.add(key)
        unique.append(diagnostic)
    return unique


@dataclass
class StaticValidationReport:
    """The merged result of every static analysis."""

    is_valid: bool
    tier: SubsetTier
    diagnostics: list[Diagnostic] = field(default_factory=list)
    subset: Optional[ValidationResult] = None
    conversion_strategy: Optional[str] = None
    profile: Optional[StaticProfile] = None

    @property
    def profile_name(self) -> str:
        """Name of the profile this report was produced under."""
        return self.profile.name if self.profile else DEFAULT_PROFILE.name

    @property
    def violations(self) -> list[str]:
        """Error messages, in source order."""
        return [d.message for d in self.diagnostics if d.is_error]

    @property
    def warnings(self) -> list[str]:
        """Non-blocking messages, in source order."""
        return [d.message for d in self.diagnostics if not d.is_error]

    def errors(self) -> list[Diagnostic]:
        """Diagnostics that make the source untranslatable."""
        return [d for d in self.diagnostics if d.is_error]

    def by_rule(self, rule_id: str) -> list[Diagnostic]:
        """Diagnostics carrying a given rule identifier."""
        return [d for d in self.diagnostics if d.rule_id == rule_id]

    def to_json(self, indent: Optional[int] = 2) -> str:
        """Render the diagnostics as JSON."""
        return diagnostics_to_json(self.diagnostics, indent=indent)


class StaticValidator:
    """Runs the frontend analyses together and merges their findings."""

    def __init__(
        self,
        profile: Optional[StaticProfile] = None,
        *,
        confidence_threshold: Optional[float] = None,
        reject_low_confidence: Optional[bool] = None,
        warnings_are_errors: Optional[bool] = None,
    ) -> None:
        """Configure the pass.

        The profile supplies the policy; the keyword arguments override
        individual parts of it, which is useful for a caller that wants one
        profile's stance on everything except a single setting.

        Args:
            profile: Validation policy. Defaults to the permissive profile.
            confidence_threshold: Inferred types below this are reported.
            reject_low_confidence: Whether weakly inferred types are fatal.
            warnings_are_errors: Whether non-fatal findings become failures.
        """
        self.profile = profile or DEFAULT_PROFILE
        self.confidence_threshold = (
            confidence_threshold if confidence_threshold is not None else self.profile.confidence_threshold
        )
        self.reject_low_confidence = (
            reject_low_confidence if reject_low_confidence is not None else self.profile.reject_low_confidence
        )
        self.warnings_are_errors = (
            warnings_are_errors if warnings_are_errors is not None else self.profile.warnings_are_errors
        )
        self.subset_validator = StaticPythonSubsetValidator()

    def validate_file(self, file_path: str) -> StaticValidationReport:
        """Validate a Python file."""
        with open(file_path, encoding="utf-8") as handle:
            return self.validate_code(handle.read())

    def validate_code(self, source_code: str) -> StaticValidationReport:
        """Validate source against every static analysis at once."""
        try:
            tree = ast.parse(source_code)
        except SyntaxError as error:
            # Nothing downstream can run without a tree, so stop here.
            span = SourceSpan(line=error.lineno, column=(error.offset or 1) - 1) if error.lineno else None
            return StaticValidationReport(
                is_valid=False,
                tier=SubsetTier.TIER_4_UNSUPPORTED,
                profile=self.profile,
                diagnostics=[
                    Diagnostic(
                        rule_id=RuleId.SYNTAX_ERROR,
                        severity=DiagnosticSeverity.ERROR,
                        message=f"Syntax error: {error}",
                        span=span,
                    )
                ],
            )

        subset = self.subset_validator.validate_ast(tree)

        diagnostics: list[Diagnostic] = list(subset.diagnostics)
        diagnostics.extend(self._analyzer_diagnostics(source_code))
        diagnostics.extend(self._constraint_diagnostics(source_code))
        diagnostics.extend(self._type_inference_diagnostics(tree))
        diagnostics.extend(self._profile_rejection_diagnostics(subset))

        # One sort gives the caller a report that reads top to bottom. Stable,
        # so same-position findings keep the order the analyses ran in, and
        # unpositioned findings trail the located ones rather than leading them.
        diagnostics = _deduplicate(diagnostics)
        diagnostics.sort(key=_source_order)

        if self.warnings_are_errors:
            # Promote after merging, so every producer is treated alike.
            diagnostics = [d if d.is_error else replace(d, severity=DiagnosticSeverity.ERROR) for d in diagnostics]

        return StaticValidationReport(
            is_valid=not any(d.is_error for d in diagnostics),
            tier=subset.tier,
            diagnostics=diagnostics,
            subset=subset,
            conversion_strategy=subset.conversion_strategy,
            profile=self.profile,
        )

    def _profile_rejection_diagnostics(self, subset: ValidationResult) -> list[Diagnostic]:
        """Report features this profile refuses regardless of declared status.

        A backend profile rejects what that backend was measured to refuse or
        silently discard. The declared status cannot express this: it has one
        value for every backend, so it has to describe the strictest.
        """
        rejected = self.profile.rejected_features
        if not rejected:
            return []

        rules = self.subset_validator.feature_rules
        diagnostics = []
        seen: set[tuple[str, Optional[int]]] = set()
        for key, span in subset.feature_uses:
            if key not in rejected:
                continue
            marker = (key, span.line if span else None)
            if marker in seen:
                continue
            seen.add(marker)
            rule = rules.get(key)
            name = rule.name if rule else key
            diagnostics.append(
                Diagnostic(
                    rule_id=RuleId.BACKEND_UNSUPPORTED,
                    severity=DiagnosticSeverity.ERROR,
                    message=f"The {self.profile.name} backend cannot translate: {name}",
                    span=span,
                    feature=name,
                    remediation=f"Avoid {name} when targeting {self.profile.name}.",
                    evidence={"profile": self.profile.name, "feature_key": key},
                )
            )
        return diagnostics

    def _analyzer_diagnostics(self, source_code: str) -> list[Diagnostic]:
        """Findings from the AST analyzer, which reports without positions."""
        # A fresh analyzer per call: it accumulates state across analyses.
        result = ASTAnalyzer().analyze(source_code)
        diagnostics = [
            Diagnostic(
                rule_id=RuleId.ANALYSIS_ERROR,
                severity=DiagnosticSeverity.ERROR,
                message=message,
            )
            for message in result.errors
        ]
        diagnostics.extend(
            Diagnostic(
                rule_id=RuleId.ANALYSIS_WARNING,
                severity=DiagnosticSeverity.WARNING,
                message=message,
            )
            for message in result.warnings
        )
        return diagnostics

    def _constraint_diagnostics(self, source_code: str) -> list[Diagnostic]:
        """Findings from the universal constraint checker."""
        violations: list[PythonConstraintViolation] = PythonConstraintChecker().check_code(source_code)
        return [
            Diagnostic(
                # The checker's own codes are stable; namespace them so they
                # cannot collide with STATIC.* identifiers.
                rule_id=f"{RuleId.CONSTRAINT_PREFIX}{violation.rule_id}",
                severity=_SEVERITY_BY_NAME.get(violation.severity, DiagnosticSeverity.WARNING),
                message=violation.message,
                span=SourceSpan(line=violation.line) if violation.line else None,
                feature=violation.category.value,
                remediation=violation.suggestion,
            )
            for violation in violations
        ]

    def _type_inference_diagnostics(self, tree: ast.AST) -> list[Diagnostic]:
        """Report names whose type could not be determined well enough.

        A construct can pass every syntactic rule and still be untranslatable
        because no type was established for it. Backends cannot emit a
        declaration for a type nobody knows.
        """
        engine = TypeInferenceEngine(enable_flow_sensitive=True)
        severity = DiagnosticSeverity.ERROR if self.reject_low_confidence else DiagnosticSeverity.WARNING
        diagnostics: list[Diagnostic] = []

        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            try:
                inferred: dict[str, Any] = engine.analyze_function_signature_enhanced(node)
            except Exception:
                # Inference is advisory here; its failure must not mask the
                # findings the other analyses already produced.
                continue

            for name, result in sorted(inferred.items()):
                confidence = getattr(result, "confidence", 1.0)
                if confidence >= self.confidence_threshold:
                    continue
                unknown = confidence <= 0.0
                diagnostics.append(
                    Diagnostic(
                        rule_id=RuleId.UNKNOWN_TYPE if unknown else RuleId.LOW_CONFIDENCE_TYPE,
                        severity=severity,
                        message=(
                            f"Type of '{name}' in '{node.name}' could not be determined"
                            if unknown
                            else f"Type of '{name}' in '{node.name}' is inferred with low confidence ({confidence:.2f})"
                        ),
                        span=SourceSpan.from_node(node),
                        node_type=type(node).__name__,
                        remediation=f"Annotate '{name}' explicitly.",
                        evidence={
                            "function": node.name,
                            "name": name,
                            "confidence": f"{confidence:.2f}",
                            "inferred_type": str(getattr(result, "python_type", "unknown")),
                        },
                    )
                )

        return diagnostics
