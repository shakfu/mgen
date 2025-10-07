"""Tests for LLVM backend functionality."""

import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from mgen.backends.llvm import IRToLLVMConverter
from mgen.frontend.static_ir import IRBuilder

# Check if LLVM tools are available
LLVM_LLC_PATH = shutil.which("llc")
LLVM_LLI_PATH = shutil.which("lli")
LLVM_CLANG_PATH = shutil.which("clang")

# Try Homebrew LLVM if standard tools not found
if not all([LLVM_LLC_PATH, LLVM_LLI_PATH, LLVM_CLANG_PATH]):
    homebrew_llvm = Path("/opt/homebrew/opt/llvm/bin")
    if homebrew_llvm.exists():
        LLVM_LLC_PATH = str(homebrew_llvm / "llc") if (homebrew_llvm / "llc").exists() else None
        LLVM_LLI_PATH = str(homebrew_llvm / "lli") if (homebrew_llvm / "lli").exists() else None
        LLVM_CLANG_PATH = str(homebrew_llvm / "clang") if (homebrew_llvm / "clang").exists() else None

LLVM_TOOLS_AVAILABLE = all([LLVM_LLC_PATH, LLVM_LLI_PATH])
pytestmark = pytest.mark.skipif(not LLVM_TOOLS_AVAILABLE, reason="LLVM tools not available")


class TestLLVMBasicConversion:
    """Test basic LLVM IR generation functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.ir_builder = IRBuilder()
        self.llvm_converter = IRToLLVMConverter()

    def _convert_to_llvm(self, python_code: str) -> str:
        """Convert Python code to LLVM IR."""
        import ast
        tree = ast.parse(python_code)
        ir_module = self.ir_builder.build_from_ast(tree)
        llvm_module = self.llvm_converter.visit_module(ir_module)
        return str(llvm_module)

    def test_simple_arithmetic(self):
        """Test simple arithmetic operations."""
        python_code = """
def add(a: int, b: int) -> int:
    return a + b
"""
        llvm_ir = self._convert_to_llvm(python_code)

        # Check for function definition
        assert 'define i64 @"add"' in llvm_ir
        # Check for addition instruction
        assert "add i64" in llvm_ir

    def test_function_call_return_types(self):
        """Test that function calls have proper return types."""
        python_code = """
def get_one() -> int:
    return 1

def get_two() -> int:
    return 2

def main() -> int:
    return get_one() + get_two()
"""
        llvm_ir = self._convert_to_llvm(python_code)

        # Should have proper function call types and addition
        assert 'call i64 @"get_one"' in llvm_ir
        assert 'call i64 @"get_two"' in llvm_ir
        assert "add i64" in llvm_ir


class TestLLVMControlFlow:
    """Test control flow constructs in LLVM backend."""

    def setup_method(self):
        """Set up test fixtures."""
        self.ir_builder = IRBuilder()
        self.llvm_converter = IRToLLVMConverter()

    def _convert_to_llvm(self, python_code: str) -> str:
        """Convert Python code to LLVM IR."""
        import ast
        tree = ast.parse(python_code)
        ir_module = self.ir_builder.build_from_ast(tree)
        llvm_module = self.llvm_converter.visit_module(ir_module)
        return str(llvm_module)

    def test_if_statement_with_comparison(self):
        """Test if statement with comparison."""
        python_code = """
def max_val(a: int, b: int) -> int:
    if a > b:
        return a
    else:
        return b
"""
        llvm_ir = self._convert_to_llvm(python_code)
        

        # Check for comparison instruction
        assert "icmp sgt" in llvm_ir
        # Check for conditional branch
        assert "br i1" in llvm_ir
        # Check for labels
        assert "if.then:" in llvm_ir
        assert "if.else:" in llvm_ir

    def test_while_loop(self):
        """Test while loop."""
        python_code = """
def count_down(n: int) -> int:
    i: int = n
    while i > 0:
        i = i - 1
    return i
"""
        llvm_ir = self._convert_to_llvm(python_code)
        

        # Check for loop structure
        assert "while.cond:" in llvm_ir
        assert "while.body:" in llvm_ir
        assert "while.exit:" in llvm_ir
        # Check for comparison and branch
        assert "icmp sgt" in llvm_ir
        assert "br i1" in llvm_ir

    def test_for_loop(self):
        """Test for loop with range."""
        python_code = """
def sum_range(n: int) -> int:
    total: int = 0
    i: int
    for i in range(n):
        total = total + i
    return total
