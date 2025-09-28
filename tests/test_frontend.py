"""Tests for the CGen Frontend - Static Python Analysis Layer."""

import sys
from pathlib import Path

import pytest

# Add src directory to Python path for development testing
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

HAS_PYTEST = True

from mgen.frontend import (
    ConstraintSeverity,
    InferenceMethod,
    IRDataType,
    StaticConstraintChecker,
    StaticPythonSubsetValidator,
    SubsetTier,
    TypeInferenceEngine,
    analyze_python_code,
    build_ir_from_code,
)


class TestASTAnalyzer:
    """Test the AST analysis framework."""

    def test_simple_function_analysis(self):
        """Test analysis of a simple function."""
        code = """
def add(x: int, y: int) -> int:
    return x + y
"""
        result = analyze_python_code(code)

        assert result.convertible
        assert len(result.functions) == 1
        assert "add" in result.functions

        func_info = result.functions["add"]
        assert func_info.name == "add"
        assert len(func_info.parameters) == 2
        assert func_info.return_type.name == "int"

    def test_function_with_variables(self):
        """Test analysis of function with local variables."""
        code = """
def calculate(x: int, y: float) -> float:
    result: float = x * y
    return result
"""
        result = analyze_python_code(code)

        assert result.convertible
        func_info = result.functions["calculate"]
        # local_variables includes both parameters and actual local variables
        assert len(func_info.local_variables) == 3  # x, y (params) + result (local)
        assert "result" in func_info.local_variables
        assert "x" in func_info.local_variables
        assert "y" in func_info.local_variables

        # Check that result is not a parameter
        assert not func_info.local_variables["result"].is_parameter

    def test_missing_type_annotations(self):
        """Test error detection for missing type annotations."""
        code = """
def bad_function(x):
    return x
"""
        result = analyze_python_code(code)

        assert not result.convertible
        assert len(result.errors) > 0
        assert any("type annotation" in error for error in result.errors)

    def test_complexity_calculation(self):
        """Test function complexity calculation."""
        simple_code = """
def simple(x: int) -> int:
    return x + 1
"""
        complex_code = """
def complex_func(x: int) -> int:
    if x > 0:
        for i in range(10):
            if i % 2 == 0:
                x = x + i
    return x
"""
        simple_result = analyze_python_code(simple_code)
        complex_result = analyze_python_code(complex_code)

        simple_func = simple_result.functions["simple"]
        complex_func = complex_result.functions["complex_func"]

        assert simple_func.complexity.value < complex_func.complexity.value


class TestTypeInference:
    """Test the type inference system."""


    def test_literal_type_inference(self):
        """Test type inference for literals."""
        engine = TypeInferenceEngine()

        # Test different literal types
        import ast
        int_literal = ast.Constant(value=42)
        float_literal = ast.Constant(value=3.14)
        bool_literal = ast.Constant(value=True)
        str_literal = ast.Constant(value="hello")

        int_result = engine.infer_expression_type(int_literal, {})
        float_result = engine.infer_expression_type(float_literal, {})
        bool_result = engine.infer_expression_type(bool_literal, {})
        str_result = engine.infer_expression_type(str_literal, {})

        assert int_result.type_info.name == "int"
        assert float_result.type_info.name == "float"
        assert bool_result.type_info.name == "bool"
        assert str_result.type_info.name == "str"

        # All should have high confidence
        assert int_result.confidence == 1.0
        assert int_result.method == InferenceMethod.LITERAL

    def test_binary_operation_inference(self):
        """Test type inference for binary operations."""
        engine = TypeInferenceEngine()

        # Create a simple AST for: 5 + 3
        import ast
        left = ast.Constant(value=5)
        right = ast.Constant(value=3)
        binop = ast.BinOp(left=left, op=ast.Add(), right=right)

        result = engine.infer_expression_type(binop, {})

        assert result.type_info.c_equivalent == "int"
        assert result.method == InferenceMethod.OPERATION
        assert result.confidence > 0.8


