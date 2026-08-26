"""Tests for measured backend capability and the profiles built from it."""

import json

import pytest

from multigen.backends.registry import registry
from multigen.frontend.backend_capabilities import (
    BUILD_FAILED,
    DROPS,
    MATCHES,
    MATRIX_PATH,
    OK,
    REFUSES,
    UNUSABLE,
    UNUSABLE_RUN,
    backend_profile,
    load_matrix,
    measure_backend,
    measure_emit,
)
from multigen.frontend.capability_probes import PROBES
from multigen.frontend.diagnostics import RuleId
from multigen.frontend.static_profile import get_profile, profile_names
from multigen.frontend.static_validation import StaticValidator
from multigen.frontend.subset_validator import StaticPythonSubsetValidator


class TestMatrixIsCurrent:
    """The checked-in measurement must match what the backends do now."""

    def test_recorded_emissions_match_a_fresh_measurement(self):
        """Run `make capabilities` after changing a backend or a probe.

        Only emission is re-measured here. Building and running every probe for
        every backend takes far too long for a unit test, and the build results
        are re-derived by the capabilities job in CI.
        """
        matrix = load_matrix()
        available = set(registry.list_backends())
        stale = {}

        for backend_name, outcomes in matrix.items():
            if backend_name not in available:
                # Not installed here, so nothing to compare against. The LLVM
                # backend is absent without llvmlite, which Python 3.14 excludes.
                continue
            for key, recorded in outcomes.items():
                actual = measure_emit(backend_name, PROBES[key].source, PROBES[key].marker)
                if actual != recorded["emit"]:
                    stale[f"{backend_name}/{key}"] = f"recorded {recorded['emit']}, measured {actual}"

        assert stale == {}, f"backend_capabilities.json is stale. Run `make capabilities`. {stale}"

    def test_every_cell_records_both_stages(self):
        """A cell without a run outcome would silently mean "emitted, untested"."""
        for backend_name, outcomes in load_matrix().items():
            for key, outcome in outcomes.items():
                assert set(outcome) == {"emit", "run"}, f"{backend_name}/{key}: {outcome}"

    def test_matrix_covers_every_available_backend(self):
        """Rows for a backend this interpreter lacks are kept, not required."""
        assert set(registry.list_backends()) <= set(load_matrix())

    def test_matrix_covers_every_probe(self):
        for backend_name, outcomes in load_matrix().items():
            assert set(outcomes) == set(PROBES), f"{backend_name} is missing rows"

    def test_every_probe_names_a_real_rule(self):
        rules = StaticPythonSubsetValidator().feature_rules

        assert set(PROBES) <= set(rules)

    def test_profiles_work_for_backends_not_installed_here(self):
        """Checking code against a target you cannot run locally is the point."""
        matrix = load_matrix()
        for backend_name in matrix:
            profile = get_profile(backend_name)
            assert profile.name == backend_name

    def test_matrix_is_written_deterministically(self):
        """Sorted keys, so regeneration produces no spurious diff."""
        payload = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))

        assert list(payload["backends"]) == sorted(payload["backends"])


class TestBackendProfiles:
    """A backend profile rejects exactly what the backend cannot translate."""

    def test_backends_are_selectable_as_profiles(self):
        for backend_name in registry.list_backends():
            assert backend_name in profile_names()
            assert get_profile(backend_name).name == backend_name

    def test_profile_rejects_what_the_matrix_marks_unusable(self):
        matrix = load_matrix()
        for backend_name, outcomes in matrix.items():
            expected = {
                key
                for key, outcome in outcomes.items()
                if outcome["emit"] in UNUSABLE or outcome["run"] in UNUSABLE_RUN
            }
            assert backend_profile(backend_name, matrix).rejected_features == expected

    def test_profile_accepts_what_the_matrix_marks_ok(self):
        matrix = load_matrix()
        for backend_name, outcomes in matrix.items():
            rejected = backend_profile(backend_name, matrix).rejected_features
            for key, outcome in outcomes.items():
                if outcome["emit"] == OK and outcome["run"] not in UNUSABLE_RUN:
                    assert key not in rejected

    def test_a_feature_one_backend_lacks_is_still_portable(self):
        """The portable profile must not inherit a single backend's limits."""
        source = 'def f(xs: list[int]) -> str:\n    return f"n={len(xs)}"\n'

        assert StaticValidator(get_profile("portable")).validate_code(source).is_valid
        assert StaticValidator(get_profile("c")).validate_code(source).is_valid

    def test_backend_rejection_is_positioned_and_identified(self):
        """LLVM handles neither generics nor f-strings; both must be reported."""
        source = 'def f(xs: list[int]) -> str:\n    return f"n={len(xs)}"\n'

        report = StaticValidator(get_profile("llvm")).validate_code(source)

        assert not report.is_valid
        rejections = report.by_rule(RuleId.BACKEND_UNSUPPORTED)
        assert {d.feature for d in rejections} == {"Generic Types", "F-Strings"}
        assert all(d.span is not None for d in rejections)


class TestMeasurementDistinguishesSilence:
    """A refusal and a silent drop are different outcomes."""

    def test_enums_are_dropped_not_refused_by_c(self):
        """The dangerous case: output produced with the members removed."""
        assert load_matrix()["c"]["enums"]["emit"] == DROPS

    def test_llvm_refuses_f_strings_rather_than_returning_null(self):
        """It used to compile f"..." to `ret i8* null`."""
        assert load_matrix()["llvm"]["f_strings"]["emit"] == REFUSES

    def test_running_finds_what_emitting_cannot(self):
        """Emission alone called these fine; the programs do not build.

        This is the whole reason the matrix builds and runs each probe.
        """
        matrix = load_matrix()
        emitted_but_broken = [
            f"{backend}/{key}"
            for backend, outcomes in matrix.items()
            for key, outcome in outcomes.items()
            if outcome["emit"] == OK and outcome["run"] == BUILD_FAILED
        ]

        assert emitted_but_broken, "expected the run stage to still be earning its keep"

    def test_measure_reports_ok_for_a_supported_feature(self):
        probe = PROBES["arithmetic_operations"]

        assert measure_emit("c", probe.source, probe.marker) == OK

    def test_c_arithmetic_builds_and_agrees_with_cpython(self):
        """The end-to-end claim the matrix now makes, checked directly."""
        outcomes = measure_backend("c")

        assert outcomes["arithmetic_operations"] == {"emit": OK, "run": MATCHES}