"""
        llvm_ir = self._convert_to_llvm(python_code)
        

        # Check for loop structure
        assert "for.cond:" in llvm_ir
        assert "for.body:" in llvm_ir
        assert "for.inc:" in llvm_ir
        assert "for.exit:" in llvm_ir


class TestLLVMBooleanOperations:
    """Test boolean operations in LLVM backend."""

    def setup_method(self):
        """Set up test fixtures."""
        self.ir_builder = IRBuilder()
        self.llvm_converter = IRToLLVMConverter()

    def _convert_to_llvm(self, python_code: str) -> str:
        """Convert Python code to LLVM IR."""
        import ast
        tree = ast.parse(python_code)
        ir_module = self.ir_builder.build_from_ast(tree)
        llvm_module = self.llvm_converter.visit_module(ir_module)
        return str(llvm_module)

    def test_and_operation(self):
        """Test boolean and operation."""
        python_code = """
def test_and(a: int, b: int) -> int:
    if a > 5 and b > 5:
        return 1
    return 0
"""
        llvm_ir = self._convert_to_llvm(python_code)
        

        # Check for comparison instructions
        assert "icmp sgt" in llvm_ir
        # Check for and instruction
        assert "and i1" in llvm_ir

    def test_or_operation(self):
        """Test boolean or operation."""
        python_code = """
def test_or(a: int, b: int) -> int:
    if a > 5 or b > 5:
        return 1
    return 0
"""
        llvm_ir = self._convert_to_llvm(python_code)
        

        # Check for comparison instructions
        assert "icmp sgt" in llvm_ir
        # Check for or instruction
        assert "or i1" in llvm_ir

    def test_not_operation(self):
        """Test boolean not operation."""
        python_code = """
def test_not(a: int) -> int:
    if not a > 5:
        return 1
    return 0
"""
        llvm_ir = self._convert_to_llvm(python_code)
        

        # Check for comparison (not is implemented as comparison with false/0)
        assert "icmp" in llvm_ir


@pytest.mark.skipif(not LLVM_LLI_PATH, reason="LLVM lli not available")
class TestLLVMExecution:
    """Test execution of generated LLVM IR."""

    def setup_method(self):
        """Set up test fixtures."""
        self.ir_builder = IRBuilder()
        self.llvm_converter = IRToLLVMConverter()
        self.temp_dir = None

    def _convert_to_llvm(self, python_code: str) -> str:
        """Convert Python code to LLVM IR."""
        import ast
        tree = ast.parse(python_code)
        ir_module = self.ir_builder.build_from_ast(tree)
        llvm_module = self.llvm_converter.visit_module(ir_module)
        return str(llvm_module)

    def teardown_method(self):
        """Clean up temporary files."""
        if self.temp_dir and Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def _execute_llvm_ir(self, llvm_ir: str) -> int:
        """Execute LLVM IR and return exit code."""
        self.temp_dir = tempfile.mkdtemp()
        ll_file = Path(self.temp_dir) / "test.ll"
        ll_file.write_text(llvm_ir)

        result = subprocess.run(
            [LLVM_LLI_PATH, str(ll_file)],
            capture_output=True,
            text=True
        )
        return result.returncode

    def test_simple_return(self):
        """Test simple return value."""
        python_code = """
def main() -> int:
    return 42
"""
        llvm_ir = self._convert_to_llvm(python_code)
        exit_code = self._execute_llvm_ir(llvm_ir)
        assert exit_code == 42

    def test_addition(self):
        """Test addition execution."""
        python_code = """
def main() -> int:
    return 1 + 2
"""
        llvm_ir = self._convert_to_llvm(python_code)
        exit_code = self._execute_llvm_ir(llvm_ir)
        assert exit_code == 3

    def test_function_call_addition(self):
        """Test addition of function call results."""
        python_code = """
def get_one() -> int:
    return 1

def get_two() -> int:
    return 2

def main() -> int:
    return get_one() + get_two()
"""
        llvm_ir = self._convert_to_llvm(python_code)
        exit_code = self._execute_llvm_ir(llvm_ir)
        assert exit_code == 3

    def test_if_statement_execution(self):
        """Test if statement execution."""
        python_code = """
def max_val(a: int, b: int) -> int:
    if a > b:
        return a
    else:
        return b

def main() -> int:
    return max_val(10, 5)
"""
        llvm_ir = self._convert_to_llvm(python_code)
        exit_code = self._execute_llvm_ir(llvm_ir)
        assert exit_code == 10

    def test_boolean_and_execution(self):
        """Test boolean and execution."""
        python_code = """
def test_and(a: int, b: int) -> int:
    if a > 5 and b > 5:
        return 1
    return 0

