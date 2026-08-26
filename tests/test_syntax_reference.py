"""The generated syntax reference must match the registry it describes."""

from pathlib import Path

import pytest

from multigen.frontend.static_profile import PORTABLE, STRICT_STATIC
from multigen.frontend.subset_validator import FeatureStatus, StaticPythonSubsetValidator
from multigen.frontend.syntax_reference import (
    ACCEPTED,
    BEGIN_MARKER,
    END_MARKER,
    REJECTED,
    WARNED,
    profile_disposition,
    render_document,
    render_feature_support,
)

DOC_PATH = Path(__file__).resolve().parent.parent / "docs" / "supported_syntax.md"


class TestDocumentIsCurrent:
    """Staleness is a build failure, not something to discover later."""

    def test_checked_in_document_matches_the_registry(self):
        """Run `make docs-syntax` after changing a feature rule or profile."""
        existing = DOC_PATH.read_text(encoding="utf-8")

        assert render_document(existing) == existing, (
            "docs/supported_syntax.md is out of date with the feature registry. Run `make docs-syntax`."
        )

    def test_document_carries_both_markers(self):
        text = DOC_PATH.read_text(encoding="utf-8")

        assert text.count(BEGIN_MARKER) == 1
        assert text.count(END_MARKER) == 1

    def test_every_rule_appears(self):
        """A rule that no table row mentions is a rule nobody can discover."""
        block = render_feature_support()

        for rule in StaticPythonSubsetValidator().feature_rules.values():
            assert rule.name in block, f"{rule.name} missing from the generated reference"


class TestProfileDisposition:
    """The table's per-profile columns follow the profile policy."""

    @pytest.mark.parametrize(
        "status,portable,strict",
        [
            (FeatureStatus.FULLY_SUPPORTED, ACCEPTED, ACCEPTED),
            (FeatureStatus.PARTIALLY_SUPPORTED, ACCEPTED, ACCEPTED),
            (FeatureStatus.EXPERIMENTAL, WARNED, REJECTED),
            (FeatureStatus.PLANNED, REJECTED, REJECTED),
            (FeatureStatus.NOT_SUPPORTED, REJECTED, REJECTED),
        ],
    )
    def test_disposition_matches_policy(self, status, portable, strict):
        assert profile_disposition(status, PORTABLE) == portable
        assert profile_disposition(status, STRICT_STATIC) == strict

    def test_documented_disposition_matches_the_validator(self):
        """The table must not promise something the validator does not do."""
        validator = StaticPythonSubsetValidator()
        # Lambda is NOT_SUPPORTED, so both profiles must reject it.
        result = validator.validate_code("def f() -> int:\n    g = lambda x: x\n    return 0\n")

        assert profile_disposition(validator.feature_rules["lambda_functions"].status, PORTABLE) == REJECTED
        assert not result.is_valid


class TestRenderDocument:
    """Refreshing the block must not corrupt the surrounding prose."""

    def test_prose_is_preserved(self):
        document = f"# Title\n\nIntro paragraph.\n\n{BEGIN_MARKER}\nstale\n{END_MARKER}\n\nTrailing prose.\n"

        updated = render_document(document)

        assert updated.startswith("# Title\n\nIntro paragraph.")
        assert updated.endswith("Trailing prose.\n")
        assert "stale" not in updated

    def test_regeneration_is_idempotent(self):
        document = f"# Title\n\n{BEGIN_MARKER}\nstale\n{END_MARKER}\n"

        once = render_document(document)

        assert render_document(once) == once

    def test_a_lone_marker_is_refused(self):
        """Guessing where the block ends would append a second copy."""
        with pytest.raises(ValueError, match="one generation marker"):
            render_document(f"# Title\n\n{BEGIN_MARKER}\nstale\n")
