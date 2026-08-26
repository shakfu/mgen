"""Programs that exercise one feature each, for measuring backend support.

A probe is a complete program: it computes an answer and prints it. That shape
lets the capability matrix do more than check that a backend emitted something
resembling the feature. It can build the generated program, run it, and compare
its output with what CPython produces for the same source.

The distinction matters. Exception handling was declared fully supported and the
matrix agreed, because the C backend emitted plausible source. The source did
not compile. Only running it revealed that, and only after it compiled did the
next divergence appear: `10 // 0` inside a `try` dies of SIGFPE rather than
reaching the handler.

Each probe defines `compute()` returning an integer answer and `main()` printing
it, so a single harness works for every backend. `marker` is a fragment that
must survive into the generated source; its absence means the feature was
silently discarded, which a program that still runs cannot reveal.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Probe:
    """A single-feature program and the evidence it should leave behind."""

    source: str
    marker: str


def _program(body: str, marker: str) -> Probe:
    """Wrap a feature fragment in the standard compute/main shape."""
    return Probe(source=body + "\n\ndef main() -> int:\n    print(compute())\n    return 0\n", marker=marker)


PROBES: dict[str, Probe] = {
    "basic_types": _program(
        "def compute() -> int:\n"
        "    count: int = 3\n"
        "    ratio: float = 2.5\n"
        "    flag: bool = True\n"
        "    if flag:\n"
        "        return count\n"
        "    return 0\n",
        "ratio",
    ),
    "function_definitions": _program(
        "def add(x: int, y: int) -> int:\n    return x + y\n\n\ndef compute() -> int:\n    return add(4, 6)\n",
        "add",
    ),
    "variable_declarations": _program(
        "def compute() -> int:\n    counter: int = 10\n    return counter\n",
        "counter",
    ),
    "control_flow": _program(
        "def compute() -> int:\n"
        "    total: int = 0\n"
        "    for i in range(5):\n"
        "        if i > 1:\n"
        "            total += i\n"
        "    while total > 100:\n"
        "        total -= 1\n"
        "    return total\n",
        "total",
    ),
    "arithmetic_operations": _program(
        "def compute() -> int:\n    a: int = 7\n    b: int = 3\n    return a * b - a + b\n",
        "compute",
    ),
    "f_strings": _program(
        'def compute() -> int:\n    x: int = 42\n    label: str = f"value={x}"\n    return len(label)\n',
        "value=",
    ),
    "enums": _program(
        "from enum import Enum\n\n\nclass Colour(Enum):\n    RED = 0\n    GREEN = 7\n\n\ndef compute() -> int:\n    return 7\n",
        "GREEN",
    ),
    "dataclasses": _program(
        "from dataclasses import dataclass\n\n\n@dataclass\nclass Point:\n    x: int\n    y: int\n\n\n"
        "def compute() -> int:\n    p: Point = Point(4, 6)\n    return p.x + p.y\n",
        "Point",
    ),
    "tuples": _program(
        "def compute() -> int:\n    pair: tuple[int, int] = (4, 6)\n    return pair[0] + pair[1]\n",
        "4",
    ),
    "namedtuples": _program(
        "from typing import NamedTuple\n\n\nclass Point(NamedTuple):\n    x: int\n    y: int\n\n\n"
        "def compute() -> int:\n    p: Point = Point(4, 6)\n    return p.x + p.y\n",
        "Point",
    ),
    "lists": _program(
        "def compute() -> int:\n    items: list[int] = [1, 2, 3, 4]\n    return len(items)\n",
        "items",
    ),
    "union_types": _program(
        "from typing import Union\n\n\ndef pick(x: Union[int, float]) -> int:\n    return 5\n\n\n"
        "def compute() -> int:\n    return pick(1)\n",
        "pick",
    ),
    "pattern_matching": _program(
        "def classify(x: int) -> int:\n    match x:\n        case 1:\n            return 10\n    return 0\n\n\n"
        "def compute() -> int:\n    return classify(1)\n",
        "10",
    ),
    "generators": _program(
        "def counter(n: int) -> int:\n    i: int = 0\n    while i < n:\n        yield i\n        i += 1\n\n\n"
        "def compute() -> int:\n    total: int = 0\n    for v in counter(5):\n        total += v\n    return total\n",
        "counter",
    ),
    "yield_from": _program(
        "def inner(n: int) -> int:\n    i: int = 0\n    while i < n:\n        yield i\n        i += 1\n\n\n"
        "def outer(n: int) -> int:\n    yield from inner(n)\n\n\n"
        "def compute() -> int:\n    total: int = 0\n    for v in outer(4):\n        total += v\n    return total\n",
        "outer",
    ),
    "generator_expressions": _program(
        "def compute() -> int:\n    items: list[int] = [1, 2, 3]\n    return sum(x * 2 for x in items)\n",
        "compute",
    ),
    "generics": _program(
        "def measure(items: list[int], table: dict[str, int]) -> int:\n    return len(items) + len(table)\n\n\n"
        "def compute() -> int:\n    values: list[int] = [1, 2, 3]\n    lookup: dict[str, int] = {}\n"
        "    return measure(values, lookup)\n",
        "items",
    ),
    "function_calls": _program(
        "def helper(x: int) -> int:\n    return x * 2\n\n\ndef compute() -> int:\n    return helper(5)\n",
        "helper",
    ),
    "comprehensions": _program(
        "def compute() -> int:\n    items: list[int] = [1, 2, 3]\n    doubled: list[int] = [x * 2 for x in items]\n"
        "    return len(doubled)\n",
        "doubled",
    ),
    "exceptions": _program(
        "def guarded(x: int) -> int:\n"
        "    try:\n"
        "        if x == 0:\n"
        "            raise ValueError('zero')\n"
        "        return x\n"
        "    except ValueError:\n"
        "        return -1\n\n\n"
        "def compute() -> int:\n    return guarded(0)\n",
        "guarded",
    ),
    "context_managers": _program(
        "def compute() -> int:\n    total: int = 0\n    with open('/dev/null') as handle:\n        total = 9\n    return total\n",
        "handle",
    ),
}

# Establishes whether a toolchain works at all here. If this fails to build, the
# backend is unverifiable in this environment and every feature-level build
# failure would be an artefact of the environment rather than a real limitation.
BASELINE = _program("def compute() -> int:\n    return 3 + 4\n", "compute")


def get_probe(rule_key: str) -> Optional[Probe]:
    """Return the probe for a rule, if one exists."""
    return PROBES.get(rule_key)