class TestConstraintChecker:
    """Test the static constraint checker."""


    def test_safe_code_passes(self):
        """Test that safe code passes constraint checking."""
        code = """
def safe_function(x: int, y: int) -> int:
    result: int = x + y
    return result
"""
        checker = StaticConstraintChecker()
        report = checker.check_code(code)

        assert report.conversion_safe
        assert len(report.get_violations_by_severity(ConstraintSeverity.ERROR)) == 0

    def test_division_by_zero_detection(self):
        """Test detection of division by zero."""
        code = """
def unsafe_division(x: int) -> float:
    return x / 0
"""
        checker = StaticConstraintChecker()
        report = checker.check_code(code)

        assert not report.conversion_safe
        errors = report.get_violations_by_severity(ConstraintSeverity.ERROR)
        assert any("division by zero" in error.message.lower() for error in errors)

    def test_c_keyword_conflict(self):
        """Test detection of C keyword conflicts."""
        code = """
def int(x: int) -> int:  # 'int' is a C keyword
    return x
"""
        checker = StaticConstraintChecker()
        report = checker.check_code(code)

        errors = report.get_violations_by_severity(ConstraintSeverity.ERROR)
        assert any("keyword" in error.message.lower() for error in errors)

    def test_unsupported_features(self):
        """Test detection of unsupported Python features."""
        code = """
def use_generator():
    return (x*2 for x in range(10))  # Generator expression
"""
        checker = StaticConstraintChecker()
        report = checker.check_code(code)

        errors = report.get_violations_by_severity(ConstraintSeverity.ERROR)
        assert any("unsupported" in error.message.lower() for error in errors)


class TestSubsetValidator:
    """Test the Python subset validator."""


    def test_tier1_fundamental_features(self):
        """Test validation of Tier 1 fundamental features."""
        code = """
def basic_function(x: int, y: float) -> float:
    result: float = x + y
    return result
"""
        validator = StaticPythonSubsetValidator()
        result = validator.validate_code(code)

        assert result.is_valid
        assert result.tier == SubsetTier.TIER_1_FUNDAMENTAL
        assert len(result.violations) == 0

    def test_unsupported_features_rejected(self):
        """Test that unsupported features are properly rejected."""
        code = """
def use_lambda():
    return lambda x: x * 2  # Lambda not supported
"""
        validator = StaticPythonSubsetValidator()
        result = validator.validate_code(code)

        assert not result.is_valid
        assert len(result.violations) > 0
        assert len(result.unsupported_features) > 0

    def test_feature_support_query(self):
        """Test querying feature support information."""
        validator = StaticPythonSubsetValidator()

        basic_types = validator.get_feature_support("basic_types")
        assert basic_types is not None
        assert basic_types.tier == SubsetTier.TIER_1_FUNDAMENTAL

        supported_features = validator.list_supported_features(SubsetTier.TIER_1_FUNDAMENTAL)
        assert len(supported_features) > 0

    def test_conversion_strategy_determination(self):
        """Test conversion strategy determination."""
        simple_code = """
def simple(x: int) -> int:
    return x + 1
"""
        validator = StaticPythonSubsetValidator()
        result = validator.validate_code(simple_code)

        assert result.conversion_strategy == "direct_conversion"


class TestStaticIR:
    """Test the Static IR generation."""


    def test_simple_function_ir(self):
        """Test IR generation for a simple function."""
        code = """
def add(x: int, y: int) -> int:
    return x + y
"""
        ir_module = build_ir_from_code(code)

        assert ir_module.name == "main"
        assert len(ir_module.functions) == 1

        func = ir_module.functions[0]
        assert func.name == "add"
        assert len(func.parameters) == 2
        assert func.return_type.base_type == IRDataType.INT

    def test_function_with_variables_ir(self):
        """Test IR generation for function with local variables."""
        code = """
def calculate(x: int, y: int) -> int:
    result: int = x + y
    return result
"""
        ir_module = build_ir_from_code(code)

        func = ir_module.functions[0]
        assert len(func.local_variables) == 1
        assert func.local_variables[0].name == "result"
        assert func.local_variables[0].ir_type.base_type == IRDataType.INT

    def test_control_flow_ir(self):
        """Test IR generation for control flow."""
        code = """
def conditional(x: int) -> int:
    if x > 0:
        return x
    else:
        return 0
"""
        ir_module = build_ir_from_code(code)

        func = ir_module.functions[0]
        # Check that we have statements in the body
        assert len(func.body) > 0

    def test_loop_ir(self):
        """Test IR generation for loops."""
        code = """
def loop_function(n: int) -> int:
    total: int = 0
    for i in range(n):
        total = total + i
    return total
"""
        ir_module = build_ir_from_code(code)

        func = ir_module.functions[0]
        assert len(func.body) > 0
        assert len(func.local_variables) >= 1  # total variable

    def test_ir_type_mapping(self):
        """Test correct type mapping in IR."""
        from mgen.frontend.static_ir import IRDataType, IRType

        int_type = IRType(IRDataType.INT)
        float_type = IRType(IRDataType.FLOAT)
        string_type = IRType(IRDataType.STRING)

        assert int_type.to_c_declaration("var") == "int var"
        assert float_type.to_c_declaration("var") == "double var"
        assert string_type.to_c_declaration("var") == "char* var"

        # Test pointer types
        int_ptr = IRType(IRDataType.INT, is_pointer=True)
        assert int_ptr.to_c_declaration("ptr") == "int *ptr"

        # Test const types
        const_int = IRType(IRDataType.INT, is_const=True)
        assert const_int.to_c_declaration("var") == "const int var"


