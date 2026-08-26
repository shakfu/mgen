"""What each backend actually does with each feature.

The declared `FeatureStatus` on a rule is a portable claim: it has to pick one
answer for every backend, so it lands on the strictest one. That is why `global`
is rejected although the LLVM backend handles it, and why generics spent a
release marked experimental although four backends emit idiomatic containers.

This module carries the per-backend answer instead, measured by running each
rule's probe through each emitter rather than asserted in prose. Three outcomes
matter:

- `ok`: the feature survives into the generated output.
- `refuses`: the backend raises, which is honest and safe.
- `drops`: output is produced with the feature quietly removed. This is the
  dangerous one, and the reason a refusal cannot be assumed from silence.

The matrix is generated (`make capabilities`) and checked in, because probing
eight backends on every validation would be far too slow. A test regenerates and
compares, so the data cannot drift from the code it describes.
"""

import contextlib
import io
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Optional

from .capability_probes import BASELINE, PROBES
from .static_profile import DEFAULT_CONFIDENCE_THRESHOLD, StaticProfile

MATRIX_PATH = Path(__file__).with_name("backend_capabilities.json")

# What happened when the backend was asked to emit the feature.
OK = "ok"
REFUSES = "refuses"
DROPS = "drops"
ERROR = "error"

# What happened when the emitted program was built and run.
MATCHES = "matches"
MISMATCH = "mismatch"
BUILD_FAILED = "build_failed"
CRASHED = "crashed"
HANGS = "hangs"
SKIPPED = "skipped"  # Nothing was emitted, so there was nothing to run.
UNVERIFIED = "unverified"  # No working toolchain here; absence of evidence.

# Emit outcomes that mean the feature must not be handed to this backend.
UNUSABLE = frozenset({REFUSES, DROPS, ERROR})
# Run outcomes that condemn a feature. UNVERIFIED deliberately does not: an
# absent compiler is a fact about this machine, not about the backend.
UNUSABLE_RUN = frozenset({MISMATCH, BUILD_FAILED, CRASHED, HANGS})

BUILD_TIMEOUT_SECONDS = 120
RUN_TIMEOUT_SECONDS = 15


def load_matrix(path: Optional[Path] = None) -> dict[str, dict[str, dict[str, str]]]:
    """Load the matrix as {backend: {rule key: {"emit": ..., "run": ...}}}."""
    source = path or MATRIX_PATH
    if not source.exists():
        return {}
    data = json.loads(source.read_text(encoding="utf-8"))
    backends: dict[str, dict[str, dict[str, str]]] = data.get("backends", {})
    return backends


def python_answer(source: str) -> str:
    """What CPython prints for this program, as the reference to match."""
    namespace: dict[str, Any] = {}
    exec(compile(source, "<probe>", "exec"), namespace)  # noqa: S102 - our own probes
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        namespace["main"]()
    return buffer.getvalue().strip()


