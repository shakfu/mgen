"""Tests for the multigen check CLI command."""

import json
import subprocess
import sys

import pytest


def _check(*args: str) -> int:
    return subprocess.run(
        [sys.executable, "-m", "multigen.cli.main", "check", *args],
        capture_output=True,
        text=True,
    ).returncode


class TestCheckCommand:
    """Exit codes must never report success for unvalidated input."""

    def test_report_alone_succeeds(self):
        """--report describes the subset and needs no input file."""
        assert _check("--report") == 0

    def test_report_does_not_excuse_a_missing_file(self, tmp_path):
        """--report used to short-circuit, exiting 0 for a nonexistent file."""
        assert _check("--report", str(tmp_path / "nope.py")) == 1

    def test_report_does_not_excuse_an_invalid_file(self, tmp_path):
        """--report must still validate the files it was given."""
        source = tmp_path / "bad.py"
        source.write_text("async def f(x: int) -> int:\n    return x\n")
        assert _check("--report", str(source)) == 1

    def test_valid_file_succeeds(self, tmp_path):
        source = tmp_path / "good.py"
        source.write_text("def add(x: int, y: int) -> int:\n    return x + y\n")
        assert _check(str(source)) == 0

    def test_no_arguments_fails(self):
        """Neither files nor --report means nothing was validated."""
        assert _check() == 1


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "multigen.cli.main", "check", *args],
        capture_output=True,
        text=True,
    )


class TestCheckProfiles:
    """The profile decides the exit code for the same file."""

    # See tests/test_static_profile.py for why this construct and not generics.
    SOURCE = "from typing import Union\n\n\ndef pick(x: Union[int, float]) -> int:\n    return 1\n"

    @pytest.fixture
    def program(self, tmp_path):
        path = tmp_path / "p.py"
        path.write_text(self.SOURCE)
        return str(path)

    def test_portable_accepts(self, program):
        assert _run(program).returncode == 0

    def test_strict_static_rejects(self, program):
        assert _run("--profile", "strict-static", program).returncode == 1

    def test_unknown_profile_is_a_usage_error(self, program):
        assert _run("--profile", "nonexistent", program).returncode == 2

    def test_warnings_as_errors_promotes_findings(self, program):
        assert _run(program).returncode == 0
        assert _run("--warnings-as-errors", program).returncode == 1

    def test_json_output_is_parseable(self, program):
        result = _run("--format", "json", "--profile", "strict-static", program)

        payload = json.loads(result.stdout)
        assert payload["profile"] == "strict-static"
        assert payload["files"][0]["valid"] is False
        assert payload["files"][0]["diagnostics"]

    def test_json_reports_a_missing_file_without_crashing(self, tmp_path):
        result = _run("--format", "json", str(tmp_path / "nope.py"))

        payload = json.loads(result.stdout)
        assert result.returncode == 1
        assert payload["files"][0]["error"] == "file not found"