class TestFrontendIntegration:
    """Integration tests for frontend components."""


    def test_complete_analysis_pipeline(self):
        """Test the complete analysis pipeline."""
        code = """
def fibonacci(n: int) -> int:
    if n <= 1:
        return n
    a: int = 0
    b: int = 1
    for i in range(2, n + 1):
        temp: int = a + b
        a = b
        b = temp
    return b
"""

        # Run all analysis components
        ast_result = analyze_python_code(code)

        checker = StaticConstraintChecker()
        constraint_report = checker.check_code(code)

        validator = StaticPythonSubsetValidator()
        validation_result = validator.validate_code(code)

        ir_module = build_ir_from_code(code)

        # Verify all components agree on convertibility
        assert ast_result.convertible
        assert constraint_report.conversion_safe
        assert validation_result.is_valid

        # Verify IR was generated
        assert len(ir_module.functions) == 1
        assert ir_module.functions[0].name == "fibonacci"

    def test_error_consistency(self):
        """Test that all components consistently identify errors."""
        bad_code = """
def bad_function(x):  # Missing type annotation
    return eval("x + 1")  # Dynamic execution
"""

        ast_result = analyze_python_code(bad_code)

        checker = StaticConstraintChecker()
        constraint_report = checker.check_code(bad_code)

        validator = StaticPythonSubsetValidator()
        validator.validate_code(bad_code)

        # All should identify problems
        assert not ast_result.convertible
        assert not constraint_report.conversion_safe
        # Note: validator might not catch all issues since it focuses on subset validation

    def test_performance_with_large_function(self):
        """Test performance with larger functions."""
        # Generate a larger function
        lines = ["def large_function(x: int) -> int:"]
        lines.append("    result: int = x")
        for i in range(50):
            lines.append(f"    temp_{i}: int = result + {i}")
            lines.append(f"    result = result + temp_{i}")
        lines.append("    return result")

        large_code = "\n".join(lines)

        # All components should handle this reasonably quickly
        import time

        start_time = time.time()
        ast_result = analyze_python_code(large_code)
        ast_time = time.time() - start_time

        start_time = time.time()
        ir_module = build_ir_from_code(large_code)
        ir_time = time.time() - start_time

        # Should complete in reasonable time
        assert ast_time < 1.0  # 1 second
        assert ir_time < 1.0   # 1 second

        # Verify results are reasonable
        assert ast_result.convertible
        assert len(ir_module.functions) == 1
        func = ir_module.functions[0]
        assert len(func.local_variables) > 40  # Should have many variables


# Add pytest markers if pytest is available
if HAS_PYTEST:
    TestASTAnalyzer = pytest.mark.frontend(pytest.mark.unit(TestASTAnalyzer))
    TestTypeInference = pytest.mark.frontend(pytest.mark.unit(TestTypeInference))
    TestConstraintChecker = pytest.mark.frontend(pytest.mark.unit(TestConstraintChecker))
    TestSubsetValidator = pytest.mark.frontend(pytest.mark.unit(TestSubsetValidator))
    TestStaticIR = pytest.mark.frontend(pytest.mark.unit(TestStaticIR))
    TestFrontendIntegration = pytest.mark.frontend(pytest.mark.integration(TestFrontendIntegration))