def main() -> int:
    return test_and(10, 10)
"""
        llvm_ir = self._convert_to_llvm(python_code)
        exit_code = self._execute_llvm_ir(llvm_ir)
        assert exit_code == 1

    def test_boolean_or_execution(self):
        """Test boolean or execution."""
        python_code = """
def test_or(a: int, b: int) -> int:
    if a > 5 or b > 5:
        return 1
    return 0

def main() -> int:
    return test_or(3, 10)
"""
        llvm_ir = self._convert_to_llvm(python_code)
        exit_code = self._execute_llvm_ir(llvm_ir)
        assert exit_code == 1

    def test_boolean_not_execution(self):
        """Test boolean not execution."""
        python_code = """
def test_not(a: int) -> int:
    if not a > 5:
        return 1
    return 0

def main() -> int:
    return test_not(3)
"""
        llvm_ir = self._convert_to_llvm(python_code)
        exit_code = self._execute_llvm_ir(llvm_ir)
        assert exit_code == 1

    def test_for_loop_execution(self):
        """Test for loop execution."""
        python_code = """
def sum_range(n: int) -> int:
    total: int = 0
    i: int
    for i in range(n):
        total = total + i
    return total

def main() -> int:
    return sum_range(10)
"""
        llvm_ir = self._convert_to_llvm(python_code)
        exit_code = self._execute_llvm_ir(llvm_ir)
        # sum(0..9) = 45
        assert exit_code == 45

    def test_break_statement_execution(self):
        """Test break statement execution."""
        python_code = """
def test_break(n: int) -> int:
    i: int = 0
    while i < n:
        if i == 5:
            break
        i = i + 1
    return i

def main() -> int:
    return test_break(10)
"""
        llvm_ir = self._convert_to_llvm(python_code)
        exit_code = self._execute_llvm_ir(llvm_ir)
        assert exit_code == 5

    def test_continue_statement_execution(self):
        """Test continue statement execution."""
        python_code = """
def test_continue(n: int) -> int:
    total: int = 0
    i: int = 0
    while i < n:
        i = i + 1
        if i % 2 == 0:
            continue
        total = total + i
    return total

def main() -> int:
    return test_continue(10)
"""
        llvm_ir = self._convert_to_llvm(python_code)
        exit_code = self._execute_llvm_ir(llvm_ir)
        # Sum of odd numbers 1,3,5,7,9 = 25
        assert exit_code == 25

    def test_elif_chain_execution(self):
        """Test elif chain execution."""
        python_code = """
def classify(x: int) -> int:
    if x > 10:
        return 1
    elif x > 5:
        return 2
    elif x > 0:
        return 3
    else:
        return 4

def main() -> int:
    return classify(7)
"""
        llvm_ir = self._convert_to_llvm(python_code)
        exit_code = self._execute_llvm_ir(llvm_ir)
        assert exit_code == 2

    def test_comparison_chaining_execution(self):
        """Test comparison chaining execution."""
        python_code = """
def is_between(x: int, low: int, high: int) -> int:
    if low < x < high:
        return 1
    return 0

def main() -> int:
    return is_between(5, 3, 10)
"""
        llvm_ir = self._convert_to_llvm(python_code)
        exit_code = self._execute_llvm_ir(llvm_ir)
        assert exit_code == 1

    def test_boolean_chaining_execution(self):
        """Test boolean chaining execution."""
        python_code = """
def test_and_chain(a: int, b: int, c: int) -> int:
    if a > 0 and b > 0 and c > 0:
        return 1
    return 0

def test_or_chain(a: int, b: int, c: int) -> int:
    if a > 10 or b > 10 or c > 10:
        return 1
    return 0

def main() -> int:
    return test_and_chain(1, 2, 3) + test_or_chain(1, 2, 15)
"""
        llvm_ir = self._convert_to_llvm(python_code)
        exit_code = self._execute_llvm_ir(llvm_ir)
        assert exit_code == 2

    def test_augmented_assignment_execution(self):
        """Test augmented assignment execution."""
        python_code = """
def test_augmented(x: int) -> int:
    y: int = 10
    y += x
    y -= 2
    y *= 2
    return y

def main() -> int:
    return test_augmented(5)
"""
        llvm_ir = self._convert_to_llvm(python_code)
        exit_code = self._execute_llvm_ir(llvm_ir)
        # (10 + 5 - 2) * 2 = 26
        assert exit_code == 26

    def test_modulo_operation_execution(self):
        """Test modulo operation execution."""
        python_code = """
