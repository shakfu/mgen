"""Tests for validation profiles."""

import pytest

from multigen.frontend.static_profile import (
    DEFAULT_PROFILE,
    PORTABLE,
    STRICT_STATIC,
    get_profile,
    profile_names,
)
from multigen.frontend.static_validation import StaticValidator

# Union is the remaining experimental construct, and the parameter's type
# cannot be pinned down, so this exercises both policy switches. Do not
# substitute a construct whose status may change: that is what broke these
# tests when generics were reclassified.
UNCERTAIN_CODE = "from typing import Union\n\n\ndef pick(x: Union[int, float]) -> int:\n    return 1\n"


class TestProfileRegistry:
    """Looking profiles up by name."""

    def test_default_is_permissive(self):
        assert DEFAULT_PROFILE is PORTABLE
        assert not PORTABLE.reject_low_confidence
        assert not PORTABLE.warnings_are_errors

    def test_strict_static_rejects_uncertainty(self):
        assert STRICT_STATIC.reject_low_confidence
        assert STRICT_STATIC.warnings_are_errors

    def test_names_cover_policies_and_backends(self):
        """Every backend is selectable by name, alongside the policy profiles.

        Asserted against the registry rather than a literal list, so adding a
        backend does not require editing this test.
        """
        from multigen.backends.registry import registry

        names = profile_names()

        assert {"portable", "strict-static"} <= set(names)
        assert set(registry.list_backends()) <= set(names)
        assert names == sorted(names)

    def test_none_selects_the_default(self):
        assert get_profile(None) is DEFAULT_PROFILE

    def test_unknown_name_is_rejected_with_the_alternatives(self):
        with pytest.raises(ValueError, match="portable"):
            get_profile("nonexistent")


class TestProfileApplication:
    """The same source, judged differently."""

    def test_profile_decides_validity(self):
        portable = StaticValidator(PORTABLE).validate_code(UNCERTAIN_CODE)
        strict = StaticValidator(STRICT_STATIC).validate_code(UNCERTAIN_CODE)

        assert portable.is_valid
        assert not strict.is_valid
        # Same findings either way; only their severity differs.
        assert {d.rule_id for d in portable.diagnostics} <= {d.rule_id for d in strict.diagnostics}

    def test_report_records_its_profile(self):
        report = StaticValidator(STRICT_STATIC).validate_code(UNCERTAIN_CODE)

        assert report.profile is STRICT_STATIC
        assert report.profile_name == "strict-static"

    def test_keyword_arguments_override_the_profile(self):
        """A caller can take a profile's stance on all but one setting."""
        relaxed = StaticValidator(STRICT_STATIC, warnings_are_errors=False, reject_low_confidence=False)

        assert relaxed.validate_code(UNCERTAIN_CODE).is_valid

    def test_portable_accepts_the_translation_corpus(self):
        """The default profile must not reject what the backends translate."""
        import glob

        validator = StaticValidator(PORTABLE)
        offenders = {}
        for path in sorted(glob.glob("tests/translation/*.py")):
            report = validator.validate_code(open(path, encoding="utf-8").read())
            if not report.is_valid:
                offenders[path] = report.violations

        assert offenders == {}
