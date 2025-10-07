"""Convert MGen Static IR to LLVM IR using llvmlite.

This module implements the IRVisitor pattern to traverse MGen's Static IR
and generate corresponding LLVM IR instructions.
"""

from typing import Any, Optional

from llvmlite import ir  # type: ignore[import-untyped]

from ...frontend.static_ir import (
    IRAssignment,
    IRBinaryOperation,
    IRBreak,
    IRContinue,
    IRDataType,
    IRExpression,
    IRFor,
    IRFunction,
    IRFunctionCall,
    IRIf,
    IRLiteral,
    IRModule,
    IRReturn,
    IRType,
    IRTypeDeclaration,
    IRVariable,
    IRVariableReference,
    IRVisitor,
    IRWhile,
)


class IRToLLVMConverter(IRVisitor):
    """Convert MGen Static IR to LLVM IR using the visitor pattern."""

    def __init__(self) -> None:
        """Initialize the LLVM IR converter."""
        self.module: ir.Module = ir.Module(name="mgen_module")
        # Set target triple to empty string to use native target
        # llvmlite will use the host's target triple
        self.module.triple = ""
        self.builder: Optional[ir.IRBuilder] = None
        self.func_symtab: dict[str, ir.Function] = {}
        self.var_symtab: dict[str, ir.AllocaInstr] = {}
        self.current_function: Optional[ir.Function] = None
        # Track current loop blocks for break/continue
        self.loop_exit_stack: list[ir.Block] = []
        self.loop_continue_stack: list[ir.Block] = []

    def visit_module(self, node: IRModule) -> ir.Module:
        """Convert IR module to LLVM module.

        Args:
            node: IR module to convert

        Returns:
            LLVM module with generated functions
        """
        # Generate type declarations first (for structs, etc.)
        for type_decl in node.type_declarations:
            type_decl.accept(self)

        # Generate functions
        for func in node.functions:
            func.accept(self)

        return self.module

    def visit_function(self, node: IRFunction) -> ir.Function:
        """Convert IR function to LLVM function.

        Args:
            node: IR function to convert

        Returns:
            LLVM function with generated body
        """
        # Map IRType → llvmlite type
        ret_type = self._convert_type(node.return_type)
        param_types = [self._convert_type(p.ir_type) for p in node.parameters]

        # Create LLVM function type and function
        func_type = ir.FunctionType(ret_type, param_types)
        func = ir.Function(self.module, func_type, node.name)

        # Store in symbol table
        self.func_symtab[node.name] = func
        self.current_function = func

        # Create entry block
        entry_block = func.append_basic_block(name="entry")
        self.builder = ir.IRBuilder(entry_block)

        # Clear variable symbol table for new function
        self.var_symtab = {}

        # Map parameters to LLVM function arguments
        for i, param in enumerate(node.parameters):
            # Allocate stack space for parameter (enables taking address)
            param_ptr = self.builder.alloca(func.args[i].type, name=param.name)
            self.builder.store(func.args[i], param_ptr)
            self.var_symtab[param.name] = param_ptr

        # Generate function body
        for stmt in node.body:
            stmt.accept(self)

        # Add implicit return if missing
        if not self.builder.block.is_terminated:
            if ret_type == ir.VoidType():
                self.builder.ret_void()
            else:
                # Return zero/null as default
                self.builder.ret(ir.Constant(ret_type, 0))

        return func

    def visit_variable(self, node: IRVariable) -> ir.AllocaInstr:
        """Visit a variable node (used for declarations).

        Args:
            node: IR variable to convert

        Returns:
            LLVM alloca instruction for the variable
        """
        if self.builder is None:
            raise RuntimeError("Builder not initialized - must be inside a function")

        var_type = self._convert_type(node.ir_type)
        var_ptr = self.builder.alloca(var_type, name=node.name)
        self.var_symtab[node.name] = var_ptr
        return var_ptr

    def visit_assignment(self, node: IRAssignment) -> None:
        """Convert IR assignment to LLVM store instruction.

        Args:
            node: IR assignment to convert
        """
        if self.builder is None:
            raise RuntimeError("Builder not initialized - must be inside a function")

        # Get or create variable
        if node.target.name not in self.var_symtab:
            # Allocate new variable
            var_type = self._convert_type(node.target.ir_type)
            var_ptr = self.builder.alloca(var_type, name=node.target.name)
            self.var_symtab[node.target.name] = var_ptr
        else:
            var_ptr = self.var_symtab[node.target.name]

        # Generate value expression if present
        if node.value:
            value = node.value.accept(self)
            self.builder.store(value, var_ptr)

    def visit_binary_operation(self, node: IRBinaryOperation) -> ir.Instruction:
        """Convert IR binary operation to LLVM instruction.

        Args:
            node: IR binary operation to convert

        Returns:
            LLVM instruction representing the operation
        """
        if self.builder is None:
            raise RuntimeError("Builder not initialized - must be inside a function")

        left = node.left.accept(self)
        right = node.right.accept(self)

        # Integer operations
        if node.result_type.base_type == IRDataType.INT:
            if node.operator == "+":
                return self.builder.add(left, right, name="add_tmp")
            elif node.operator == "-":
                return self.builder.sub(left, right, name="sub_tmp")
            elif node.operator == "*":
                return self.builder.mul(left, right, name="mul_tmp")
            elif node.operator == "/":
                return self.builder.sdiv(left, right, name="div_tmp")
            elif node.operator == "%":
                return self.builder.srem(left, right, name="rem_tmp")
            elif node.operator == "<<":
                return self.builder.shl(left, right, name="shl_tmp")
            elif node.operator == ">>":
                return self.builder.ashr(left, right, name="shr_tmp")
            elif node.operator == "&":
                return self.builder.and_(left, right, name="and_tmp")
            elif node.operator == "|":
                return self.builder.or_(left, right, name="or_tmp")
            elif node.operator == "^":
                return self.builder.xor(left, right, name="xor_tmp")

        # Float operations
        elif node.result_type.base_type == IRDataType.FLOAT:
            if node.operator == "+":
                return self.builder.fadd(left, right, name="fadd_tmp")
            elif node.operator == "-":
                return self.builder.fsub(left, right, name="fsub_tmp")
            elif node.operator == "*":
                return self.builder.fmul(left, right, name="fmul_tmp")
            elif node.operator == "/":
                return self.builder.fdiv(left, right, name="fdiv_tmp")

        # Boolean operations (comparisons)
        elif node.result_type.base_type == IRDataType.BOOL:
            # Determine operand types to choose correct comparison instruction
            left_type = node.left.result_type.base_type

            if left_type == IRDataType.INT:
                # Integer comparisons (icmp)
                if node.operator == "<":
                    return self.builder.icmp_signed("<", left, right, name="cmp_tmp")
                elif node.operator == "<=":
                    return self.builder.icmp_signed("<=", left, right, name="cmp_tmp")
                elif node.operator == ">":
                    return self.builder.icmp_signed(">", left, right, name="cmp_tmp")
                elif node.operator == ">=":
                    return self.builder.icmp_signed(">=", left, right, name="cmp_tmp")
                elif node.operator == "==":
                    return self.builder.icmp_signed("==", left, right, name="cmp_tmp")
                elif node.operator == "!=":
                    return self.builder.icmp_signed("!=", left, right, name="cmp_tmp")
            elif left_type == IRDataType.FLOAT:
                # Float comparisons (fcmp)
                if node.operator == "<":
                    return self.builder.fcmp_ordered("<", left, right, name="fcmp_tmp")
                elif node.operator == "<=":
                    return self.builder.fcmp_ordered("<=", left, right, name="fcmp_tmp")
                elif node.operator == ">":
                    return self.builder.fcmp_ordered(">", left, right, name="fcmp_tmp")
                elif node.operator == ">=":
                    return self.builder.fcmp_ordered(">=", left, right, name="fcmp_tmp")
                elif node.operator == "==":
                    return self.builder.fcmp_ordered("==", left, right, name="fcmp_tmp")
                elif node.operator == "!=":
                    return self.builder.fcmp_ordered("!=", left, right, name="fcmp_tmp")
            elif left_type == IRDataType.BOOL:
                # Boolean comparisons
                if node.operator == "==":
                    return self.builder.icmp_signed("==", left, right, name="cmp_tmp")
                elif node.operator == "!=":
                    return self.builder.icmp_signed("!=", left, right, name="cmp_tmp")
                elif node.operator == "and":
                    return self.builder.and_(left, right, name="and_tmp")
                elif node.operator == "or":
                    return self.builder.or_(left, right, name="or_tmp")

        raise NotImplementedError(f"Binary operator '{node.operator}' not implemented for type {node.result_type.base_type}")

    def visit_literal(self, node: IRLiteral) -> ir.Constant:
        """Convert IR literal to LLVM constant.

        Args:
            node: IR literal to convert

        Returns:
            LLVM constant value
        """
        llvm_type = self._convert_type(node.result_type)

        if node.result_type.base_type == IRDataType.INT:
            return ir.Constant(llvm_type, int(node.value))
        elif node.result_type.base_type == IRDataType.FLOAT:
            return ir.Constant(llvm_type, float(node.value))
        elif node.result_type.base_type == IRDataType.BOOL:
            return ir.Constant(llvm_type, 1 if node.value else 0)
        elif node.result_type.base_type == IRDataType.STRING:
            # String literals are handled as global constants
            # For now, return null pointer as placeholder
            return ir.Constant(llvm_type, None)
        elif node.result_type.base_type == IRDataType.VOID:
            # VOID literals shouldn't exist - this is likely a bug in IR generation
            # Return null pointer as workaround
            return ir.Constant(ir.IntType(8).as_pointer(), None)

        raise NotImplementedError(f"Literal type {node.result_type.base_type} not implemented (value={node.value})")

    def visit_variable_reference(self, node: IRVariableReference) -> ir.LoadInstr:
        """Convert IR variable reference to LLVM load instruction.

        Args:
            node: IR variable reference to convert

        Returns:
            LLVM load instruction
        """
        if self.builder is None:
            raise RuntimeError("Builder not initialized - must be inside a function")

        var_ptr = self.var_symtab.get(node.variable.name)
        if var_ptr is None:
            raise RuntimeError(f"Variable '{node.variable.name}' not found in symbol table")

        return self.builder.load(var_ptr, name=node.variable.name)

    def visit_function_call(self, node: IRFunctionCall) -> ir.CallInstr:
        """Convert IR function call to LLVM call instruction.

        Args:
            node: IR function call to convert

        Returns:
            LLVM call instruction
        """
        if self.builder is None:
            raise RuntimeError("Builder not initialized - must be inside a function")

        func = self.func_symtab.get(node.function_name)
        if func is None:
            raise RuntimeError(f"Function '{node.function_name}' not found in symbol table")

        args = [arg.accept(self) for arg in node.arguments]
        return self.builder.call(func, args, name="call_tmp")

    def visit_return(self, node: IRReturn) -> None:
        """Convert IR return statement to LLVM ret instruction.

        Args:
            node: IR return statement to convert
        """
        if self.builder is None:
            raise RuntimeError("Builder not initialized - must be inside a function")

        if node.value:
            ret_val = node.value.accept(self)
            self.builder.ret(ret_val)
        else:
            self.builder.ret_void()

    def visit_break(self, node: IRBreak) -> None:
        """Convert IR break statement to LLVM branch to loop exit.

        Args:
            node: IR break statement to convert
        """
        if self.builder is None:
            raise RuntimeError("Builder not initialized - must be inside a function")

        if not self.loop_exit_stack:
            raise RuntimeError("Break statement outside of loop")

        # Branch to the current loop's exit block
        self.builder.branch(self.loop_exit_stack[-1])

    def visit_continue(self, node: IRContinue) -> None:
        """Convert IR continue statement to LLVM branch to loop condition.

        Args:
            node: IR continue statement to convert
        """
        if self.builder is None:
            raise RuntimeError("Builder not initialized - must be inside a function")

        if not self.loop_continue_stack:
            raise RuntimeError("Continue statement outside of loop")

        # Branch to the current loop's condition block
        self.builder.branch(self.loop_continue_stack[-1])

    def visit_if(self, node: IRIf) -> None:
        """Convert IR if statement to LLVM basic blocks with branches.

        Args:
            node: IR if statement to convert
        """
        if self.builder is None or self.current_function is None:
            raise RuntimeError("Builder not initialized - must be inside a function")

        # Evaluate condition
        cond = node.condition.accept(self)

        # Create basic blocks
        then_block = self.current_function.append_basic_block("if.then")
        else_block = self.current_function.append_basic_block("if.else")
        merge_block = self.current_function.append_basic_block("if.merge")

        # Branch on condition
        self.builder.cbranch(cond, then_block, else_block)

        # Generate then block
        self.builder.position_at_end(then_block)
        for stmt in node.then_body:
            stmt.accept(self)
        if not self.builder.block.is_terminated:
            self.builder.branch(merge_block)

        # Generate else block
        self.builder.position_at_end(else_block)
        for stmt in node.else_body:
            stmt.accept(self)
        if not self.builder.block.is_terminated:
            self.builder.branch(merge_block)

        # Continue at merge point
        self.builder.position_at_end(merge_block)

    def visit_while(self, node: IRWhile) -> None:
        """Convert IR while loop to LLVM loop blocks.

        Args:
            node: IR while loop to convert
        """
        if self.builder is None or self.current_function is None:
            raise RuntimeError("Builder not initialized - must be inside a function")

        # Create basic blocks
        cond_block = self.current_function.append_basic_block("while.cond")
        body_block = self.current_function.append_basic_block("while.body")
        exit_block = self.current_function.append_basic_block("while.exit")

        # Track loop blocks for break/continue
        self.loop_exit_stack.append(exit_block)
        self.loop_continue_stack.append(cond_block)

        # Jump to condition check
        self.builder.branch(cond_block)

        # Generate condition block
        self.builder.position_at_end(cond_block)
        cond = node.condition.accept(self)
        self.builder.cbranch(cond, body_block, exit_block)

        # Generate body block
        self.builder.position_at_end(body_block)
        for stmt in node.body:
            stmt.accept(self)
        if not self.builder.block.is_terminated:
            self.builder.branch(cond_block)  # Loop back

        # Pop loop blocks from stack
        self.loop_exit_stack.pop()
        self.loop_continue_stack.pop()

        # Continue after loop
        self.builder.position_at_end(exit_block)

    def visit_for(self, node: IRFor) -> None:
        """Convert IR for loop (range-based) to LLVM loop blocks.

        Args:
            node: IR for loop to convert
        """
        if self.builder is None or self.current_function is None:
            raise RuntimeError("Builder not initialized - must be inside a function")

        # Allocate loop variable
        loop_var_type = self._convert_type(node.variable.ir_type)
        loop_var_ptr = self.builder.alloca(loop_var_type, name=node.variable.name)
        self.var_symtab[node.variable.name] = loop_var_ptr

        # Initialize loop variable with start value
        start_val = node.start.accept(self)
        self.builder.store(start_val, loop_var_ptr)

        # Create basic blocks
        cond_block = self.current_function.append_basic_block("for.cond")
        body_block = self.current_function.append_basic_block("for.body")
        inc_block = self.current_function.append_basic_block("for.inc")
        exit_block = self.current_function.append_basic_block("for.exit")

        # Track loop blocks for break/continue
        self.loop_exit_stack.append(exit_block)
        self.loop_continue_stack.append(inc_block)  # continue jumps to increment

        # Jump to condition
        self.builder.branch(cond_block)

        # Condition: loop_var < end
        self.builder.position_at_end(cond_block)
        loop_var_val = self.builder.load(loop_var_ptr)
        end_val = node.end.accept(self)
        cond = self.builder.icmp_signed("<", loop_var_val, end_val, name="for.cond")
        self.builder.cbranch(cond, body_block, exit_block)

        # Body
        self.builder.position_at_end(body_block)
        for stmt in node.body:
            stmt.accept(self)
        if not self.builder.block.is_terminated:
            self.builder.branch(inc_block)

        # Increment
        self.builder.position_at_end(inc_block)
        loop_var_val = self.builder.load(loop_var_ptr)
        if node.step:
            step_val = node.step.accept(self)
        else:
            step_val = ir.Constant(loop_var_type, 1)
        next_val = self.builder.add(loop_var_val, step_val, name="for.inc")
        self.builder.store(next_val, loop_var_ptr)
        self.builder.branch(cond_block)

        # Pop loop blocks from stack
        self.loop_exit_stack.pop()
        self.loop_continue_stack.pop()

        # Exit
        self.builder.position_at_end(exit_block)

    def visit_type_declaration(self, node: IRTypeDeclaration) -> None:
        """Visit a type declaration node (structs, unions, enums).

        Args:
            node: IR type declaration to convert
        """
        # Type declarations will be implemented when needed for complex types
        # For now, we focus on basic types
        pass

    def _convert_type(self, ir_type: IRType) -> ir.Type:
        """Map IRType to llvmlite type.

        Args:
            ir_type: MGen IR type

        Returns:
            Corresponding llvmlite type
        """
        # Base type mapping
        type_mapping = {
            IRDataType.VOID: ir.VoidType(),
            IRDataType.INT: ir.IntType(64),  # 64-bit integer
            IRDataType.FLOAT: ir.DoubleType(),  # double precision
            IRDataType.BOOL: ir.IntType(1),  # i1
            IRDataType.STRING: ir.IntType(8).as_pointer(),  # char*
        }

        base = type_mapping.get(ir_type.base_type, ir.VoidType())

        # Handle pointers
        if ir_type.is_pointer or ir_type.pointer_depth > 0:
            depth = ir_type.pointer_depth or 1
            for _ in range(depth):
                base = base.as_pointer()

        # Handle arrays
        if ir_type.array_dimensions:
            # Build array types from innermost to outermost
            for dim in reversed(ir_type.array_dimensions):
                if dim:
                    base = ir.ArrayType(base, dim)
                else:
                    # Unknown dimension, use pointer
                    base = base.as_pointer()

        return base
