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
