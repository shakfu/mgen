"""Convert MGen Static IR to LLVM IR using llvmlite.

This module implements the IRVisitor pattern to traverse MGen's Static IR
and generate corresponding LLVM IR instructions.
"""

from typing import Any, Optional, Union

from llvmlite import ir  # type: ignore[import-untyped]

from ...frontend.static_ir import (
    IRAssignment,
    IRBinaryOperation,
    IRBreak,
    IRContinue,
    IRDataType,
    IRExpression,
    IRExpressionStatement,
    IRFor,
    IRFunction,
    IRFunctionCall,
    IRIf,
    IRLiteral,
    IRModule,
    IRReturn,
    IRType,
    IRTypeCast,
    IRTypeDeclaration,
    IRVariable,
    IRVariableReference,
    IRVisitor,
    IRWhile,
)
from .runtime_decls import LLVMRuntimeDeclarations


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
        self.global_symtab: dict[str, ir.GlobalVariable] = {}
        self.current_function: Optional[ir.Function] = None
        # Track current loop blocks for break/continue
        self.loop_exit_stack: list[ir.Block] = []
        self.loop_continue_stack: list[ir.Block] = []
        # Runtime declarations for C library
        self.runtime = LLVMRuntimeDeclarations(self.module)

    def visit_module(self, node: IRModule) -> ir.Module:
        """Convert IR module to LLVM module.

        Args:
            node: IR module to convert

        Returns:
            LLVM module with generated functions
        """
        # Declare runtime library functions first
        self.runtime.declare_all()

        # Generate type declarations first (for structs, etc.)
        for type_decl in node.type_declarations:
            type_decl.accept(self)

        # Generate global variables
        for global_var in node.global_variables:
            global_var.accept(self)

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

    def visit_variable(self, node: IRVariable) -> Union[ir.AllocaInstr, ir.GlobalVariable]:
        """Visit a variable node (used for declarations).

        Args:
            node: IR variable to convert

        Returns:
            LLVM alloca instruction for local variables or GlobalVariable for globals
        """
        var_type = self._convert_type(node.ir_type)

        # If builder is None, this is a global variable
        if self.builder is None:
            # Create global variable with initializer
            if node.initial_value is not None:
                initial_value = node.initial_value.accept(self)
            else:
                # Default initialization to zero
                if var_type == ir.IntType(64):
                    initial_value = ir.Constant(ir.IntType(64), 0)
                elif var_type == ir.DoubleType():
                    initial_value = ir.Constant(ir.DoubleType(), 0.0)
                elif var_type == ir.IntType(1):
                    initial_value = ir.Constant(ir.IntType(1), 0)
                else:
                    raise NotImplementedError(f"Default initialization for type {var_type} not implemented")

            global_var = ir.GlobalVariable(self.module, var_type, name=node.name)
            global_var.initializer = initial_value
            global_var.linkage = "internal"  # Make it module-private
            self.global_symtab[node.name] = global_var
            return global_var
        else:
            # Local variable - use alloca
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

        # Check if it's a global variable first
        if node.target.name in self.global_symtab:
            var_ptr = self.global_symtab[node.target.name]
        elif node.target.name not in self.var_symtab:
            # Allocate new local variable
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

        # For short-circuit operators (and, or), we need special handling
        # to avoid evaluating the right side when not necessary
        if node.result_type.base_type == IRDataType.BOOL and node.operator in ("and", "or"):
            return self._visit_short_circuit_boolean(node)

        # For all other operators, evaluate both sides immediately
        left = node.left.accept(self)
        right = node.right.accept(self)

        # String operations
        if node.left.result_type.base_type == IRDataType.STRING:
            if node.operator == "+":
                # String concatenation using C library functions
                return self._concat_strings(left, right)

        # Integer operations
        if node.result_type.base_type == IRDataType.INT:
            if node.operator == "+":
                return self.builder.add(left, right, name="add_tmp")
            elif node.operator == "-":
                return self.builder.sub(left, right, name="sub_tmp")
            elif node.operator == "*":
                return self.builder.mul(left, right, name="mul_tmp")
            elif node.operator == "/" or node.operator == "//":
                return self.builder.sdiv(left, right, name="div_tmp")
            elif node.operator == "%":
                # Python modulo uses floored division, C uses truncated division
                # To convert: if remainder and divisor have different signs, add divisor to remainder
                c_rem = self.builder.srem(left, right, name="c_rem")

                # Check if signs differ: (c_rem < 0) != (right < 0)
                zero = ir.Constant(ir.IntType(64), 0)
                rem_neg = self.builder.icmp_signed("<", c_rem, zero, name="rem_neg")
                divisor_neg = self.builder.icmp_signed("<", right, zero, name="divisor_neg")
                signs_differ = self.builder.xor(rem_neg, divisor_neg, name="signs_differ")

                # Check if remainder is non-zero
                rem_nonzero = self.builder.icmp_signed("!=", c_rem, zero, name="rem_nonzero")

                # Adjust if signs differ AND remainder is non-zero
                need_adjust = self.builder.and_(signs_differ, rem_nonzero, name="need_adjust")

                # result = need_adjust ? (c_rem + right) : c_rem
                adjusted = self.builder.add(c_rem, right, name="adjusted")
                result = self.builder.select(need_adjust, adjusted, c_rem, name="mod_tmp")
                return result
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
                # Boolean comparisons (and/or handled separately via _visit_short_circuit_boolean)
                if node.operator == "==":
                    return self.builder.icmp_signed("==", left, right, name="cmp_tmp")
                elif node.operator == "!=":
                    return self.builder.icmp_signed("!=", left, right, name="cmp_tmp")

        raise NotImplementedError(f"Binary operator '{node.operator}' not implemented for type {node.result_type.base_type}")

    def _visit_short_circuit_boolean(self, node: IRBinaryOperation) -> ir.Instruction:
        """Handle short-circuit evaluation for 'and' and 'or' operators.

        Args:
            node: IR binary operation with 'and' or 'or' operator

        Returns:
            LLVM instruction representing the short-circuit boolean result
        """
        if self.builder is None or self.current_function is None:
            raise RuntimeError("Builder not initialized - must be inside a function")

        # Evaluate left side first
        left = node.left.accept(self)
        left_end_block = self.builder.block  # Block where left evaluation ended

        if node.operator == "and":
            # Short-circuit AND: if left is false, result is false without evaluating right
            eval_right_block = self.current_function.append_basic_block("and.eval_right")
            merge_block = self.current_function.append_basic_block("and.merge")

            # Branch: if left is true, evaluate right; otherwise skip to merge
            self.builder.cbranch(left, eval_right_block, merge_block)

            # Evaluate right side (only if left was true)
            self.builder.position_at_end(eval_right_block)
            right = node.right.accept(self)
            eval_right_end_block = self.builder.block  # May have changed during right evaluation
            self.builder.branch(merge_block)

            # Merge block: use phi to select result
            self.builder.position_at_end(merge_block)
            phi = self.builder.phi(ir.IntType(1), name="and_tmp")
            phi.add_incoming(ir.Constant(ir.IntType(1), 0), left_end_block)  # Left was false
            phi.add_incoming(right, eval_right_end_block)  # Right result
            return phi

        elif node.operator == "or":
            # Short-circuit OR: if left is true, result is true without evaluating right
            eval_right_block = self.current_function.append_basic_block("or.eval_right")
            merge_block = self.current_function.append_basic_block("or.merge")

            # Branch: if left is false, evaluate right; otherwise skip to merge
            self.builder.cbranch(left, merge_block, eval_right_block)

            # Evaluate right side (only if left was false)
            self.builder.position_at_end(eval_right_block)
            right = node.right.accept(self)
            eval_right_end_block = self.builder.block  # May have changed during right evaluation
            self.builder.branch(merge_block)

            # Merge block: use phi to select result
            self.builder.position_at_end(merge_block)
            phi = self.builder.phi(ir.IntType(1), name="or_tmp")
            phi.add_incoming(ir.Constant(ir.IntType(1), 1), left_end_block)  # Left was true
            phi.add_incoming(right, eval_right_end_block)  # Right result
            return phi

        else:
            raise RuntimeError(f"Unexpected operator in short-circuit: {node.operator}")

    def visit_literal(self, node: IRLiteral) -> Union[ir.Constant, ir.CallInstr]:
        """Convert IR literal to LLVM constant or initialization call.

        Args:
            node: IR literal to convert

        Returns:
            LLVM constant value or call instruction for complex types
        """
        llvm_type = self._convert_type(node.result_type)

        if node.result_type.base_type == IRDataType.LIST:
            # List literal - allocate and initialize
            if self.builder is None:
                raise RuntimeError("Builder not initialized - must be inside a function")

            vec_int_type = self.runtime.get_vec_int_type()
            vec_int_init_ptr_func = self.runtime.get_function("vec_int_init_ptr")
            vec_int_push_func = self.runtime.get_function("vec_int_push")

            # Allocate space for the vec_int struct on stack
            vec_ptr = self.builder.alloca(vec_int_type, name="list_tmp")

            # Initialize it by calling vec_int_init_ptr() which takes a pointer
            self.builder.call(vec_int_init_ptr_func, [vec_ptr], name="")

            # If list has elements, push them
            if isinstance(node.value, list) and len(node.value) > 0:
                for element_expr in node.value:
                    # Visit the element expression to get its LLVM value
                    element_val = element_expr.accept(self)
                    # Push the element to the list
                    self.builder.call(vec_int_push_func, [vec_ptr, element_val], name="")

            # Return the pointer
            return vec_ptr
        elif node.result_type.base_type == IRDataType.INT:
            return ir.Constant(llvm_type, int(node.value))
        elif node.result_type.base_type == IRDataType.FLOAT:
            return ir.Constant(llvm_type, float(node.value))
        elif node.result_type.base_type == IRDataType.BOOL:
            return ir.Constant(llvm_type, 1 if node.value else 0)
        elif node.result_type.base_type == IRDataType.STRING:
            # String literals are stored as global constants
            # Create a null-terminated string
            str_value = str(node.value)
            str_bytes = (str_value + '\0').encode('utf-8')
            str_const = ir.Constant(ir.ArrayType(ir.IntType(8), len(str_bytes)), bytearray(str_bytes))

            # Create global variable for the string
            str_global = ir.GlobalVariable(self.module, str_const.type, name=f"str_{len(self.module.globals)}")
            str_global.linkage = 'internal'
            str_global.global_constant = True
            str_global.initializer = str_const

            # Return pointer to the string (i8*)
            if self.builder is not None:
                return self.builder.gep(str_global, [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), 0)])
            else:
                # During global variable initialization, return the global itself
                return str_global
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

        # Check global variables first, then local
        var_ptr = self.global_symtab.get(node.variable.name)
        if var_ptr is None:
            var_ptr = self.var_symtab.get(node.variable.name)
        if var_ptr is None:
            raise RuntimeError(f"Variable '{node.variable.name}' not found in symbol table")

        return self.builder.load(var_ptr, name=node.variable.name)

    def _get_or_create_c_function(self, name: str, ret_type: ir.Type, arg_types: list[ir.Type], var_arg: bool = False) -> ir.Function:
        """Get or create a C library function declaration.

        Args:
            name: Name of the C function
            ret_type: Return type
            arg_types: List of argument types
            var_arg: Whether function has variable arguments

        Returns:
            LLVM function declaration
        """
        if name in self.func_symtab:
            return self.func_symtab[name]

        func_ty = ir.FunctionType(ret_type, arg_types, var_arg=var_arg)
        func = ir.Function(self.module, func_ty, name=name)
        self.func_symtab[name] = func
        return func

    def _concat_strings(self, left: ir.Value, right: ir.Value) -> ir.Value:
        """Concatenate two strings using C library functions.

        Args:
            left: First string (i8*)
            right: Second string (i8*)

        Returns:
            Concatenated string (i8*)
        """
        if self.builder is None:
            raise RuntimeError("Builder not initialized")

        # Declare C library functions if not already declared
        i8_ptr = ir.IntType(8).as_pointer()
        i64 = ir.IntType(64)

        strlen_func = self._get_or_create_c_function("strlen", i64, [i8_ptr])
        malloc_func = self._get_or_create_c_function("malloc", i8_ptr, [i64])
        strcpy_func = self._get_or_create_c_function("strcpy", i8_ptr, [i8_ptr, i8_ptr])
        strcat_func = self._get_or_create_c_function("strcat", i8_ptr, [i8_ptr, i8_ptr])

        # Get lengths of both strings
        left_len = self.builder.call(strlen_func, [left], name="left_len")
        right_len = self.builder.call(strlen_func, [right], name="right_len")

        # Calculate total length (left_len + right_len + 1 for null terminator)
        total_len = self.builder.add(left_len, right_len, name="total_len")
        total_len_plus_null = self.builder.add(total_len, ir.Constant(i64, 1), name="total_len_plus_null")

        # Allocate memory for result
        result_ptr = self.builder.call(malloc_func, [total_len_plus_null], name="result_ptr")

        # Copy first string
        self.builder.call(strcpy_func, [result_ptr, left], name="strcpy_tmp")

        # Concatenate second string
        self.builder.call(strcat_func, [result_ptr, right], name="strcat_tmp")

        return result_ptr

    def _get_or_create_builtin(self, name: str, arg_types: list[ir.Type]) -> ir.Function:
        """Get or create a builtin function declaration.

        Args:
            name: Name of the builtin function
            arg_types: List of argument types

        Returns:
            LLVM function declaration for the builtin
        """
        # Check if already declared
        if name in self.func_symtab:
            return self.func_symtab[name]

        # Create builtin function declarations
        if name == "print":
            # print() uses printf internally
            # For simplicity, we'll handle integer printing first
            # Signature: int printf(i8*, ...)
            printf_ty = ir.FunctionType(ir.IntType(32), [ir.IntType(8).as_pointer()], var_arg=True)
            printf_func = ir.Function(self.module, printf_ty, name="printf")
            self.func_symtab["printf"] = printf_func
            return printf_func
        else:
            raise NotImplementedError(f"Builtin function '{name}' not implemented")

    def visit_function_call(self, node: IRFunctionCall) -> ir.CallInstr:
        """Convert IR function call to LLVM call instruction.

        Args:
            node: IR function call to convert

        Returns:
            LLVM call instruction
        """
        if self.builder is None:
            raise RuntimeError("Builder not initialized - must be inside a function")

        # Handle method calls (from IR builder)
        if node.function_name == "__method_append__":
            # list.append(value) -> vec_int_push(list_ptr, value)
            if len(node.arguments) != 2:
                raise RuntimeError("append() requires exactly 2 arguments (list and value)")

            list_ptr = node.arguments[0].accept(self)  # Already a pointer
            value = node.arguments[1].accept(self)

            # Get vec_int_push function
            vec_int_push_func = self.runtime.get_function("vec_int_push")

            # Call vec_int_push - it modifies the list in place
            self.builder.call(vec_int_push_func, [list_ptr, value], name="")

            # Return the pointer (unchanged, since append mutates in place)
            return list_ptr

        elif node.function_name == "__getitem__":
            # list[index] -> vec_int_at(list_ptr, index)
            if len(node.arguments) != 2:
                raise RuntimeError("__getitem__() requires exactly 2 arguments (list and index)")

            list_ptr = node.arguments[0].accept(self)  # Already a pointer
            index = node.arguments[1].accept(self)

            # Get vec_int_at function
            vec_int_at_func = self.runtime.get_function("vec_int_at")

            # Call vec_int_at
            return self.builder.call(vec_int_at_func, [list_ptr, index], name="list_at")

        elif node.function_name == "__setitem__":
            # list[index] = value -> vec_int_set(list_ptr, index, value)
            if len(node.arguments) != 3:
                raise RuntimeError("__setitem__() requires exactly 3 arguments (list, index, value)")

            list_ptr = node.arguments[0].accept(self)  # Already a pointer
            index = node.arguments[1].accept(self)
            value = node.arguments[2].accept(self)

            # Get vec_int_set function
            vec_int_set_func = self.runtime.get_function("vec_int_set")

            # Call vec_int_set - it modifies the list in place
            return self.builder.call(vec_int_set_func, [list_ptr, index, value], name="")

        # Handle builtin functions
        elif node.function_name == "len":
            # len() function - use strlen for strings, vec_int_size for lists
            if len(node.arguments) != 1:
                raise NotImplementedError("len() requires exactly one argument")

            arg = node.arguments[0]
            llvm_arg = arg.accept(self)

            if arg.result_type.base_type == IRDataType.STRING:
                # Use C strlen function
                i8_ptr = ir.IntType(8).as_pointer()
                i64 = ir.IntType(64)
                strlen_func = self._get_or_create_c_function("strlen", i64, [i8_ptr])
                return self.builder.call(strlen_func, [llvm_arg], name="len_tmp")
            elif arg.result_type.base_type == IRDataType.LIST:
                # Use vec_int_size function from runtime
                # llvm_arg is already a pointer
                vec_int_size_func = self.runtime.get_function("vec_int_size")
                return self.builder.call(vec_int_size_func, [llvm_arg], name="len_tmp")
            else:
                raise NotImplementedError(f"len() for type {arg.result_type.base_type} not implemented")

        elif node.function_name == "print":
            # Get or create printf declaration
            arg_types = [arg.result_type for arg in node.arguments]
            printf_func = self._get_or_create_builtin("print", arg_types)

            # Create format string based on argument type
            if len(node.arguments) == 1:
                arg = node.arguments[0]
                if arg.result_type.base_type == IRDataType.INT:
                    fmt_str = "%lld\\0A\\00"  # %lld\n\0
                elif arg.result_type.base_type == IRDataType.FLOAT:
                    fmt_str = "%f\\0A\\00"  # %f\n\0
                elif arg.result_type.base_type == IRDataType.BOOL:
                    fmt_str = "%d\\0A\\00"  # %d\n\0
                elif arg.result_type.base_type == IRDataType.STRING:
                    fmt_str = "%s\\0A\\00"  # %s\n\0
                else:
                    raise NotImplementedError(f"Print for type {arg.result_type.base_type} not implemented")

                # Create global string constant for format
                fmt_const = ir.Constant(ir.ArrayType(ir.IntType(8), len(fmt_str.encode('utf-8').decode('unicode_escape'))),
                                       bytearray(fmt_str.encode('utf-8').decode('unicode_escape').encode('utf-8')))
                fmt_global = ir.GlobalVariable(self.module, fmt_const.type, name=f"fmt_{len(self.module.globals)}")
                fmt_global.linkage = 'internal'
                fmt_global.global_constant = True
                fmt_global.initializer = fmt_const

                # Get pointer to the format string
                fmt_ptr = self.builder.gep(fmt_global, [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), 0)])

                # Evaluate argument and call printf
                llvm_arg = arg.accept(self)
                return self.builder.call(printf_func, [fmt_ptr, llvm_arg], name="print_tmp")
            else:
                raise NotImplementedError("Print with multiple arguments not implemented")

        # Regular function call
        func = self.func_symtab.get(node.function_name)
        if func is None:
            raise RuntimeError(f"Function '{node.function_name}' not found in symbol table")

        args = [arg.accept(self) for arg in node.arguments]
        return self.builder.call(func, args, name="call_tmp")

    def visit_type_cast(self, node: IRTypeCast) -> ir.Instruction:
        """Convert IR type cast to LLVM cast instruction.

        Args:
            node: IR type cast to convert

        Returns:
            LLVM cast instruction
        """
        if self.builder is None:
            raise RuntimeError("Builder not initialized - must be inside a function")

        value = node.value.accept(self)
        source_type = node.value.result_type.base_type
        target_type = node.result_type.base_type

        # INT to FLOAT
        if source_type == IRDataType.INT and target_type == IRDataType.FLOAT:
            llvm_target = self._convert_type(node.result_type)
            return self.builder.sitofp(value, llvm_target, name="cast_tmp")

        # FLOAT to INT
        elif source_type == IRDataType.FLOAT and target_type == IRDataType.INT:
            llvm_target = self._convert_type(node.result_type)
            return self.builder.fptosi(value, llvm_target, name="cast_tmp")

        # INT to BOOL
        elif source_type == IRDataType.INT and target_type == IRDataType.BOOL:
            zero = ir.Constant(ir.IntType(64), 0)
            return self.builder.icmp_signed("!=", value, zero, name="cast_tmp")

        # FLOAT to BOOL
        elif source_type == IRDataType.FLOAT and target_type == IRDataType.BOOL:
            zero = ir.Constant(ir.DoubleType(), 0.0)
            return self.builder.fcmp_ordered("!=", value, zero, name="cast_tmp")

        # BOOL to INT
        elif source_type == IRDataType.BOOL and target_type == IRDataType.INT:
            llvm_target = self._convert_type(node.result_type)
            return self.builder.zext(value, llvm_target, name="cast_tmp")

        # Same type - no cast needed
        elif source_type == target_type:
            return value

        # Unsupported cast
        else:
            raise NotImplementedError(f"Type cast from {source_type} to {target_type} not implemented")

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

    def visit_expression_statement(self, node: IRExpressionStatement) -> None:
        """Convert IR expression statement to LLVM.

        Args:
            node: IR expression statement to convert
        """
        if self.builder is None:
            raise RuntimeError("Builder not initialized - must be inside a function")

        # Evaluate the expression (e.g., void function call)
        # The expression's side effects (like function calls) will be executed
        node.expression.accept(self)

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

        # Condition: loop_var < end (or > end for negative step)
        self.builder.position_at_end(cond_block)
        loop_var_val = self.builder.load(loop_var_ptr)
        end_val = node.end.accept(self)

        # Determine comparison operator based on step value
        # For negative steps, use >, for positive steps use <
        from ...frontend.static_ir import IRBinaryOperation, IRLiteral

        def is_negative_step(step: Optional[IRExpression]) -> bool:
            """Check if step is a negative constant."""
            if step is None:
                return False
            if isinstance(step, IRLiteral):
                return isinstance(step.value, int) and step.value < 0
            # Handle negative literals encoded as 0 - N
            if isinstance(step, IRBinaryOperation) and step.operator == "-":
                if isinstance(step.left, IRLiteral) and step.left.value == 0:
                    if isinstance(step.right, IRLiteral) and isinstance(step.right.value, int):
                        return step.right.value > 0
            return False

        comparison_op = ">" if is_negative_step(node.step) else "<"
        cond = self.builder.icmp_signed(comparison_op, loop_var_val, end_val, name="for.cond")
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
        # Handle list types (LIST<T>)
        if ir_type.base_type == IRDataType.LIST:
            # Lists are represented as pointers to vec_int structs
            # This allows proper mutation semantics (append modifies in place)
            # TODO: Support other element types (vec_double, vec_str, etc.)
            return self.runtime.get_vec_int_type().as_pointer()

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
