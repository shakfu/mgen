"""Basic tests for LLVM backend."""

import tempfile
from pathlib import Path

import pytest

from mgen.backends.llvm import IRToLLVMConverter, LLVMBackend
from mgen.frontend.static_ir import build_ir_from_code


class TestLLVMIRGeneration:
    """Test LLVM IR generation from Static IR."""

    def test_simple_add_function(self):
        """Test generating LLVM IR for a simple add function."""
        python_code = """
def add(x: int, y: int) -> int:
    return x + y
"""

        # Build Static IR from Python
        ir_module = build_ir_from_code(python_code)

        # Convert to LLVM IR
        converter = IRToLLVMConverter()
        llvm_module = converter.visit_module(ir_module)

        # Get LLVM IR as string
        llvm_ir = str(llvm_module)

        # Verify LLVM IR contains expected elements
        assert "define" in llvm_ir  # Function definition
        assert "add" in llvm_ir  # Function name
        assert "i64" in llvm_ir  # 64-bit integer type
        assert "ret" in llvm_ir  # Return instruction

    def test_arithmetic_operations(self):
        """Test LLVM IR generation for arithmetic operations."""
        python_code = """
def calc(a: int, b: int) -> int:
    result: int = a + b - a * b
    return result
"""

        ir_module = build_ir_from_code(python_code)
        converter = IRToLLVMConverter()
        llvm_module = converter.visit_module(ir_module)
        llvm_ir = str(llvm_module)

        # Check for arithmetic instructions
        assert "add" in llvm_ir or "sub" in llvm_ir or "mul" in llvm_ir
        assert "alloca" in llvm_ir  # Local variable allocation
        assert "store" in llvm_ir  # Variable assignment
        assert "load" in llvm_ir  # Variable read

    def test_function_with_local_variable(self):
        """Test LLVM IR generation with local variables."""
        python_code = """
def square(x: int) -> int:
    result: int = x * x
    return result
"""

        ir_module = build_ir_from_code(python_code)
        converter = IRToLLVMConverter()
        llvm_module = converter.visit_module(ir_module)
        llvm_ir = str(llvm_module)

        assert "alloca i64" in llvm_ir  # Variable allocation
        assert "store" in llvm_ir
        assert "mul" in llvm_ir  # Multiplication


class TestLLVMBackend:
    """Test LLVM backend integration."""

    def test_backend_initialization(self):
        """Test LLVM backend initializes correctly."""
        backend = LLVMBackend()

        assert backend.get_name() == "llvm"
        assert backend.get_file_extension() == ".ll"
        assert backend.get_emitter() is not None
        assert backend.get_factory() is not None
        assert backend.get_builder() is not None

    def test_backend_feature_support(self):
        """Test feature support queries."""
        backend = LLVMBackend()

        assert backend.supports_feature("functions")
        assert backend.supports_feature("variables")
        assert backend.supports_feature("arithmetic")
        assert backend.supports_feature("control_flow")
        assert backend.supports_feature("loops")

    def test_emit_simple_function(self):
        """Test emitting LLVM IR via backend."""
        backend = LLVMBackend()

        python_code = """
def add(x: int, y: int) -> int:
    return x + y
"""

        llvm_ir = backend.get_emitter().emit_module(python_code)

        assert llvm_ir is not None
        assert len(llvm_ir) > 0
        assert "define" in llvm_ir
        assert '@"add"' in llvm_ir or "@add" in llvm_ir


class TestLLVMBuilder:
    """Test LLVM builder functionality."""

    def test_generate_makefile(self):
        """Test Makefile generation."""
        backend = LLVMBackend()
        builder = backend.get_builder()

        makefile = builder.generate_build_file(["test.ll"], "test_program")

        assert "LLC" in makefile
        assert "CLANG" in makefile
        assert "test_program" in makefile
        assert "test.ll" in makefile
        assert ".PHONY" in makefile

    def test_get_compile_flags(self):
        """Test compile flags retrieval."""
        backend = LLVMBackend()
        builder = backend.get_builder()

        flags = builder.get_compile_flags()

        assert isinstance(flags, list)
        assert "-filetype=obj" in flags


class TestEndToEnd:
    """End-to-end tests for LLVM backend."""

    def test_generate_llvm_ir_file(self):
        """Test generating LLVM IR file from Python code."""
        python_code = """
def multiply(x: int, y: int) -> int:
    result: int = x * y
    return result
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            # Generate LLVM IR
            backend = LLVMBackend()
            llvm_ir = backend.get_emitter().emit_module(python_code)

            # Write to file
            output_file = Path(temp_dir) / "multiply.ll"
            output_file.write_text(llvm_ir)

            # Verify file exists and has content
            assert output_file.exists()
            content = output_file.read_text()
            assert len(content) > 0
            assert "define" in content
            assert '@"multiply"' in content or "@multiply" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