def run_probe(backend_name: str, source: str) -> str:
    """Build the generated program and compare its output with CPython's.

    Returns one of the run outcomes. A build or run failure here is attributed
    to the feature only when the backend's baseline probe builds; see
    `measure_backend`.
    """
    from ..pipeline import BuildMode, MultiGenPipeline, PipelineConfig

    with tempfile.TemporaryDirectory() as workdir:
        directory = Path(workdir)
        program = directory / "probe.py"
        program.write_text(source, encoding="utf-8")

        config = PipelineConfig(
            target_language=backend_name,
            build_mode=BuildMode.DIRECT,
            output_dir=str(directory / "out"),
            enable_advanced_analysis=False,
        )
        try:
            result = MultiGenPipeline(config=config).convert(program)
        except Exception:  # noqa: BLE001 - any failure is a failure to build
            return BUILD_FAILED
        if not result.success or not result.executable_path:
            return BUILD_FAILED

        try:
            completed = subprocess.run(  # noqa: S603 - executing our own build
                [result.executable_path],
                capture_output=True,
                text=True,
                timeout=RUN_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            return HANGS
        except OSError:
            return BUILD_FAILED

        if completed.returncode != 0:
            return CRASHED
        return MATCHES if completed.stdout.strip() == python_answer(source) else MISMATCH


def measure_emit(backend_name: str, source: str, marker: str) -> str:
    """Ask one backend to emit one probe and classify what came back.

    Kept here rather than in the generator script so the drift test measures
    exactly what the checked-in data claims to be a measurement of.
    """
    from ..backends.registry import registry

    try:
        emitted = registry.get_backend(backend_name).get_emitter().emit_module(source, None)
    except Exception as exc:  # noqa: BLE001 - any failure is a non-translation
        name = type(exc).__name__
        return REFUSES if name == "UnsupportedFeatureError" else ERROR
    return OK if marker.lower() in emitted.lower() else DROPS


def measure_backend(
    backend_name: str, recorded: Optional[dict[str, dict[str, str]]] = None
) -> dict[str, dict[str, str]]:
    """Measure every probe against one backend.

    The baseline decides whether run results mean anything here. If a trivial
    program will not build, this machine lacks the toolchain, and every
    feature-level build failure would say more about the machine than about the
    backend.

    When a run cannot be verified, a previously recorded verdict is carried
    forward rather than replaced with `unverified`. Toolchains differ between
    a developer's machine and a CI runner, and without this the matrix would
    flip back and forth depending on where it was last generated.
    """
    baseline_emit = measure_emit(backend_name, BASELINE.source, BASELINE.marker)
    runnable = baseline_emit == OK and run_probe(backend_name, BASELINE.source) == MATCHES
    previous = recorded or {}

    outcomes: dict[str, dict[str, str]] = {}
    for rule_key, probe in sorted(PROBES.items()):
        emit = measure_emit(backend_name, probe.source, probe.marker)
        if emit != OK:
            run = SKIPPED
        elif runnable:
            run = run_probe(backend_name, probe.source)
        else:
            was = previous.get(rule_key, {}).get("run", UNVERIFIED)
            run = was if was not in (SKIPPED, UNVERIFIED) else UNVERIFIED
        outcomes[rule_key] = {"emit": emit, "run": run}
    return outcomes


def unusable_features(
    backend_name: str, matrix: Optional[dict[str, dict[str, dict[str, str]]]] = None
) -> frozenset[str]:
    """Rule keys this backend cannot translate.

    A feature is unusable when the backend will not emit it, or when the program
    it emits does not build, crashes, hangs, or disagrees with CPython. A run
    that could not be verified here is not held against it.
    """
    table = (matrix if matrix is not None else load_matrix()).get(backend_name, {})
    return frozenset(
        key for key, outcome in table.items() if outcome.get("emit") in UNUSABLE or outcome.get("run") in UNUSABLE_RUN
    )


def backend_profile(backend_name: str, matrix: Optional[dict[str, dict[str, dict[str, str]]]] = None) -> StaticProfile:
    """Build a validation profile describing one backend.

    The profile rejects exactly what the measurement says this backend cannot
    translate, so it never claims support the backend does not have.
    """
    rejected = unusable_features(backend_name, matrix)
    return StaticProfile(
        name=backend_name,
        description=(
            f"What the {backend_name} backend can actually translate, measured from its own output. "
            f"Rejects {len(rejected)} feature(s) the backend refuses or silently discards."
        ),
        reject_low_confidence=False,
        confidence_threshold=DEFAULT_CONFIDENCE_THRESHOLD,
        warnings_are_errors=False,
        rejected_features=rejected,
    )


def backend_profile_names(matrix: Optional[dict[str, dict[str, dict[str, str]]]] = None) -> list[str]:
    """Backends the matrix covers, in a stable order."""
    return sorted(matrix if matrix is not None else load_matrix())
