"""Tests for basic TypeScript backend functionality."""

from multigen.backends.typescript.converter import MultiGenPythonToTypeScriptConverter


class TestTypeScriptBasicsConversion:
    """Test basic conversion functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.converter = MultiGenPythonToTypeScriptConverter()

    def test_simple_function_conversion(self):
        """Test simple function with type annotations."""
        python_code = """
def add_numbers(a: int, b: int) -> int:
    return a + b
"""
        ts_code = self.converter.convert_code(python_code)

        assert "function add_numbers(a: number, b: number): number" in ts_code
        assert "return (a + b);" in ts_code
        assert 'import * as mg from "./multigen_ts_runtime.ts";' in ts_code

    def test_function_with_string_parameters(self):
        """Test function with string parameters."""
        python_code = """
def greet(name: str) -> str:
    return "Hello " + name
"""
        ts_code = self.converter.convert_code(python_code)

        assert "function greet(name: string): string" in ts_code
        assert 'return ("Hello " + name);' in ts_code

    def test_function_with_multiple_types(self):
        """Test function with various parameter types."""
        python_code = """
def process(count: int, rate: float, active: bool, name: str) -> str:
    return name
"""
        ts_code = self.converter.convert_code(python_code)

        assert "function process(count: number, rate: number, active: boolean, name: string): string" in ts_code

    def test_void_return_function(self):
        """Test function with no return value."""
        python_code = """
def print_message(msg: str) -> None:
    print(msg)
"""
        ts_code = self.converter.convert_code(python_code)

        assert "function print_message(msg: string): void" in ts_code
        assert "mg.print(msg);" in ts_code

    def test_auto_type_inference(self):
        """Test fallback to any when annotations are missing."""
        python_code = """
def mystery_function(x, y):
    return x + y
"""
        ts_code = self.converter.convert_code(python_code)

        assert "function mystery_function(x: any, y: any): any" in ts_code
        assert "return (x + y);" in ts_code

    def test_main_is_invoked(self):
        """Test that a main() function gets a trailing call."""
        python_code = """
def main() -> int:
    print(1)
    return 0
"""
        ts_code = self.converter.convert_code(python_code)

        assert "function main(): void" in ts_code
        assert ts_code.rstrip().endswith("main();")


class TestTypeScriptStatements:
    """Test basic statement conversion."""

    def setup_method(self):
        self.converter = MultiGenPythonToTypeScriptConverter()

    def test_annotated_assignment(self):
        """Test annotated variable assignment."""
        python_code = """
def test_annotated() -> int:
    count: int = 10
    name: str = "test"
    return count
"""
        ts_code = self.converter.convert_code(python_code)

        assert "let count: number = 10;" in ts_code
        assert 'let name: string = "test";' in ts_code

    def test_if_else_statement(self):
        """Test if/else statement conversion."""
        python_code = """
def test_if(x: int) -> int:
    if x > 5:
        return x * 2
    else:
        return x
"""
        ts_code = self.converter.convert_code(python_code)

        assert "if ((x > 5))" in ts_code
        assert "} else {" in ts_code

    def test_while_loop(self):
        """Test while loop conversion."""
        python_code = """
def test_while(n: int) -> int:
    i: int = 0
    while i < n:
        i = i + 1
    return i
"""
        ts_code = self.converter.convert_code(python_code)

        assert "while ((i < n))" in ts_code

    def test_for_range_loop(self):
        """Test for loop with range conversion."""
        python_code = """
def test_for(n: int) -> int:
    total: int = 0
    for i in range(n):
        total = total + i
    return total
"""
        ts_code = self.converter.convert_code(python_code)

        assert "for (let i = 0; i < n; i++)" in ts_code

    def test_for_range_with_start_stop(self):
        """Test for loop with range(start, stop)."""
        python_code = """
def test_for_range(start: int, stop: int) -> int:
    total: int = 0
    for i in range(start, stop):
        total = total + i
    return total
"""
        ts_code = self.converter.convert_code(python_code)

        assert "for (let i = start; i < stop; i++)" in ts_code


class TestTypeScriptOperators:
    """Test operator conversion, including Python-specific semantics."""

    def setup_method(self):
        self.converter = MultiGenPythonToTypeScriptConverter()

    def test_binary_operations(self):
        python_code = """
def test_ops(a: int, b: int) -> int:
    return a + b - a * b
"""
        ts_code = self.converter.convert_code(python_code)
        assert "return ((a + b) - (a * b));" in ts_code

    def test_floor_division_routes_to_runtime(self):
        """Floor division must use mg.floorDiv, not JS `/`."""
        python_code = """
def test_floordiv(a: int, b: int) -> int:
    return a // b
"""
        ts_code = self.converter.convert_code(python_code)
        assert "mg.floorDiv(a, b)" in ts_code

    def test_modulo_routes_to_runtime(self):
        """Modulo must use mg.pyMod for Python sign semantics."""
        python_code = """
def test_mod(a: int, b: int) -> int:
    return a % b
"""
        ts_code = self.converter.convert_code(python_code)
        assert "mg.pyMod(a, b)" in ts_code

    def test_power_is_native(self):
        python_code = """
def test_pow(a: int, b: int) -> int:
    return a ** b
"""
        ts_code = self.converter.convert_code(python_code)
        assert "(a ** b)" in ts_code

    def test_true_division_is_native(self):
        python_code = """
def test_div(a: int, b: int) -> float:
    return a / b
"""
        ts_code = self.converter.convert_code(python_code)
        assert "(a / b)" in ts_code

    def test_augmented_floordiv_expands(self):
        python_code = """
def test_augfloordiv(a: int, b: int) -> int:
    a //= b
    return a
"""
        ts_code = self.converter.convert_code(python_code)
        assert "a = mg.floorDiv(a, b);" in ts_code

    def test_boolean_and_none_constants(self):
        python_code = """
def test_consts() -> int:
    x: bool = True
    y: bool = False
    return 0
"""
        ts_code = self.converter.convert_code(python_code)
        assert "let x: boolean = true;" in ts_code
        assert "let y: boolean = false;" in ts_code


class TestTypeScriptBuiltins:
    """Test built-in function conversion."""

    def setup_method(self):
        self.converter = MultiGenPythonToTypeScriptConverter()

    def test_print_function(self):
        python_code = """
def test_print(msg: str) -> None:
    print(msg)
    print("Hello", "World")
"""
        ts_code = self.converter.convert_code(python_code)
        assert "mg.print(msg);" in ts_code
        assert 'mg.print("Hello", "World");' in ts_code

    def test_len_uses_length_for_arrays(self):
        python_code = """
def test_len(items: list) -> int:
    return len(items)
"""
        ts_code = self.converter.convert_code(python_code)
        assert "items.length" in ts_code

    def test_len_uses_size_for_maps(self):
        python_code = """
def test_len(items: dict) -> int:
    return len(items)
"""
        ts_code = self.converter.convert_code(python_code)
        assert "items.size" in ts_code

    def test_range_function(self):
        python_code = """
def test_range() -> None:
    r: list = list(range(10))
"""
        ts_code = self.converter.convert_code(python_code)
        assert "mg.range(10)" in ts_code

    def test_str_conversion(self):
        python_code = """
def test_str(x: int) -> str:
    return str(x)
"""
        ts_code = self.converter.convert_code(python_code)
        assert "mg.toStr(x)" in ts_code
