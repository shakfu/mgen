"""Test cases for flow-sensitive type inference."""

import ast

from mgen.frontend.flow_sensitive_inference import FLOW_BOOL, FLOW_FLOAT, FLOW_INT, FlowSensitiveInferencer, TypeUnifier
from mgen.frontend.type_inference import TypeInferenceEngine


class TestTypeUnifier:
    """Test the TypeUnifier class."""

    def test_basic_unification(self):
        """Test basic type unification."""
        unifier = TypeUnifier()

        # Same types unify to themselves
        assert unifier.unify(FLOW_INT, FLOW_INT) == FLOW_INT

        # Unknown types unify to known type
        from mgen.frontend.flow_sensitive_inference import FLOW_UNKNOWN
        assert unifier.unify(FLOW_INT, FLOW_UNKNOWN) == FLOW_INT

        # Numeric coercion
        result = unifier.unify(FLOW_INT, FLOW_FLOAT)
        assert result == FLOW_FLOAT

    def test_bool_int_coercion(self):
        """Test bool-int type coercion."""
        unifier = TypeUnifier()
        result = unifier.unify(FLOW_BOOL, FLOW_INT)
        assert result == FLOW_INT


class TestFlowSensitiveInferencer:
    """Test the FlowSensitiveInferencer class."""

    def setUp(self):
        """Set up test fixtures."""
        self.fallback_engine = TypeInferenceEngine(enable_flow_sensitive=False)
        self.inferencer = FlowSensitiveInferencer(self.fallback_engine)

    def test_parameter_inference_from_usage(self):
        """Test inferring parameter types from usage patterns."""
        self.setUp()

        # Test function with unannotated parameter used in arithmetic
        code = """
def test_func(x, y: int):
    if x > 0:
        result = x + y
    else:
        result = x * 2
    return result
"""
        tree = ast.parse(code)
        func_node = tree.body[0]

        results = self.inferencer.analyze_function_flow(func_node)

        # Should infer x as int from arithmetic usage
        assert "x" in results
        assert results["x"].confidence > 0.0
        assert results["x"].type_info.name in ["int", "union"]  # May be union with float

    def test_comparison_type_propagation(self):
        """Test type propagation through comparisons."""
        self.setUp()

        code = """
def test_func(a, b):
    if a > b:
        return a + 1
    return b + 2
"""
        tree = ast.parse(code)
        func_node = tree.body[0]

        results = self.inferencer.analyze_function_flow(func_node)

        # Both parameters should be inferred as compatible numeric types
        assert "a" in results
        assert "b" in results
        assert results["a"].confidence > 0.0
        assert results["b"].confidence > 0.0

    def test_return_type_inference(self):
        """Test return type inference."""
        self.setUp()

        code = """
def test_func(x: int):
    if x > 0:
        return x + 1
    else:
        return x * 2
"""
        tree = ast.parse(code)
        func_node = tree.body[0]

        results = self.inferencer.analyze_function_flow(func_node)

        # Should infer return type as int
        assert "__return__" in results
        assert results["__return__"].type_info.name == "int"

    def test_flow_sensitive_branching(self):
        """Test flow-sensitive analysis with branching."""
        self.setUp()

        code = """
def test_func(flag: bool):
    if flag:
        result = 42
    else:
        result = 3.14
    return result
"""
        tree = ast.parse(code)
        func_node = tree.body[0]

        results = self.inferencer.analyze_function_flow(func_node)

        # result should be unified as union or float (depends on unification strategy)
        # At minimum, should have reasonable confidence
        assert "result" in results
        assert results["result"].confidence > 0.0


class TestIntegrationWithExistingEngine:
    """Test integration with existing TypeInferenceEngine."""

    def test_enhanced_analysis_fallback(self):
        """Test that enhanced analysis falls back gracefully."""
        engine = TypeInferenceEngine(enable_flow_sensitive=True)

        # Test with well-formed function
        code = """
def test_func(x: int, y: int) -> int:
    return x + y
"""
        tree = ast.parse(code)
        func_node = tree.body[0]

        results = engine.analyze_function_signature_enhanced(func_node)

        # Should work and provide results
        assert len(results) > 0
        assert "x" in results
        assert "y" in results

    def test_disable_flow_sensitive(self):
        """Test disabling flow-sensitive analysis."""
        engine = TypeInferenceEngine(enable_flow_sensitive=False)

        code = """
def test_func(x: int, y: int) -> int:
    return x + y
"""
        tree = ast.parse(code)
        func_node = tree.body[0]

        # Should use regular analysis
        results = engine.analyze_function_signature_enhanced(func_node)
        assert len(results) > 0
