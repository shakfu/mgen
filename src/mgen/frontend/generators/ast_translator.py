"""Python-to-C AST Translator

Converts Python AST nodes to C code using the CFile library.
This module implements comprehensive translation of Python constructs
to their C equivalents.
"""

import ast
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from cfile import CFactory, StyleOptions, Writer


@dataclass
class TranslationContext:
    """Context for maintaining translation state."""

    variables: Dict[str, str] = None  # variable_name -> c_type
    functions: Dict[str, str] = None  # function_name -> return_type
    c_factory: CFactory = None
    current_function: Optional[str] = None
    indent_level: int = 0

    def __post_init__(self):
        if self.variables is None:
            self.variables = {}
        if self.functions is None:
            self.functions = {}
        if self.c_factory is None:
            self.c_factory = CFactory()


class PythonToCTranslator:
    """Translates Python AST nodes to C code using CFile."""

    def __init__(self):
        self.context = TranslationContext()
        self.builtin_functions = {
            "print": self._translate_print,
            "len": self._translate_len,
            "range": self._translate_range,
            "abs": self._translate_abs,
            "min": self._translate_min,
            "max": self._translate_max,
            "int": self._translate_int_cast,
            "float": self._translate_float_cast,
        }
        self.math_functions = {
            "sin": "sin",
            "cos": "cos",
            "tan": "tan",
            "sqrt": "sqrt",
            "log": "log",
            "exp": "exp",
            "pow": "pow",
            "abs": "fabs",
        }

    def translate_module(self, module_node: ast.Module) -> str:
        """Translate a complete Python module to C code."""
        C = self.context.c_factory

        # Create main C file structure
        includes = []
        includes.append(C.include("stdio.h"))
        includes.append(C.include("stdlib.h"))
        includes.append(C.include("math.h"))
        includes.append(C.include("string.h"))

        functions = []
        global_vars = []

        # Process all top-level nodes
        for node in module_node.body:
            if isinstance(node, ast.FunctionDef):
                func = self._translate_function(node)
                if func:
                    functions.append(func)
            elif isinstance(node, ast.Assign):
                var_decl = self._translate_global_assignment(node)
                if var_decl:
                    global_vars.append(var_decl)

        # Build final C code
        elements = []
        elements.extend(includes)
        elements.append(C.blank())

        if global_vars:
            elements.extend(global_vars)
            elements.append(C.blank())

        # Add function declarations
        for func in functions:
            elements.append(C.declaration(func))
            elements.append(C.blank())

        # Create writer and generate code
        writer = Writer(StyleOptions())
        return writer.write(C.sequence(*elements))

    def _translate_function(self, func_node: ast.FunctionDef) -> Optional[Any]:
        """Translate a Python function to C function."""
        C = self.context.c_factory

        # Extract function information
        func_name = func_node.name
        self.context.current_function = func_name

        # Handle parameters
        params = []
        for arg in func_node.args.args:
            param_type = self._infer_parameter_type(arg, func_node)
            param_name = arg.arg
            self.context.variables[param_name] = param_type
            params.append(C.variable(param_type, param_name))

        # Infer return type
        return_type = self._infer_return_type(func_node)
        self.context.functions[func_name] = return_type

        # Translate function body
        body_statements = []
        for stmt in func_node.body:
            c_stmt = self._translate_statement(stmt)
            if c_stmt:
                if isinstance(c_stmt, list):
                    body_statements.extend(c_stmt)
                else:
                    body_statements.append(c_stmt)

        # Create function
        if not body_statements:
            # Add default return if no statements
            if return_type != "void":
                body_statements.append(C.func_return(C.literal("0")))

        func = C.function(return_type, func_name, parameters=params, body=body_statements)

        # Reset function context
        self.context.current_function = None

        return func

    def _translate_statement(self, stmt: ast.stmt) -> Union[Any, List[Any], None]:
        """Translate a Python statement to C statement(s)."""
        C = self.context.c_factory

        if isinstance(stmt, ast.Return):
            return self._translate_return(stmt)
        elif isinstance(stmt, ast.Assign):
            return self._translate_assignment(stmt)
        elif isinstance(stmt, ast.AugAssign):
            return self._translate_aug_assignment(stmt)
        elif isinstance(stmt, ast.If):
            return self._translate_if(stmt)
        elif isinstance(stmt, ast.While):
            return self._translate_while(stmt)
        elif isinstance(stmt, ast.For):
            return self._translate_for(stmt)
        elif isinstance(stmt, ast.Expr):
            return self._translate_expression_statement(stmt)
        else:
            # Unsupported statement - add comment
            return C.comment(f"Unsupported statement: {type(stmt).__name__}")

    def _translate_return(self, return_node: ast.Return) -> Any:
        """Translate return statement."""
        C = self.context.c_factory

        if return_node.value:
            expr = self._translate_expression(return_node.value)
            return C.func_return(expr)
        else:
            return C.func_return(C.literal("0"))  # Default return

    def _translate_assignment(self, assign_node: ast.Assign) -> Union[Any, List[Any]]:
        """Translate assignment statement."""
        C = self.context.c_factory
        statements = []

        # Handle simple assignments (target = value)
        value_expr = self._translate_expression(assign_node.value)

        for target in assign_node.targets:
            if isinstance(target, ast.Name):
                var_name = target.id
                var_type = self._infer_variable_type(assign_node.value)

                if var_name not in self.context.variables:
                    # Variable declaration with initialization
                    self.context.variables[var_name] = var_type
                    statements.append(C.variable(var_type, var_name, value_expr))
                else:
                    # Simple assignment
                    statements.append(C.assignment(C.variable(var_name), value_expr))
            elif isinstance(target, ast.Subscript):
                # Array assignment
                array_expr = self._translate_expression(target.value)
                index_expr = self._translate_expression(target.slice)
                statements.append(C.assign(C.array_access(array_expr, index_expr), value_expr))

        return statements if len(statements) > 1 else statements[0] if statements else None

    def _translate_aug_assignment(self, aug_assign_node: ast.AugAssign) -> Any:
        """Translate augmented assignment (+=, -=, etc.)."""
        C = self.context.c_factory

        target_expr = self._translate_expression(aug_assign_node.target)
        value_expr = self._translate_expression(aug_assign_node.value)

        # Map Python operators to C operators
        op_map = {
            ast.Add: "+",
            ast.Sub: "-",
            ast.Mult: "*",
            ast.Div: "/",
            ast.Mod: "%",
        }

        op = op_map.get(type(aug_assign_node.op), "+")
        combined_expr = C.binary_op(target_expr, op, value_expr)

        return C.assign(target_expr, combined_expr)

    def _translate_if(self, if_node: ast.If) -> Any:
        """Translate if statement."""
        C = self.context.c_factory

        condition = self._translate_expression(if_node.test)

        # Translate body
        then_stmts = []
        for stmt in if_node.body:
            c_stmt = self._translate_statement(stmt)
            if c_stmt:
                if isinstance(c_stmt, list):
                    then_stmts.extend(c_stmt)
                else:
                    then_stmts.append(c_stmt)

        # Translate else clause if present
        else_stmts = []
        if if_node.orelse:
            for stmt in if_node.orelse:
                c_stmt = self._translate_statement(stmt)
                if c_stmt:
                    if isinstance(c_stmt, list):
                        else_stmts.extend(c_stmt)
                    else:
                        else_stmts.append(c_stmt)

        if else_stmts:
            return C.if_else(condition, then_stmts, else_stmts)
        else:
            return C.if_(condition, then_stmts)

    def _translate_while(self, while_node: ast.While) -> Any:
        """Translate while loop."""
        C = self.context.c_factory

        condition = self._translate_expression(while_node.test)

        # Translate body
        body_stmts = []
        for stmt in while_node.body:
            c_stmt = self._translate_statement(stmt)
            if c_stmt:
                if isinstance(c_stmt, list):
                    body_stmts.extend(c_stmt)
                else:
                    body_stmts.append(c_stmt)

        return C.while_(condition, body_stmts)

    def _translate_for(self, for_node: ast.For) -> Any:
        """Translate for loop (convert to while loop)."""
        C = self.context.c_factory
        statements = []

        # Simple for i in range() loops
        if (
            isinstance(for_node.iter, ast.Call)
            and isinstance(for_node.iter.func, ast.Name)
            and for_node.iter.func.id == "range"
        ):
            loop_var = for_node.target.id
            range_args = for_node.iter.args

            if len(range_args) == 1:
                # range(n) -> for(i=0; i<n; i++)
                start = C.literal("0")
                end = self._translate_expression(range_args[0])
                step = C.literal("1")
            elif len(range_args) == 2:
                # range(start, end)
                start = self._translate_expression(range_args[0])
                end = self._translate_expression(range_args[1])
                step = C.literal("1")
            elif len(range_args) == 3:
                # range(start, end, step)
                start = self._translate_expression(range_args[0])
                end = self._translate_expression(range_args[1])
                step = self._translate_expression(range_args[2])
            else:
                # Fallback
                start = C.literal("0")
                end = C.literal("10")
                step = C.literal("1")

            # Declare loop variable
            self.context.variables[loop_var] = "int"

            # Translate body
            body_stmts = []
            for stmt in for_node.body:
                c_stmt = self._translate_statement(stmt)
                if c_stmt:
                    if isinstance(c_stmt, list):
                        body_stmts.extend(c_stmt)
                    else:
                        body_stmts.append(c_stmt)

            # Add increment to body
            body_stmts.append(C.assign(C.variable_ref(loop_var), C.binary_op(C.variable_ref(loop_var), "+", step)))

            # Create for loop
            init = C.assign(C.variable_ref(loop_var), start)
            condition = C.binary_op(C.variable_ref(loop_var), "<", end)

            statements.append(C.variable("int", loop_var, start))
            statements.append(C.while_(condition, body_stmts))

            return statements

        # Fallback for other iterables
        return C.comment("Complex for loop not yet supported")

    def _translate_expression_statement(self, expr_stmt: ast.Expr) -> Any:
        """Translate expression statement."""
        return self._translate_expression(expr_stmt.value)

    def _translate_expression(self, expr: ast.expr) -> Any:
        """Translate a Python expression to C expression."""
        C = self.context.c_factory

        if isinstance(expr, ast.Constant):
            return self._translate_constant(expr)
        elif isinstance(expr, ast.Name):
            return C.variable_ref(expr.id)
        elif isinstance(expr, ast.BinOp):
            return self._translate_binary_op(expr)
        elif isinstance(expr, ast.UnaryOp):
            return self._translate_unary_op(expr)
        elif isinstance(expr, ast.Compare):
            return self._translate_compare(expr)
        elif isinstance(expr, ast.Call):
            return self._translate_call(expr)
        elif isinstance(expr, ast.Subscript):
            return self._translate_subscript(expr)
        elif isinstance(expr, ast.BoolOp):
            return self._translate_bool_op(expr)
        else:
            return C.literal(f"/* Unsupported expr: {type(expr).__name__} */")

    def _translate_constant(self, const: ast.Constant) -> Any:
        """Translate constant values."""
        C = self.context.c_factory

        if isinstance(const.value, bool):
            return C.literal("1" if const.value else "0")
        elif isinstance(const.value, int):
            return C.literal(str(const.value))
        elif isinstance(const.value, float):
            return C.literal(f"{const.value:.6f}")
        elif isinstance(const.value, str):
            return C.str_literal(const.value)
        else:
            return C.literal(str(const.value))

    def _translate_binary_op(self, binop: ast.BinOp) -> Any:
        """Translate binary operations."""
        C = self.context.c_factory

        left = self._translate_expression(binop.left)
        right = self._translate_expression(binop.right)

        op_map = {
            ast.Add: "+",
            ast.Sub: "-",
            ast.Mult: "*",
            ast.Div: "/",
            ast.Mod: "%",
            ast.Pow: "**",  # Will need special handling
            ast.FloorDiv: "/",  # Approximation
        }

        if isinstance(binop.op, ast.Pow):
            # Use pow function for exponentiation
            return C.func_call("pow", [left, right])

        op = op_map.get(type(binop.op), "+")
        return C.binary_op(left, op, right)

    def _translate_unary_op(self, unaryop: ast.UnaryOp) -> Any:
        """Translate unary operations."""
        C = self.context.c_factory

        operand = self._translate_expression(unaryop.operand)

        if isinstance(unaryop.op, ast.UAdd):
            return operand
        elif isinstance(unaryop.op, ast.USub):
            return C.unary_op("-", operand)
        elif isinstance(unaryop.op, ast.Not):
            return C.unary_op("!", operand)
        else:
            return operand

    def _translate_compare(self, compare: ast.Compare) -> Any:
        """Translate comparison operations."""
        C = self.context.c_factory

        left = self._translate_expression(compare.left)

        # Handle multiple comparisons (a < b < c)
        if len(compare.ops) == 1 and len(compare.comparators) == 1:
            op = compare.ops[0]
            right = self._translate_expression(compare.comparators[0])

            op_map = {
                ast.Eq: "==",
                ast.NotEq: "!=",
                ast.Lt: "<",
                ast.LtE: "<=",
                ast.Gt: ">",
                ast.GtE: ">=",
            }

            c_op = op_map.get(type(op), "==")
            return C.binary_op(left, c_op, right)

        # For complex comparisons, create compound conditions
        conditions = []
        current_left = left

        for op, comparator in zip(compare.ops, compare.comparators):
            right = self._translate_expression(comparator)

            op_map = {
                ast.Eq: "==",
                ast.NotEq: "!=",
                ast.Lt: "<",
                ast.LtE: "<=",
                ast.Gt: ">",
                ast.GtE: ">=",
            }

            c_op = op_map.get(type(op), "==")
            conditions.append(C.binary_op(current_left, c_op, right))
            current_left = right

        # Combine with && if multiple conditions
        result = conditions[0]
        for condition in conditions[1:]:
            result = C.binary_op(result, "&&", condition)

        return result

    def _translate_bool_op(self, boolop: ast.BoolOp) -> Any:
        """Translate boolean operations (and, or)."""
        C = self.context.c_factory

        values = [self._translate_expression(val) for val in boolop.values]

        if isinstance(boolop.op, ast.And):
            op = "&&"
        elif isinstance(boolop.op, ast.Or):
            op = "||"
        else:
            op = "&&"

        result = values[0]
        for value in values[1:]:
            result = C.binary_op(result, op, value)

        return result

    def _translate_call(self, call: ast.Call) -> Any:
        """Translate function calls."""
        C = self.context.c_factory

        if isinstance(call.func, ast.Name):
            func_name = call.func.id

            # Handle built-in functions
            if func_name in self.builtin_functions:
                return self.builtin_functions[func_name](call)

            # Handle math functions
            if func_name in self.math_functions:
                c_func_name = self.math_functions[func_name]
                args = [self._translate_expression(arg) for arg in call.args]
                return C.func_call(c_func_name, args)

            # Regular function call
            args = [self._translate_expression(arg) for arg in call.args]
            return C.func_call(func_name, args)

        elif isinstance(call.func, ast.Attribute):
            # Method calls (obj.method())
            obj = self._translate_expression(call.func.value)
            method = call.func.attr
            args = [self._translate_expression(arg) for arg in call.args]

            # For now, treat as regular function call
            return C.func_call(method, [obj] + args)

        return C.literal("/* Unsupported call */")

    def _translate_subscript(self, subscript: ast.Subscript) -> Any:
        """Translate array/list subscript access."""
        C = self.context.c_factory

        array = self._translate_expression(subscript.value)
        index = self._translate_expression(subscript.slice)

        return C.array_access(array, index)

    # Built-in function translators
    def _translate_print(self, call: ast.Call) -> Any:
        """Translate print() function to printf()."""
        C = self.context.c_factory

        if not call.args:
            return C.func_call("printf", [C.str_literal("\\n")])

        # Simple print implementation
        args = []
        format_parts = []

        for arg in call.args:
            arg_expr = self._translate_expression(arg)
            args.append(arg_expr)

            # Infer format specifier (simplified)
            if isinstance(arg, ast.Constant):
                if isinstance(arg.value, int):
                    format_parts.append("%d")
                elif isinstance(arg.value, float):
                    format_parts.append("%.6f")
                elif isinstance(arg.value, str):
                    format_parts.append("%s")
                else:
                    format_parts.append("%s")
            else:
                format_parts.append("%d")  # Default to int

        format_str = " ".join(format_parts) + "\\n"
        printf_args = [C.str_literal(format_str)] + args

        return C.func_call("printf", printf_args)

    def _translate_len(self, call: ast.Call) -> Any:
        """Translate len() function."""
        C = self.context.c_factory

        if call.args:
            # For arrays, we'll need to track sizes separately
            # For now, return a placeholder
            return C.literal("/* len() not fully implemented */")

        return C.literal("0")

    def _translate_range(self, call: ast.Call) -> Any:
        """Range is handled in for loop translation."""
        C = self.context.c_factory
        return C.literal("/* range() handled in for loops */")

    def _translate_abs(self, call: ast.Call) -> Any:
        """Translate abs() function."""
        C = self.context.c_factory

        if call.args:
            arg = self._translate_expression(call.args[0])
            return C.func_call("abs", [arg])

        return C.literal("0")

    def _translate_min(self, call: ast.Call) -> Any:
        """Translate min() function."""
        C = self.context.c_factory

        if len(call.args) >= 2:
            # Use ternary operator for two arguments
            a = self._translate_expression(call.args[0])
            b = self._translate_expression(call.args[1])
            condition = C.binary_op(a, "<", b)
            return C.ternary(condition, a, b)

        return C.literal("0")

    def _translate_max(self, call: ast.Call) -> Any:
        """Translate max() function."""
        C = self.context.c_factory

        if len(call.args) >= 2:
            # Use ternary operator for two arguments
            a = self._translate_expression(call.args[0])
            b = self._translate_expression(call.args[1])
            condition = C.binary_op(a, ">", b)
            return C.ternary(condition, a, b)

        return C.literal("0")

    def _translate_int_cast(self, call: ast.Call) -> Any:
        """Translate int() cast."""
        C = self.context.c_factory

        if call.args:
            arg = self._translate_expression(call.args[0])
            return C.cast("int", arg)

        return C.literal("0")

    def _translate_float_cast(self, call: ast.Call) -> Any:
        """Translate float() cast."""
        C = self.context.c_factory

        if call.args:
            arg = self._translate_expression(call.args[0])
            return C.cast("double", arg)

        return C.literal("0.0")

    def _translate_global_assignment(self, assign_node: ast.Assign) -> Optional[Any]:
        """Translate global variable assignment."""
        C = self.context.c_factory

        if len(assign_node.targets) == 1 and isinstance(assign_node.targets[0], ast.Name):
            var_name = assign_node.targets[0].id
            var_type = self._infer_variable_type(assign_node.value)
            value = self._translate_expression(assign_node.value)

            self.context.variables[var_name] = var_type
            return C.variable(var_type, var_name, value)

        return None

    # Type inference helpers
    def _infer_parameter_type(self, arg: ast.arg, func_node: ast.FunctionDef) -> str:
        """Infer parameter type from annotations or usage."""
        if arg.annotation:
            return self._annotation_to_c_type(arg.annotation)

        # Fallback to int for now
        return "int"

    def _infer_return_type(self, func_node: ast.FunctionDef) -> str:
        """Infer return type from annotations or return statements."""
        if func_node.returns:
            return self._annotation_to_c_type(func_node.returns)

        # Look for return statements
        for stmt in ast.walk(func_node):
            if isinstance(stmt, ast.Return) and stmt.value:
                return self._infer_expression_type(stmt.value)

        return "void"

    def _infer_variable_type(self, expr: ast.expr) -> str:
        """Infer variable type from expression."""
        return self._infer_expression_type(expr)

    def _infer_expression_type(self, expr: ast.expr) -> str:
        """Infer type of expression."""
        if isinstance(expr, ast.Constant):
            if isinstance(expr.value, bool):
                return "int"
            elif isinstance(expr.value, int):
                return "int"
            elif isinstance(expr.value, float):
                return "double"
            elif isinstance(expr.value, str):
                return "char*"
        elif isinstance(expr, ast.BinOp):
            left_type = self._infer_expression_type(expr.left)
            right_type = self._infer_expression_type(expr.right)

            # Type promotion rules
            if left_type == "double" or right_type == "double":
                return "double"
            else:
                return "int"
        elif isinstance(expr, ast.Name):
            return self.context.variables.get(expr.id, "int")
        elif isinstance(expr, ast.Call):
            if isinstance(expr.func, ast.Name):
                func_name = expr.func.id
                if func_name in self.context.functions:
                    return self.context.functions[func_name]
                elif func_name in self.math_functions:
                    return "double"

        return "int"  # Default fallback

    def _annotation_to_c_type(self, annotation: ast.expr) -> str:
        """Convert Python type annotation to C type."""
        if isinstance(annotation, ast.Name):
            type_map = {
                "int": "int",
                "float": "double",
                "str": "char*",
                "bool": "int",
            }
            return type_map.get(annotation.id, "int")
        elif isinstance(annotation, ast.Constant):
            if isinstance(annotation.value, str):
                return annotation.value  # Direct C type

        return "int"  # Default fallback