def test_mod(a: int, b: int) -> int:
    return a % b

def main() -> int:
    return test_mod(17, 5)
"""
        llvm_ir = self._convert_to_llvm(python_code)
        exit_code = self._execute_llvm_ir(llvm_ir)
        assert exit_code == 2

    def test_bitwise_operations_execution(self):
        """Test bitwise operations execution."""
        python_code = """
def test_bitwise(a: int, b: int) -> int:
    x: int = a << 2
    y: int = b >> 1
    z: int = a & b
    w: int = a | b
    v: int = a ^ b
    return x + y + z + w + v

def main() -> int:
    return test_bitwise(12, 5)
"""
        llvm_ir = self._convert_to_llvm(python_code)
        exit_code = self._execute_llvm_ir(llvm_ir)
        # 48 + 2 + 4 + 13 + 9 = 76
        assert exit_code == 76

    def test_integer_division_execution(self):
        """Test integer division execution."""
        python_code = """
def test_intdiv(a: int, b: int) -> int:
    return a // b

def main() -> int:
    return test_intdiv(17, 5)
"""
        llvm_ir = self._convert_to_llvm(python_code)
        exit_code = self._execute_llvm_ir(llvm_ir)
        assert exit_code == 3

    def test_type_cast_execution(self):
        """Test type casting execution."""
        python_code = """
def int_to_float(x: int) -> float:
    return float(x)

def float_to_int(x: float) -> int:
    return int(x)

def main() -> int:
    a: float = int_to_float(42)
    b: int = float_to_int(3.7)
    return b
"""
        llvm_ir = self._convert_to_llvm(python_code)
        exit_code = self._execute_llvm_ir(llvm_ir)
        assert exit_code == 3

    def test_comprehensive_program_execution(self):
        """Test comprehensive program with multiple algorithms."""
        python_code = """
def fibonacci(n: int) -> int:
    if n <= 1:
        return n
    a: int = 0
    b: int = 1
    i: int
    for i in range(2, n + 1):
        temp: int = a + b
        a = b
        b = temp
    return b

def factorial(n: int) -> int:
    result: int = 1
    i: int
    for i in range(1, n + 1):
        result *= i
    return result

def is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    i: int = 3
    while i * i <= n:
        if n % i == 0:
            return False
        i += 2
    return True

def main() -> int:
    fib10: int = fibonacci(10)
    fact5: int = factorial(5)
    prime: bool = is_prime(17)
    prime_int: int = int(prime)
    return fib10 + fact5 + prime_int
"""
        llvm_ir = self._convert_to_llvm(python_code)
        exit_code = self._execute_llvm_ir(llvm_ir)
        # fib(10)=55, fact(5)=120, is_prime(17)=1 => 55+120+1=176
        assert exit_code == 176

    def test_unary_operators_execution(self):
        """Test unary operators execution."""
        python_code = """
def test_unary(x: int) -> int:
    a: int = -x
    b: int = +x
    c: int = ~x
    return a + b + c

def test_negative() -> int:
    x: int = -42
    y: int = -10
    return x + y

def main() -> int:
    result1: int = test_unary(5)
    result2: int = test_negative()
    return result1 + result2
"""
        llvm_ir = self._convert_to_llvm(python_code)
        exit_code = self._execute_llvm_ir(llvm_ir)
        # -5+5-6 + -42-10 = -6 + -52 = -58 => 256-58=198 (unsigned byte wrapping)
        assert exit_code == 198

    def test_boolean_literals_execution(self):
        """Test boolean literals execution."""
        python_code = """
def test_bool() -> int:
    a: bool = True
    b: bool = False
    if a and not b:
        return 1
    return 0

def main() -> int:
    return test_bool()
"""
        llvm_ir = self._convert_to_llvm(python_code)
        exit_code = self._execute_llvm_ir(llvm_ir)
        assert exit_code == 1

    def test_multiple_early_returns_execution(self):
        """Test multiple early return paths."""
        python_code = """
def classify_number(x: int) -> int:
    if x < 0:
        return -1
    if x == 0:
        return 0
    if x < 10:
        return 1
    if x < 100:
        return 2
    return 3

def main() -> int:
    a: int = classify_number(-5)
    b: int = classify_number(0)
    c: int = classify_number(5)
    d: int = classify_number(50)
    e: int = classify_number(200)
    return a + b + c + d + e
"""
        llvm_ir = self._convert_to_llvm(python_code)
        exit_code = self._execute_llvm_ir(llvm_ir)
        # -1 + 0 + 1 + 2 + 3 = 5
        assert exit_code == 5
