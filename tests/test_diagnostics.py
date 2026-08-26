"""Tests for structured validation diagnostics."""

import json

import pytest

from multigen.frontend.diagnostics import (
    Diagnostic,
    DiagnosticSeverity,
    RuleId,
    SourceSpan,
    diagnostics_to_json,
)
from multigen.frontend.subset_validator import StaticPythonSubsetValidator


class TestDiagnostic:
    """The diagnostic value type."""

    def test_format_reads_as_a_compiler_diagnostic(self):
        diagnostic = Diagnostic(
            rule_id=RuleId.UNANNOTATED_PARAMETER,
            severity=DiagnosticSeverity.ERROR,
            message="parameter 'x' is missing type annotation",
            span=SourceSpan(line=3, column=10),
        )

        rendered = diagnostic.format("prog.py")

        assert rendered == (
            "prog.py:3:10: error: [STATIC.UNANNOTATED_PARAMETER] parameter 'x' is missing type annotation"
        )

    def test_to_dict_is_json_serialisable(self):
        diagnostic = Diagnostic(
            rule_id=RuleId.UNSUPPORTED_FEATURE,
            severity=DiagnosticSeverity.WARNING,
            message="Experimental",
            span=SourceSpan(line=1, column=0, end_line=1, end_column=4),
            node_type="Subscript",
            feature="Generic Types",
            remediation="Avoid it",
            evidence={"identifier": "T"},
        )

        payload = json.loads(diagnostics_to_json([diagnostic]))[0]

        assert payload["rule_id"] == RuleId.UNSUPPORTED_FEATURE
        assert payload["severity"] == "warning"
        assert payload["span"] == {"line": 1, "column": 0, "end_line": 1, "end_column": 4}
        assert payload["evidence"] == {"identifier": "T"}

    def test_optional_fields_are_omitted(self):
        payload = Diagnostic(
            rule_id=RuleId.SYNTAX_ERROR,
            severity=DiagnosticSeverity.ERROR,
            message="boom",
        ).to_dict()

        assert set(payload) == {"rule_id", "severity", "message"}


class TestValidatorDiagnostics:
    """The validator reports diagnostics, and the string views derive from them."""

    def test_string_views_derive_from_diagnostics(self):
        """violations and warnings cannot drift from the diagnostics."""
        code = "def f(x, y: int) -> int:\n    return x + y\n"

        result = StaticPythonSubsetValidator().validate_code(code)

        assert result.violations == [d.message for d in result.diagnostics if d.is_error]
        assert result.warnings == [d.message for d in result.diagnostics if not d.is_error]

    @pytest.mark.parametrize(
        "code,rule_id",
        [
            ("def f(x) -> int:\n    return x\n", RuleId.UNANNOTATED_PARAMETER),
            ("def f(x: int):\n    return x\n", RuleId.MISSING_RETURN_ANNOTATION),
            ("@weird\ndef f(x: int) -> int:\n    return x\n", RuleId.UNSUPPORTED_DECORATOR),
            ("async def f(x: int) -> int:\n    return x\n", RuleId.UNRECOGNIZED_CONSTRUCT),
            ("from enum import Enum\n\n\nclass S(Enum):\n    A = 0\n", RuleId.FEATURE_NOT_IMPLEMENTED),
            ("def f() -> int:\n    g = lambda x: x\n    return 0\n", RuleId.UNSUPPORTED_FEATURE),
            ('def f(x: int) -> str:\n    return f"{x!r}"\n', RuleId.FSTRING_CONVERSION_FLAG),
            ("def f(x: int) -> int:\n    return (\n", RuleId.SYNTAX_ERROR),
        ],
    )
    def test_rule_ids_are_stable_and_specific(self, code, rule_id):
        """Each failure mode has its own identifier, not one generic string."""
        result = StaticPythonSubsetValidator().validate_code(code)

        assert not result.is_valid
        assert rule_id in {d.rule_id for d in result.diagnostics}

    def test_diagnostics_carry_positions(self):
        code = "def ok(x: int) -> int:\n    return x\n\n\ndef bad(y) -> int:\n    return y\n"

        result = StaticPythonSubsetValidator().validate_code(code)

        (diagnostic,) = [d for d in result.diagnostics if d.rule_id == RuleId.UNANNOTATED_PARAMETER]
        assert diagnostic.span is not None
        assert diagnostic.span.line == 5
        assert diagnostic.evidence == {"function": "bad", "parameter": "y"}

    def test_diagnostics_are_reported_in_source_order(self):
        """ast.walk is breadth-first; the report must still read top to bottom."""
        code = (
            "def a(p) -> int:\n"
            "    return p\n"
            "\n"
            "\n"
            "async def b(n: int) -> int:\n"
            "    return n\n"
            "\n"
            "\n"
            "def c(q) -> int:\n"
            "    return q\n"
        )

        result = StaticPythonSubsetValidator().validate_code(code)

        lines = [d.span.line for d in result.diagnostics if d.span]
        assert lines == sorted(lines)

    def test_remediation_is_offered(self):
        result = StaticPythonSubsetValidator().validate_code("def f(x) -> int:\n    return x\n")

        (diagnostic,) = [d for d in result.diagnostics if d.rule_id == RuleId.UNANNOTATED_PARAMETER]
        assert diagnostic.remediation == "Annotate the parameter, for example `x: int`."
