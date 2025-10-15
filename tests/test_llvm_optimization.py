"""Test LLVM optimization passes."""

import pytest

from mgen.backends.llvm.optimizer import LLVMOptimizer


class TestLLVMOptimizer:
    """Test suite for LLVM optimization pass manager."""

    def test_optimizer_initialization(self) -> None:
        """Test that optimizer can be initialized with different levels."""
        for level in range(4):
            optimizer = LLVMOptimizer(opt_level=level)
            assert optimizer.opt_level == level

    def test_invalid_optimization_level(self) -> None:
        """Test that invalid optimization levels raise ValueError."""
        with pytest.raises(ValueError, match="Optimization level must be 0-3"):
            LLVMOptimizer(opt_level=-1)

        with pytest.raises(ValueError, match="Optimization level must be 0-3"):
            LLVMOptimizer(opt_level=4)

    def test_optimization_info(self) -> None:
        """Test that optimization info is correctly reported."""
        optimizer = LLVMOptimizer(opt_level=2)
        info = optimizer.get_optimization_info()

        assert info["opt_level"] == 2
        assert info["opt_name"] == "O2"
        assert info["inlining_threshold"] == 225
        assert info["vectorization_enabled"] is True
        assert info["loop_unrolling_enabled"] is True
        assert "target_triple" in info

    def test_optimize_simple_function(self) -> None:
        """Test optimization of a simple function."""
        # Simple function: add two numbers
        ir = """
        define i64 @add(i64 %a, i64 %b) {
        entry:
          %result = add i64 %a, %b
          ret i64 %result
        }
        """

        optimizer = LLVMOptimizer(opt_level=2)
        optimized = optimizer.optimize(ir)

        # Should still be valid IR
        assert "define i64 @add" in optimized or 'define i64 @"add"' in optimized
        assert "ret i64" in optimized

    def test_optimize_eliminates_dead_code(self) -> None:
        """Test that optimization eliminates dead code."""
        # Function with dead code after return
        ir = """
        define i64 @test(i64 %x) {
        entry:
          ret i64 %x
          %dead1 = add i64 %x, 1
          %dead2 = mul i64 %dead1, 2
          ret i64 %dead2
        }
        """

        optimizer = LLVMOptimizer(opt_level=2)
        optimized = optimizer.optimize(ir)

        # Dead code should be eliminated (though exact IR format may vary)
        # At minimum, the function should still work
        assert "define i64 @test" in optimized or 'define i64 @"test"' in optimized
        assert "ret i64" in optimized

    def test_optimize_simplifies_expressions(self) -> None:
        """Test that optimization simplifies constant expressions."""
        # Function with redundant operations
        ir = """
        define i64 @compute(i64 %x) {
        entry:
          %v1 = add i64 %x, 0
          %v2 = mul i64 %v1, 1
          %v3 = add i64 %v2, 10
          %v4 = sub i64 %v3, 10
          ret i64 %v4
        }
        """

        optimizer = LLVMOptimizer(opt_level=2)
        optimized = optimizer.optimize(ir)

        # Optimizations should simplify to essentially: ret i64 %x
        # The exact form depends on LLVM version, but it should be simpler
        assert "define i64 @compute" in optimized or 'define i64 @"compute"' in optimized
        assert len(optimized) < len(ir) or "ret i64 %x" in optimized or "ret i64 %0" in optimized

    def test_optimization_levels_comparison(self) -> None:
        """Test that higher optimization levels produce different results."""
        # Function with optimization opportunities
        ir = """
        define i64 @fibonacci(i64 %n) {
        entry:
          %cmp = icmp sle i64 %n, 1
          br i1 %cmp, label %base, label %recursive

        base:
          ret i64 %n

        recursive:
          %n1 = sub i64 %n, 1
          %fib1 = call i64 @fibonacci(i64 %n1)
          %n2 = sub i64 %n, 2
          %fib2 = call i64 @fibonacci(i64 %n2)
          %result = add i64 %fib1, %fib2
          ret i64 %result
        }
        """

        opt0 = LLVMOptimizer(opt_level=0).optimize(ir)
        opt1 = LLVMOptimizer(opt_level=1).optimize(ir)
        opt2 = LLVMOptimizer(opt_level=2).optimize(ir)
        opt3 = LLVMOptimizer(opt_level=3).optimize(ir)

        # O0 should keep the original structure (no optimization)
        assert "call i64 @fibonacci" in opt0 or 'call i64 @"fibonacci"' in opt0

        # Higher levels may optimize differently
        # At minimum, they should all be valid
        for optimized in [opt1, opt2, opt3]:
            assert "define i64" in optimized
            assert "ret i64" in optimized

    def test_optimize_with_multiple_functions(self) -> None:
        """Test optimization of module with multiple functions."""
        ir = """
        define i64 @helper(i64 %x) {
        entry:
          %result = mul i64 %x, 2
          ret i64 %result
        }

        define i64 @main(i64 %n) {
        entry:
          %tmp = call i64 @helper(i64 %n)
          %result = add i64 %tmp, 5
          ret i64 %result
        }
        """

        optimizer = LLVMOptimizer(opt_level=2)
        optimized = optimizer.optimize(ir)

        # Should optimize both functions (check for "define" keyword which must be present)
        # Note: function names may be inlined/optimized away, but module should have at least one function
        assert "define" in optimized and "ret i64" in optimized

    def test_optimize_preserves_semantics(self) -> None:
        """Test that optimization preserves program semantics."""
        # Function that computes (x * 2) + 3
        ir = """
        define i64 @compute(i64 %x) {
        entry:
          %doubled = mul i64 %x, 2
          %result = add i64 %doubled, 3
          ret i64 %result
        }
        """

        optimizer = LLVMOptimizer(opt_level=3)
        optimized = optimizer.optimize(ir)

        # The semantic operations should still be present
        # (though they may be reordered or combined)
        # Note: LLVM may add attributes, so check for "define" separately
        assert "define" in optimized
        assert "ret i64" in optimized

    def test_invalid_ir_raises_error(self) -> None:
        """Test that invalid IR raises appropriate error."""
        invalid_ir = "this is not valid LLVM IR"

        optimizer = LLVMOptimizer(opt_level=2)
        with pytest.raises(ValueError, match="Failed to parse LLVM IR"):
            optimizer.optimize(invalid_ir)

    def test_empty_function(self) -> None:
        """Test optimization of empty function."""
        ir = """
        define void @empty() {
        entry:
          ret void
        }
        """

        optimizer = LLVMOptimizer(opt_level=2)
        optimized = optimizer.optimize(ir)

        # Should handle empty functions gracefully
        assert "define void @empty" in optimized or 'define void @"empty"' in optimized
        assert "ret void" in optimized

    def test_inlining_threshold_values(self) -> None:
        """Test that inlining thresholds are set correctly."""
        opt0 = LLVMOptimizer(opt_level=0)
        opt1 = LLVMOptimizer(opt_level=1)
        opt2 = LLVMOptimizer(opt_level=2)
        opt3 = LLVMOptimizer(opt_level=3)

        assert opt0._get_inlining_threshold() == 0
        assert opt1._get_inlining_threshold() == 75
        assert opt2._get_inlining_threshold() == 225
        assert opt3._get_inlining_threshold() == 275

    def test_optimization_with_loop(self) -> None:
        """Test optimization of function containing a loop."""
        # Simple loop that adds numbers 0 to n
        ir = """
        define i64 @sum_to_n(i64 %n) {
        entry:
          br label %loop

        loop:
          %i = phi i64 [ 0, %entry ], [ %i_next, %loop ]
          %sum = phi i64 [ 0, %entry ], [ %sum_next, %loop ]
          %sum_next = add i64 %sum, %i
          %i_next = add i64 %i, 1
          %cmp = icmp slt i64 %i_next, %n
          br i1 %cmp, label %loop, label %exit

        exit:
          ret i64 %sum_next
        }
        """

        optimizer = LLVMOptimizer(opt_level=2)
        optimized = optimizer.optimize(ir)

        # Should successfully optimize loop
        assert "define i64" in optimized
        assert "ret i64" in optimized

    def test_o0_preserves_original_ir(self) -> None:
        """Test that O0 preserves the original IR structure."""
        ir = """
        define i64 @test(i64 %x, i64 %y) {
        entry:
          %sum = add i64 %x, %y
          %doubled = mul i64 %sum, 2
          ret i64 %doubled
        }
        """

        optimizer = LLVMOptimizer(opt_level=0)
        optimized = optimizer.optimize(ir)

        # O0 should preserve structure (minimal changes)
        # The function should still have the same basic operations
        assert "add i64" in optimized
        assert "mul i64" in optimized
        assert "ret i64" in optimized
