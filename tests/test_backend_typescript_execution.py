"""End-to-end execution tests for the TypeScript backend.

These compile generated TypeScript with Deno and compare runtime output to
CPython. They are skipped cleanly when Deno is not installed (mirroring the
ghc/ocaml gating used elsewhere).
"""

import runpy
import shutil
import subprocess
from pathlib import Path

import pytest

from multigen.backends.typescript.converter import MultiGenPythonToTypeScriptConverter

BENCH_DIR = Path(__file__).parent / "benchmarks"
RUNTIME = Path("src/multigen/backends/typescript/runtime/multigen_ts_runtime.ts")

BENCHMARKS = [
    "algorithms/fibonacci.py",
    "algorithms/quicksort.py",
    "algorithms/matmul.py",
    "algorithms/wordcount.py",
    "data_structures/list_ops.py",
    "data_structures/dict_ops.py",
    "data_structures/set_ops.py",
]

deno_available = shutil.which("deno") is not None
pytestmark = pytest.mark.skipif(not deno_available, reason="Deno not installed")


def _python_output(path: Path) -> str:
    """Run a benchmark's main() under CPython and capture stdout."""
    import io
    from contextlib import redirect_stdout

    ns = runpy.run_path(str(path))
    buf = io.StringIO()
    with redirect_stdout(buf):
        ns["main"]()
    return buf.getvalue().strip()


@pytest.mark.parametrize("rel", BENCHMARKS)
def test_benchmark_matches_cpython(rel, tmp_path):
    """Generated TypeScript runs under Deno and matches CPython output."""
    src = BENCH_DIR / rel
    converter = MultiGenPythonToTypeScriptConverter()
    ts_code = converter.convert_code(src.read_text())

    name = Path(rel).stem
    (tmp_path / f"{name}.ts").write_text(ts_code)
    shutil.copy2(RUNTIME, tmp_path / "multigen_ts_runtime.ts")

    result = subprocess.run(
        ["deno", "run", "--no-check", "--quiet", f"{name}.ts"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, f"Deno run failed: {result.stderr}"
    assert result.stdout.strip() == _python_output(src)
