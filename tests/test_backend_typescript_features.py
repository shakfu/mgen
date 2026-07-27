"""Tests for TypeScript backend containers, OOP, comprehensions, and control flow."""

from multigen.backends.typescript.converter import MultiGenPythonToTypeScriptConverter


class TestTypeScriptContainers:
    """Test container literal and type mapping."""

    def setup_method(self):
        self.converter = MultiGenPythonToTypeScriptConverter()

    def test_list_literal_and_type(self):
        python_code = """
def make_list() -> list:
    xs: list[int] = [1, 2, 3]
    return xs
"""
        ts_code = self.converter.convert_code(python_code)
        assert "let xs: number[] = [1, 2, 3];" in ts_code

    def test_dict_literal_uses_map(self):
        python_code = """
def make_dict() -> dict:
    d: dict[str, int] = {"a": 1}
    return d
"""
        ts_code = self.converter.convert_code(python_code)
        assert "Map<string, number>" in ts_code
        assert 'new Map([["a", 1]])' in ts_code

    def test_set_literal_uses_set(self):
        python_code = """
def make_set() -> set:
    s: set[int] = {1, 2, 3}
    return s
"""
        ts_code = self.converter.convert_code(python_code)
        assert "Set<number>" in ts_code
        assert "new Set([1, 2, 3])" in ts_code

    def test_subscript_assign_on_map_uses_set_method(self):
        python_code = """
def fill() -> dict:
    d: dict[str, int] = {}
    d["a"] = 1
    return d
"""
        ts_code = self.converter.convert_code(python_code)
        assert 'd.set("a", 1);' in ts_code

    def test_membership_on_map_uses_has(self):
        python_code = """
def check(d: dict) -> bool:
    return 1 in d
"""
        ts_code = self.converter.convert_code(python_code)
        assert "d.has(1)" in ts_code

    def test_membership_on_list_uses_includes(self):
        python_code = """
def check(xs: list) -> bool:
    return 1 in xs
"""
        ts_code = self.converter.convert_code(python_code)
        assert "xs.includes(1)" in ts_code


class TestTypeScriptComprehensions:
    """Test comprehension conversion to array methods."""

    def setup_method(self):
        self.converter = MultiGenPythonToTypeScriptConverter()

    def test_list_comprehension_over_range(self):
        python_code = """
def squares() -> list:
    return [x * x for x in range(10)]
"""
        ts_code = self.converter.convert_code(python_code)
        assert "mg.range(10).map((x) => (x * x))" in ts_code

    def test_list_comprehension_with_filter(self):
        python_code = """
def evens() -> list:
    return [x for x in range(10) if x % 2 == 0]
"""
        ts_code = self.converter.convert_code(python_code)
        assert ".filter((x) =>" in ts_code
        assert "mg.pyMod(x, 2)" in ts_code

    def test_dict_comprehension(self):
        python_code = """
def build() -> dict:
    return {x: x * 2 for x in range(5)}
"""
        ts_code = self.converter.convert_code(python_code)
        assert "new Map(mg.range(5).map((x) => [x, (x * 2)]))" in ts_code

    def test_set_comprehension(self):
        python_code = """
def build() -> set:
    return {x for x in range(5)}
"""
        ts_code = self.converter.convert_code(python_code)
        assert "new Set(mg.range(5).map((x) => x))" in ts_code

    def test_set_comprehension_over_set_spreads(self):
        """Set has no array methods; source must be spread to an array."""
        python_code = """
def build() -> set:
    numbers: set = {1, 2, 3}
    return {x for x in numbers if x > 1}
"""
        ts_code = self.converter.convert_code(python_code)
        assert "[...numbers]" in ts_code


class TestTypeScriptOOP:
    """Test class conversion to TypeScript classes."""

    def setup_method(self):
        self.converter = MultiGenPythonToTypeScriptConverter()

    def test_class_with_constructor(self):
        python_code = """
class Counter:
    def __init__(self, start: int):
        self.count: int = start

    def increment(self) -> None:
        self.count = self.count + 1

    def get(self) -> int:
        return self.count
"""
        ts_code = self.converter.convert_code(python_code)
        assert "class Counter {" in ts_code
        assert "count: number;" in ts_code
        assert "constructor(start: number)" in ts_code
        assert "this.count = start;" in ts_code
        assert "increment(): void" in ts_code
        assert "this.count = (this.count + 1);" in ts_code

    def test_constructor_call_uses_new(self):
        python_code = """
class Point:
    def __init__(self, x: int):
        self.x: int = x

def make() -> Point:
    return Point(5)
"""
        ts_code = self.converter.convert_code(python_code)
        assert "new Point(5)" in ts_code


class TestTypeScriptControlFlow:
    """Test exception handling, with-statements, and generators."""

    def setup_method(self):
        self.converter = MultiGenPythonToTypeScriptConverter()

    def test_raise_uses_runtime_error_class(self):
        python_code = """
def check(x: int) -> int:
    if x < 0:
        raise ValueError("negative")
    return x
"""
        ts_code = self.converter.convert_code(python_code)
        assert 'throw new mg.ValueError("negative");' in ts_code

    def test_try_except_uses_instanceof(self):
        python_code = """
def safe() -> int:
    try:
        return 1
    except ValueError:
        return 0
"""
        ts_code = self.converter.convert_code(python_code)
        assert "try {" in ts_code
        assert "catch (__e)" in ts_code
        assert "__e instanceof mg.ValueError" in ts_code

    def test_generator_collects_to_array(self):
        python_code = """
def gen(n: int) -> int:
    for i in range(n):
        yield i
"""
        ts_code = self.converter.convert_code(python_code)
        assert "let __mgen_result: number[] = [];" in ts_code
        assert "__mgen_result.push(i);" in ts_code
        assert "return __mgen_result;" in ts_code

    def test_fstring_uses_template_literal(self):
        python_code = """
def greet(name: str) -> str:
    return f"Hello {name}"
"""
        ts_code = self.converter.convert_code(python_code)
        assert "`Hello ${mg.toStr(name)}`" in ts_code
